"""Read QIIME 2 action evidence without extracting or executing archive contents.

The original parser's public function names and action-file mapping are retained.
TypedDicts narrow its existing dictionary interface. Runtime validation occurs at
the YAML boundary, and the report layer uses immutable dataclasses.
"""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import NotRequired, TypedDict
from uuid import UUID
from zipfile import BadZipFile, ZipFile

import yaml

type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_PROVENANCE_BYTES = 64 * 1024 * 1024


class ProvenanceError(ValueError):
    """An archive lacks readable, structurally valid provenance evidence."""


class ActionFiles(TypedDict):
    """ZIP members, preserving the original parser's two-key API."""

    action: str
    previous_action: list[str]


class ParsedRecord(TypedDict):
    """Validated record compatible with the original parser's output."""

    uuid: str
    artifact_uuid: str
    plugin: str
    action: str
    inputs: list[str]
    is_main: bool
    parameters: NotRequired[dict[str, JSONValue]]


class QIIME2Loader(yaml.SafeLoader):
    """Safely preserve values of QIIME 2 local tags such as !ref and !cite."""

    @classmethod
    def construct_qiime2_tag(
        cls, loader: yaml.SafeLoader, tag_suffix: str, node: yaml.nodes.Node
    ) -> object:
        """Decode a local tag without importing or constructing Python objects."""
        if isinstance(node, yaml.nodes.ScalarNode):
            return loader.construct_scalar(node)
        if isinstance(node, yaml.nodes.SequenceNode):
            return loader.construct_sequence(node, deep=True)
        if isinstance(node, yaml.nodes.MappingNode):
            return loader.construct_mapping(node, deep=True)
        raise ProvenanceError(f"Unsupported YAML tag: !{tag_suffix}")

    def construct_mapping(
        self, node: yaml.nodes.MappingNode, deep: bool = False
    ) -> dict[object, object]:
        """Reject duplicate YAML keys instead of silently discarding evidence."""
        self.flatten_mapping(node)
        result: dict[object, object] = {}
        for key_node, value_node in node.value:
            key: object = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ProvenanceError(f"Duplicate YAML key: {key!r}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


QIIME2Loader.add_multi_constructor("!", QIIME2Loader.construct_qiime2_tag)


def json_value(value: object, depth: int = 0) -> JSONValue:
    """Validate YAML values and normalize dates/sets for lossless readable export.

    A depth limit also rejects recursive YAML aliases. Exotic Python types never
    cross into the GUI model. YAML sets become deterministically ordered lists.
    """
    if depth > 60:
        raise ProvenanceError("YAML nesting exceeds 60 levels or contains a recursive alias.")
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        values = sorted(value, key=str) if isinstance(value, set) else value
        return [json_value(item, depth + 1) for item in values]
    if isinstance(value, dict):
        result: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProvenanceError("YAML mapping keys must be strings.")
            result[key] = json_value(item, depth + 1)
        return result
    raise ProvenanceError(f"Unsupported YAML value: {type(value).__name__}")


def mapping(value: JSONValue, label: str) -> dict[str, JSONValue]:
    """Require a mapping at a documented provenance boundary."""
    if not isinstance(value, dict):
        raise ProvenanceError(f"{label} must be a mapping.")
    return value


def string(value: JSONValue, label: str) -> str:
    """Require a nonempty string instead of coercing malformed fields."""
    if not isinstance(value, str) or not value:
        raise ProvenanceError(f"{label} must be a nonempty string.")
    return value


def read_member(archive: ZipFile, member: str) -> str:
    """Read one bounded UTF-8 member; never extract any data payload to disk."""
    info = archive.getinfo(member)
    if info.file_size > MAX_MEMBER_BYTES:
        raise ProvenanceError(f"Provenance member exceeds 8 MiB: {member}")
    with archive.open(info) as stream:
        data = stream.read(MAX_MEMBER_BYTES + 1)
    if len(data) > MAX_MEMBER_BYTES:
        raise ProvenanceError(f"Provenance member exceeds 8 MiB: {member}")
    return data.decode("utf-8")


def load_zipfile(file_path: Path) -> ZipFile | BadZipFile | OSError:
    """Open an archive read-only, returning an opening error to the caller."""
    try:
        return ZipFile(file_path, "r")
    except (BadZipFile, OSError) as error:
        return error


def close_zipfile(zipfile: ZipFile) -> None:
    """Close an archive returned by :func:`load_zipfile`."""
    zipfile.close()


def get_action_files(zipfile: ZipFile) -> ActionFiles | ValueError:
    """Find exactly one main action and same-root upstream action members."""
    try:
        if zipfile.fp is None:
            raise ProvenanceError("The archive is already closed.")
        names = zipfile.namelist()
        if len(names) != len(set(names)):
            raise ProvenanceError("Duplicate ZIP member names were found.")
        main = [n for n in names if re.fullmatch(r"[^/]+/provenance/action/action\.yaml", n)]
        if len(main) != 1:
            raise ProvenanceError(
                "Expected one provenance/action/action.yaml; found " + str(len(main))
            )
        root = main[0].split("/")[0]
        UUID(root)
        previous = sorted(
            n
            for n in names
            if re.fullmatch(r"[^/]+/provenance/artifacts/[^/]+/action/action\.yaml", n)
        )
        if any(not n.startswith(root + "/") for n in previous):
            raise ProvenanceError("Provenance members belong to multiple archive roots.")
        if sum(zipfile.getinfo(n).file_size for n in [main[0], *previous]) > MAX_PROVENANCE_BYTES:
            raise ProvenanceError("Action YAML total exceeds 64 MiB.")
        return {"action": main[0], "previous_action": previous}
    except ValueError as error:
        return error


@dataclass(frozen=True)
class ActionRecord:
    """One artifact's producing execution and source evidence."""

    uuid: str
    artifact_uuid: str
    plugin: str
    action: str
    inputs: tuple[str, ...]
    is_main: bool
    parameters: dict[str, JSONValue]
    member: str
    raw_yaml: str
    runtime: dict[str, JSONValue]
    framework_version: str

    @property
    def command(self) -> str:
        """Return the human-readable QIIME CLI method name (not a runnable command)."""
        return f"{self.plugin} {self.action.replace('_', '-')}"

    def as_dict(self, verbose: bool = True) -> ParsedRecord:
        """Return the original parser's record structure for compatibility/export."""
        result: ParsedRecord = {
            "uuid": self.uuid,
            "artifact_uuid": self.artifact_uuid,
            "plugin": self.plugin,
            "action": self.action,
            "inputs": list(self.inputs),
            "is_main": self.is_main,
        }
        if verbose:
            result["parameters"] = self.parameters
        return result


def parse_action(archive: ZipFile, member: str, is_main: bool) -> ActionRecord:
    """Validate and decode one action YAML, including nested collection inputs."""
    raw = read_member(archive, member)
    document = mapping(json_value(yaml.load(raw, Loader=QIIME2Loader)), member)
    execution = mapping(document.get("execution"), "execution")
    action = mapping(document.get("action"), "action")
    execution_uuid = str(UUID(string(execution.get("uuid"), "execution.uuid")))
    artifact_uuid = str(UUID(member.split("/")[0 if is_main else 3]))
    if action.get("type") == "import":
        plugin, name = "qiime tools", "import"
    else:
        plugin_name = string(action.get("plugin"), "action.plugin").rsplit(":", 1)[-1]
        plugin = "qiime " + plugin_name.replace("_", "-")
        name = string(action.get("action"), "action.action")

    inputs: list[str] = []
    pending: list[JSONValue] = [action.get("inputs")]
    # QIIME collections can nest lists and named mappings at arbitrary levels.
    while pending:
        item = pending.pop()
        if item is None:
            continue
        if isinstance(item, str):
            uid = str(UUID(item))
            if uid not in inputs:
                inputs.append(uid)
        elif isinstance(item, dict):
            pending.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            pending.extend(reversed(item))
        else:
            raise ProvenanceError("An input reference must contain artifact UUID strings.")

    parameters: dict[str, JSONValue] = {}
    parameter_list = action.get("parameters")
    if parameter_list is not None:
        if not isinstance(parameter_list, list):
            raise ProvenanceError("action.parameters must be a list of mappings.")
        for item in parameter_list:
            entry = mapping(item, "parameter")
            if parameters.keys() & entry.keys():
                raise ProvenanceError("Duplicate parameter names were found.")
            parameters.update(entry)
    environment = mapping(document.get("environment", {}), "environment")
    framework = mapping(environment.get("framework", {}), "environment.framework")
    version = string(framework.get("version", "unknown"), "framework.version")
    return ActionRecord(
        execution_uuid,
        artifact_uuid,
        plugin,
        name,
        tuple(inputs),
        is_main,
        parameters,
        member,
        raw,
        mapping(execution.get("runtime", {}), "runtime"),
        version,
    )


def parse_yaml(
    action_files: ActionFiles, zipfile: ZipFile, verbose: bool = False
) -> list[ParsedRecord] | ValueError | KeyError | TypeError | OSError | BadZipFile | yaml.YAMLError:
    """Parse main/upstream members using the original exception-as-value API."""
    try:
        members = [(action_files["action"], True)]
        members.extend((member, False) for member in action_files["previous_action"])
        return [parse_action(zipfile, member, main).as_dict(verbose) for member, main in members]
    except (ValueError, KeyError, TypeError, OSError, BadZipFile, yaml.YAMLError) as error:
        return error


@dataclass(frozen=True)
class Report:
    """Reachable artifact graph in dependency order, plus explicit evidence gaps."""

    path: Path
    artifact_uuid: str
    semantic_type: str
    data_format: str
    records: tuple[ActionRecord, ...]
    missing_inputs: tuple[str, ...]
    archive_version: str

    @property
    def executions(self) -> tuple[ActionRecord, ...]:
        """Deduplicate multi-output executions, preserving the main artifact marker."""
        unique: dict[str, ActionRecord] = {}
        for record in self.records:
            if record.uuid not in unique or record.is_main:
                unique[record.uuid] = record
        return tuple(unique.values())

    def to_json(self, verbose: bool = True) -> str:
        """Export a versioned document with artifact edges and source-member paths."""
        return json.dumps(
            {
                "schema_version": 1,
                "source_path": str(self.path),
                "artifact_uuid": self.artifact_uuid,
                "semantic_type": self.semantic_type,
                "format": self.data_format,
                "archive_version": self.archive_version,
                "missing_inputs": self.missing_inputs,
                "records": [
                    dict(
                        r.as_dict(verbose),
                        source_member=r.member,
                        runtime=r.runtime,
                        framework_version=r.framework_version,
                    )
                    for r in self.records
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


def order_records(records: list[ActionRecord]) -> tuple[tuple[ActionRecord, ...], tuple[str, ...]]:
    """Topologically order reachable artifacts; reject cycles and expose missing inputs."""
    mains = [r for r in records if r.is_main]
    if len(mains) != 1:
        raise ProvenanceError("Exactly one main artifact is required.")
    indexed = {r.artifact_uuid: r for r in records}
    if len(indexed) != len(records):
        raise ProvenanceError("Duplicate artifact UUIDs were found.")
    reachable: set[str] = set()
    pending = [mains[0].artifact_uuid]
    while pending:
        uid = pending.pop()
        if uid not in reachable:
            reachable.add(uid)
            if uid in indexed:
                pending.extend(indexed[uid].inputs)
    selected = [r for r in records if r.artifact_uuid in reachable]
    degrees = {r.artifact_uuid: len(set(r.inputs) & indexed.keys()) for r in selected}
    children: dict[str, list[str]] = {r.artifact_uuid: [] for r in selected}
    for record in selected:
        for uid in set(record.inputs):
            if uid in children:
                children[uid].append(record.artifact_uuid)
    ready = deque(sorted(uid for uid, degree in degrees.items() if degree == 0))
    ordered: list[ActionRecord] = []
    while ready:
        uid = ready.popleft()
        ordered.append(indexed[uid])
        for child in sorted(children[uid]):
            degrees[child] -= 1
            if degrees[child] == 0:
                ready.append(child)
    if len(ordered) != len(selected):
        raise ProvenanceError("The provenance graph contains a cycle.")
    return tuple(ordered), tuple(sorted(reachable - indexed.keys()))


def parse_archive(path: Path) -> Report:
    """Build a report from a QZA/QZV, reading only metadata and action YAML.

    Raises:
        ProvenanceError: ZIP/YAML/UUID/graph validation fails.
        OSError: The file is unavailable or unreadable.

    This does not verify payload checksums or execute QIIME commands. Missing
    ancestor evidence remains an explicit warning in the report.
    """
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ProvenanceError(f"Not a file: {resolved}")
    try:
        with ZipFile(resolved, "r") as archive:
            members = get_action_files(archive)
            if isinstance(members, ValueError):
                raise members
            root = members["action"].split("/")[0]
            metadata = mapping(
                json_value(
                    yaml.load(read_member(archive, root + "/metadata.yaml"), Loader=QIIME2Loader)
                ),
                "metadata.yaml",
            )
            if str(UUID(string(metadata.get("uuid"), "metadata.uuid"))) != root:
                raise ProvenanceError("metadata.uuid does not match the archive root.")
            version = read_member(archive, root + "/VERSION")
            if not version.startswith("QIIME 2\n"):
                raise ProvenanceError("Invalid QIIME 2 VERSION header.")
            records = [parse_action(archive, members["action"], True)]
            records.extend(
                parse_action(archive, member, False) for member in members["previous_action"]
            )
            ordered, missing = order_records(records)
            return Report(
                resolved,
                root,
                string(metadata.get("type"), "metadata.type"),
                str(metadata.get("format") or "—"),
                ordered,
                missing,
                version.strip(),
            )
    except (BadZipFile, ValueError, KeyError, TypeError, yaml.YAMLError, RecursionError) as error:
        raise ProvenanceError(f"{resolved.name}: {error}") from error
