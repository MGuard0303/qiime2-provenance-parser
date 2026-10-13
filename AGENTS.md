# Project Maintenance Instructions

## English

- The maintenance root is `/Users/lixuanmu/projects/qiime2-provenance-parser/`.
  Since 2026-10-09, all program updates, builds, deliveries and new validation
  records take place inside this project.
- macOS source is in `macOS/source/`; current Windows source is in
  `Windows/source/`. Keep each platform's source, runtime, builds and deliveries
  separate.
- `Windows/archive/v1.0.0/` retains the original Windows delivery. Routine program
  work uses current Windows source. Previous Codex outputs and Storage3 source
  directories are historical references. The explicit project-wide Markdown
  policy also applies to documentation in the archived and packaged copies.
- Rebuild the corresponding delivery after source changes. Preserve third-party
  licenses and verifiable records. Shared parsing or GUI behavior changes need
  consideration on both platforms; use each platform's strict type-check setup.
- In the complete local checkout, refresh file descriptions with
  `python tools/update_file_report.py` when that local tool exists. It is excluded
  from the minimal GitHub source repository. Source-only clones use the retained
  source tests and build checks. The local report includes all files and symlinks
  without recursively following symlink directories.
- The owner manually adds and manages Git. Do not initialize a repository, create
  remotes or commit automatically.
- Avoid the prohibited Chinese response constructions listed in the Chinese
  section below.
- Tables use 11-point text, bold column headings, and no background fills or
  custom colors.
- Every project file uses an English filename. Markdown documents use complete
  bilingual content, with the English section first and the Chinese section
  second. Update all references, generators and ignore rules when renaming files.
  Apply this to current source, bundled copies and the local historical archive.

---

## 中文

- 项目维护根目录为 `/Users/lixuanmu/projects/qiime2-provenance-parser/`。
  从 2026-10-09 起，所有程序更新、构建、交付和新增验证记录都在本项目内进行。
- macOS 源码位于 `macOS/source/`，Windows 当前源码位于 `Windows/source/`。
  两个平台的源码、运行库、构建和交付分别存放。
- `Windows/archive/v1.0.0/` 是本次指定旧 Windows 目录的完整历史副本，
  日常更新使用 Windows 当前源码。归档文档也适用全项目的双语说明规则，
  程序保留历史版本。原 Codex outputs 和 Storage3 源目录是历史来源。
- 更新源码后重新构建对应平台交付，保留第三方许可证和可核查的验证记录。
  共享解析或 GUI 行为的修改需要同步考虑两平台，严格类型检查使用各自配置。
- 完整本地项目中，文件清单工具存在时可用 `python tools/update_file_report.py` 刷新报告。
  此工具不纳入 GitHub 最小源码仓库；纯源码克隆使用保留的测试与构建检查。
  本地报告覆盖全部文件和符号链接，扫描时不递归跟随符号链接。
- Git 由用户手动添加和管理；不要自行初始化仓库、创建远程或提交。
- 回答时避免使用“不是，而是”和“我反而”。
- 如创建表格，不设置底纹或颜色；列标题只加粗，字号使用 11。
- 项目所有文件采用英文文件名。Markdown 内容使用完整中英双语，英文段落在前，
  中文段落在后。修改文件名时同步修正引用、生成工具和忽略规则，覆盖当前源码、
  打包副本和本地旧版归档。

