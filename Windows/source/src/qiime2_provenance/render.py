"""Escape evidence before rendering and share report formatting across GUI/CLI."""

import json
from html import escape

from .parser import ActionRecord, Report


def parameter_table(record: ActionRecord) -> str:
    """Render recorded parameter names and JSON values without interpreting HTML.

    JSON preserves booleans, nulls, strings and collections. An empty mapping
    only means this evidence record contains no parameters, not that QIIME used
    no defaults. Tables use 11 pt text, bold headers and no fill colors.
    """
    if not record.parameters:
        return "<p>此步骤的证据未记录 parameters。</p>"
    rows = "".join(
        f"<tr><td>{escape(key)}</td><td>"
        f"{escape(json.dumps(value, ensure_ascii=False))}</td></tr>"
        for key, value in record.parameters.items()
    )
    return (
        '<table style="font-size:11pt" cellspacing="8">'
        '<tr><th align="left">参数名</th><th align="left">值</th></tr>'
        + rows
        + "</table>"
    )


def render_parameters(report: Report) -> str:
    """Show parameters once per execution, in the evidence chain's dependency order.

    Include the execution UUID and original ZIP member for traceability. Display
    recorded names verbatim rather than guessing CLI flags or missing defaults.
    """
    parts = [
        "<h3>每一步的 QIIME 参数</h3>",
        "<p>按证据链顺序排列；同一次执行的多个输出合并显示。"
        "参数名与值来自 action.yaml，未记录的默认值不作推断。</p>",
    ]
    for index, record in enumerate(report.executions, 1):
        parts.extend(
            [
                f"<h3>{index:02d} · {escape(record.command)}</h3>",
                parameter_table(record),
                f"<p><b>Execution UUID</b><br>{escape(record.uuid)}<br>"
                f"<b>ZIP 内证据位置</b><br>{escape(record.member)}</p>",
            ]
        )
    return "".join(parts)


def render_text(report: Report, verbose: bool = False) -> str:
    """Format evidence first, followed by per-artifact details and optional parameters."""
    lines = [
        "QIIME 2 Provenance Report",
        "=" * 25,
        f"Artifact : {report.path}",
        f"Type     : {report.semantic_type}",
        f"UUID     : {report.artifact_uuid}",
        f"Actions  : {len(report.executions)}",
        "",
        "Evidence chain",
        "--------------",
        "Dependency order; adjacent rows may belong to different branches.",
    ]
    for index, record in enumerate(report.executions, 1):
        lines.append(f"{index:02d}. {record.command}" + (" [MAIN]" if record.is_main else ""))
    if report.missing_inputs:
        lines.extend(["", "WARNING: missing upstream provenance:", *report.missing_inputs])
    lines.extend(["", "Parsed provenance", "-----------------"])
    for index, record in enumerate(report.records, 1):
        lines.extend(
            [
                "",
                f"[{index}] {record.command}" + (" [MAIN]" if record.is_main else ""),
                f"  Execution UUID : {record.uuid}",
                f"  Artifact UUID  : {record.artifact_uuid}",
                f"  Inputs         : {', '.join(record.inputs) or 'none'}",
                f"  QIIME version  : {record.framework_version}",
                f"  Source member  : {record.member}",
            ]
        )
        if verbose:
            lines.append("  Parameters     :")
            lines.extend(
                f"    {key}: {json.dumps(value, ensure_ascii=False)}"
                for key, value in record.parameters.items()
            )
            if not record.parameters:
                lines.append("    not recorded in this evidence record")
    lines.extend(["", "Scope: provenance metadata only; data payload checksums were not verified."])
    return "\n".join(lines)


def render_action(record: ActionRecord, report: Report, verbose: bool) -> str:
    """Render one execution with all output artifacts and clickable upstream records."""
    outputs = [r for r in report.records if r.uuid == record.uuid]
    parts = [
        f"<h3>{escape(record.command)}</h3>",
        f"<p><b>Execution UUID</b><br>{escape(record.uuid)}</p>",
    ]
    parts.append(
        "<p><b>输出 Artifact</b><br>"
        + "<br>".join(
            escape(r.artifact_uuid) + (" · 当前文件" if r.is_main else "") for r in outputs
        )
        + "</p>"
    )
    known = {r.artifact_uuid for r in report.records}
    inputs = tuple(dict.fromkeys(uid for r in outputs for uid in r.inputs))
    parts.append(
        "<p><b>上游输入</b><br>"
        + (
            "<br>".join(
                f'<a href="artifact:{uid}">{uid}</a>' if uid in known else f"{uid} · 缺少记录"
                for uid in inputs
            )
            or "无（导入起点）"
        )
        + "</p>"
    )
    parts.append(f"<p><b>QIIME 2</b> · {escape(record.framework_version)}</p>")
    if record.runtime:
        parts.append(
            "<p><b>执行时间</b><br>"
            + "<br>".join(
                f"{escape(key)}: {escape(str(value))}" for key, value in record.runtime.items()
            )
            + "</p>"
        )
    if verbose:
        parts.append("<h3>QIIME 参数</h3>" + parameter_table(record))
    else:
        parts.append("<p>勾选左侧「Verbose：显示 QIIME 参数」查看此步骤的参数值。</p>")
    parts.append(f"<p><b>ZIP 内证据位置</b><br>{escape(record.member)}</p>")
    return "".join(parts)


def render_html(report: Report, verbose: bool) -> str:
    """Create an offline, script-free HTML report with escaped source content."""
    return (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        "<title>QIIME 2 Provenance Report</title><style>"
        "body{max-width:1100px;margin:48px auto;padding:0 24px;font:15px system-ui;"
        "line-height:1.7;color:#182831}pre{white-space:pre-wrap;overflow-wrap:anywhere;"
        "font:13px ui-monospace,monospace}</style><body>"
        "<h1>QIIME 2 Provenance Report</h1><pre>"
        + escape(render_text(report, verbose))
        + "</pre></body></html>"
    )
