#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
READER = Path(
    "/Users/dotcink/.agents/skills/baoyu-url-to-markdown/scripts/vendor/baoyu-fetch/src/cli.ts"
)
ROOT_URL = "https://notes.andymatuschak.org/Evergreen_notes"
OUTPUT_ROOT = REPO_ROOT / "url-to-markdown" / "notes.andymatuschak.org"
RAW_ROOT = OUTPUT_ROOT / ".raw"
STATE_PATH = OUTPUT_ROOT / "crawl-state.json"

SITE_LINK_RE = re.compile(r"\[([^\]]+)\]\((https://notes\.andymatuschak\.org/[^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    slug = path.split("/")[-1]
    return slug or "index"


def safe_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', " ", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(".")
    return cleaned or "Untitled"


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    match = FRONTMATTER_RE.match(text)
    if match:
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')
        body = text[match.end() :].lstrip()
    else:
        body = text
    return metadata, body


def parse_frontmatter_file(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    match = FRONTMATTER_RE.match(text)
    if not match:
        return metadata
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def fetch_url(url: str) -> Path:
    slug = slug_from_url(url)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_ROOT / f"{slug}.md"
    cmd = [
        "bun",
        str(READER),
        url,
        "--output",
        str(raw_path),
        "--download-media",
    ]
    result = subprocess.run(
        cmd,
        check=False,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        summary = stderr or stdout or f"exit_code={result.returncode}"
        summary = " ".join(summary.split())
        raise RuntimeError(summary[:500])
    return raw_path


def extract_site_links(body: str) -> list[tuple[str, str]]:
    seen: set[str] = set()
    results: list[tuple[str, str]] = []
    for text, url in SITE_LINK_RE.findall(body):
        if url in seen:
            continue
        seen.add(url)
        results.append((text, url))
    return results


def rewrite_links(body: str, url_to_title: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        text, url = match.groups()
        title = url_to_title.get(url) or text
        return f"[[{title}]]"

    return SITE_LINK_RE.sub(repl, body)


def write_obsidian_note(title: str, source_url: str, body: str) -> Path:
    final_name = safe_name(title) + ".md"
    final_path = OUTPUT_ROOT / final_name
    frontmatter = "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'source: "{source_url}"',
            f'captured: "{utc_now()}"',
            "---",
            "",
        ]
    )
    final_path.write_text(frontmatter + body.rstrip() + "\n", encoding="utf-8")
    return final_path


def log(message: str) -> None:
    print(message, flush=True)


def make_initial_state(root_url: str, depth: int | None) -> dict:
    return {
        "root_url": root_url,
        "depth": depth,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "pending": [{"url": root_url, "depth": 0}],
        "seen_urls": [],
        "fetched_urls": [],
        "out_links": {},
        "url_to_title": {},
        "written_files": {},
        "errors": {},
    }


def load_state(resume: bool, root_url: str, depth: int | None) -> dict:
    if (resume or STATE_PATH.exists()) and STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return make_initial_state(root_url, depth)


def save_state(state: dict) -> None:
    state["updated_at"] = utc_now()
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def should_expand(current_depth: int, max_depth: int | None) -> bool:
    if max_depth is None:
        return True
    return current_depth < max_depth


def sync_state_with_disk(state: dict) -> dict:
    state.setdefault("errors", {})
    state.setdefault("pending", [])
    state.setdefault("seen_urls", [])
    state.setdefault("fetched_urls", [])
    state.setdefault("out_links", {})
    state.setdefault("url_to_title", {})
    state.setdefault("written_files", {})

    raw_urls: set[str] = set()
    if RAW_ROOT.exists():
        for raw_path in RAW_ROOT.glob("*.md"):
            metadata, _ = parse_markdown(raw_path)
            url = metadata.get("url") or metadata.get("requestedUrl") or metadata.get("source")
            title = metadata.get("title")
            if not url:
                continue
            raw_urls.add(url)
            if title:
                state["url_to_title"][url] = title

    written_files: dict[str, str] = {}
    for md_path in OUTPUT_ROOT.glob("*.md"):
        if md_path.name in {"README.md"}:
            continue
        metadata = parse_frontmatter_file(md_path)
        url = metadata.get("source") or metadata.get("url")
        title = metadata.get("title")
        if not url:
            continue
        written_files[url] = str(md_path.relative_to(REPO_ROOT))
        if title:
            state["url_to_title"][url] = title

    fetched_urls = set(state.get("fetched_urls", [])) | raw_urls | set(written_files.keys())
    seen_urls = set(state.get("seen_urls", [])) | fetched_urls

    dedup_pending: list[dict[str, int | str]] = []
    pending_seen: set[str] = set()
    for item in state.get("pending", []):
        url = str(item["url"])
        if url in fetched_urls or url in pending_seen:
            continue
        pending_seen.add(url)
        dedup_pending.append({"url": url, "depth": int(item["depth"])})

    state["written_files"] = written_files
    state["fetched_urls"] = sorted(fetched_urls)
    state["seen_urls"] = sorted(seen_urls)
    state["pending"] = dedup_pending
    return state


def write_note_from_raw(url: str, raw_path: Path, state: dict) -> Path:
    metadata, body = parse_markdown(raw_path)
    title = metadata.get("title") or state.get("url_to_title", {}).get(url) or slug_from_url(url).replace("_", " ")
    state.setdefault("url_to_title", {})[url] = title
    rewritten = rewrite_links(body, state["url_to_title"])
    final_path = write_obsidian_note(title, url, rewritten)
    state.setdefault("written_files", {})[url] = str(final_path.relative_to(REPO_ROOT))
    return final_path


def rebuild_pending_from_raw(state: dict) -> list[dict[str, int | str]]:
    root_url = state.get("root_url", ROOT_URL)
    max_depth = state.get("depth")
    raw_bodies: dict[str, str] = {}
    for raw_path in RAW_ROOT.glob("*.md"):
        metadata, body = parse_markdown(raw_path)
        url = metadata.get("url") or metadata.get("requestedUrl") or metadata.get("source")
        if url:
            raw_bodies[url] = body

    if root_url not in raw_bodies and root_url not in set(state.get("fetched_urls", [])):
        return []

    seen_bfs: set[str] = set()
    missing: list[dict[str, int | str]] = []
    queue: list[tuple[str, int]] = [(root_url, 0)]

    while queue:
        url, depth = queue.pop(0)
        if url in seen_bfs:
            continue
        seen_bfs.add(url)

        if url not in raw_bodies:
            if url not in set(state.get("fetched_urls", [])):
                missing.append({"url": url, "depth": depth})
            continue

        if not should_expand(depth, max_depth):
            continue

        for _, linked_url in extract_site_links(raw_bodies[url]):
            if linked_url not in seen_bfs:
                queue.append((linked_url, depth + 1))

    dedup: list[dict[str, int | str]] = []
    added: set[str] = set()
    fetched = set(state.get("fetched_urls", []))
    for item in missing:
        url = str(item["url"])
        if url in fetched or url in added:
            continue
        added.add(url)
        dedup.append(item)
    return dedup


def rebuild_pending_from_state_graph(state: dict) -> list[dict[str, int | str]]:
    root_url = state.get("root_url", ROOT_URL)
    max_depth = state.get("depth")
    out_links: dict[str, list[str]] = state.get("out_links", {})
    fetched = set(state.get("fetched_urls", []))

    if root_url not in fetched and root_url not in out_links:
        return []

    seen_bfs: set[str] = set()
    missing: list[dict[str, int | str]] = []
    queue: list[tuple[str, int]] = [(root_url, 0)]

    while queue:
        url, depth = queue.pop(0)
        if url in seen_bfs:
            continue
        seen_bfs.add(url)

        if url not in fetched:
            missing.append({"url": url, "depth": depth})
            continue

        if not should_expand(depth, max_depth):
            continue

        for linked_url in out_links.get(url, []):
            if linked_url not in seen_bfs:
                queue.append((linked_url, depth + 1))

    dedup: list[dict[str, int | str]] = []
    added: set[str] = set()
    for item in missing:
        url = str(item["url"])
        if url in fetched or url in added:
            continue
        added.add(url)
        dedup.append(item)
    return dedup


def seed_pending(root_url: str) -> list[dict[str, int | str]]:
    return [{"url": root_url, "depth": 0}]


def crawl(state: dict) -> None:
    fetched_urls: set[str] = set(state.get("fetched_urls", []))
    pending: list[dict[str, int | str]] = state.get("pending", [])
    processed_count = len(fetched_urls)
    run_seen: set[str] = set()
    run_queued: set[str] = {str(item["url"]) for item in pending}

    while pending:
        item = pending.pop(0)
        url = str(item["url"])
        current_depth = int(item["depth"])
        run_queued.discard(url)
        if url in run_seen:
            continue
        run_seen.add(url)

        state["pending"] = pending
        save_state(state)

        already_done = url in fetched_urls and url in state.get("written_files", {})
        if already_done:
            note_name = Path(state["written_files"][url]).name
            log(
                f'[skip] depth={current_depth} done={processed_count} queued={len(pending)} seen={len(run_seen)} file="{note_name}" url={url}'
            )
            out_links = state.get("out_links", {}).get(url, [])
            if not should_expand(current_depth, state.get("depth")):
                continue
        else:
            log(
                f"[fetch] depth={current_depth} done={processed_count} queued={len(pending)} seen={len(run_seen)} url={url}"
            )

            try:
                raw_path = fetch_url(url)
            except Exception as exc:
                state.setdefault("errors", {})[url] = str(exc)
                state["pending"] = [{"url": url, "depth": current_depth}] + pending
                save_state(state)
                log(f"[error] depth={current_depth} url={url} message={str(exc)}")
                raise

            fetched_urls.add(url)
            state["fetched_urls"] = sorted(fetched_urls)
            final_path = write_note_from_raw(url, raw_path, state)
            processed_count = len(fetched_urls)
            save_state(state)
            log(
                f'[saved] done={processed_count} queued={len(pending)} file="{final_path.name}"'
            )

            if not should_expand(current_depth, state.get("depth")):
                continue

            _, body = parse_markdown(raw_path)
            out_links = [linked_url for _, linked_url in extract_site_links(body)]
            state.setdefault("out_links", {})[url] = out_links
            save_state(state)

        added = 0
        for linked_url in out_links:
            if linked_url in run_seen or linked_url in run_queued:
                continue
            pending.append({"url": linked_url, "depth": current_depth + 1})
            run_queued.add(linked_url)
            added += 1

        state["seen_urls"] = sorted(set(state.get("seen_urls", [])) | run_seen | run_queued)
        state["pending"] = pending
        save_state(state)
        log(
            f"[expand] added={added} queued={len(pending)} seen={len(run_seen) + len(run_queued)} from={slug_from_url(url)}"
        )


def write_manifest(state: dict) -> None:
    manifest = OUTPUT_ROOT / "README.md"
    depth_value = state.get("depth")
    depth_text = "all" if depth_value is None else str(depth_value)
    lines = [
        "# Andy Matuschak Evergreen Notes",
        "",
        f"抓取时间: {utc_now()}",
        f"根页面: {state.get('root_url', ROOT_URL)}",
        f"抓取层级: {depth_text}",
        f"页面数量: {len(state.get('written_files', {}))}",
        f"待抓数量: {len(state.get('pending', []))}",
        "",
        "已抓取页面:",
        "",
    ]
    for path in sorted(state.get("written_files", {}).values()):
        lines.append(f"- {path}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cleanup_raw() -> None:
    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)


def parse_depth(value: str) -> int | None:
    if value == "all":
        return None
    depth = int(value)
    return max(depth, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Andy Matuschak notes into local Markdown with Obsidian wikilinks."
    )
    parser.add_argument(
        "url",
        help="Root URL to crawl. This page is treated as depth 0.",
    )
    parser.add_argument(
        "--depth",
        default="1",
        help='Recursion depth, default: 1. Use "all" for the whole reachable site graph.',
    )
    parser.add_argument("--resume", action="store_true", help="Resume from crawl-state.json")
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep temporary raw markdown files for resume or inspection",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    depth = parse_depth(args.depth)
    root_url = args.url
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    state = load_state(args.resume, root_url, depth)
    if state.get("root_url") != root_url:
        state = make_initial_state(root_url, depth)
    state["root_url"] = root_url
    state["depth"] = depth

    state = sync_state_with_disk(state)
    state["pending"] = seed_pending(root_url)
    save_state(state)

    log(
        f"[resume] fetched={len(state.get('fetched_urls', []))} queued={len(state.get('pending', []))} written={len(state.get('written_files', {}))} depth={'all' if state.get('depth') is None else state.get('depth')}"
    )

    crawl(state)
    write_manifest(state)
    log(
        f"[done] written={len(state.get('written_files', {}))} queued={len(state.get('pending', []))} state={STATE_PATH.relative_to(REPO_ROOT)}"
    )

    if not args.keep_raw:
        cleanup_raw()


if __name__ == "__main__":
    main()
