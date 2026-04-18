# Evergreen Notes

本仓库保存从 Andy Matuschak 笔记站抓取并转换后的 Obsidian 笔记。

入口：

- [Evergreen notes](./evergreen_notes/Evergreen%20notes.md)

## 目录

- `evergreen_notes/`
  转换后的 Markdown 笔记主目录。
- `evergreen_notes/off-topic/`
  与常青笔记主线关系较弱的笔记。
- `scripts/fetch_evergreen_notes.py`
  抓取并转换为 Obsidian 双链的脚本。
- `.cache/fetch_evergreen_notes/`
  抓取过程中的原始缓存和状态文件，不提交到 Git。

## 用法

```bash
python3 ./scripts/fetch_evergreen_notes.py fetch \
  https://notes.andymatuschak.org/Evergreen_notes \
  --depth 1 \
  -o evergreen_notes
```

合并为单文件：

```bash
python3 ./scripts/fetch_evergreen_notes.py compile \
  -o evergreen_notes \
  --compiled-output auto
```

参数：

- `url`
  `fetch` 子命令的根页面，视为 `depth 0`。
- `--depth`
  `fetch` 子命令的抓取层级，支持数字或 `all`。
- `-o`, `--output-dir`
  输出目录。`fetch` 会写入分散笔记，`compile` 会从这里读取已有笔记。
- `--keep-raw`
  `fetch` 子命令参数，保留 `.cache/` 下的原始抓取结果。
- `--compiled-output`
  `compile` 子命令参数。默认值 `auto` 会生成 `evergreen_notes_compiled.md`；也可传入自定义路径。

## 说明

- 站内链接会被转换为 Obsidian `[[双链]]`。
- `fetch` 只负责拉取和写入分散笔记，不会默认生成合并文件。
- `compile` 只负责把已有笔记目录合并成单文件 Markdown，便于导入或分享。
- 为兼容旧调用，直接把 URL 作为第一个参数传给脚本时，会按 `fetch` 处理。
