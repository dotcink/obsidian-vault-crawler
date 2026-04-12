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
python3 ./scripts/fetch_evergreen_notes.py \
  https://notes.andymatuschak.org/Evergreen_notes \
  --depth 1 \
  -o evergreen_notes
```

参数：

- `url`
  根页面，视为 `depth 0`。
- `--depth`
  抓取层级，支持数字或 `all`。
- `-o`, `--output-dir`
  输出目录。
- `--keep-raw`
  保留 `.cache/` 下的原始抓取结果。

## 说明

- 站内链接会被转换为 Obsidian `[[双链]]`。
- 脚本每次都会从传入根页面重新做一轮 BFS，但会跳过已成功下载并转换的页面。
