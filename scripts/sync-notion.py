#!/usr/bin/env python3
"""
Notion DB → Markdown 파일 동기화

사용법: python3 scripts/sync-notion.py
- Notion DB에서 상태=발행 글을 가져와 src/content/blog/ 에 .md 파일로 생성
- 빌드 전에 실행하면 Notion 글이 사이트에 반영됨
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests

# 설정
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DB_ID = os.environ.get("ELECTRIC_NOTION_DB", "")  # Notion DB ID (나중에 설정)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "content", "blog")
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def slugify(text):
    """한글 포함 슬러그 생성."""
    text = text.strip().lower()
    text = re.sub(r'[^\w\s가-힣-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text


def get_rich_text(prop):
    """Notion rich_text 속성에서 텍스트 추출."""
    return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))


def get_title(prop):
    """Notion title 속성에서 텍스트 추출."""
    return "".join(t.get("plain_text", "") for t in prop.get("title", []))


def get_select(prop):
    """Notion select 속성에서 값 추출."""
    sel = prop.get("select")
    return sel.get("name", "") if sel else ""


def get_blocks_as_markdown(page_id):
    """페이지 블록을 마크다운으로 변환."""
    blocks = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        data = resp.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    md_lines = []
    for block in blocks:
        btype = block.get("type", "")
        content = block.get(btype, {})
        rt = content.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rt)

        if btype == "heading_2":
            md_lines.append(f"\n## {text}\n")
        elif btype == "heading_3":
            md_lines.append(f"\n### {text}\n")
        elif btype == "paragraph":
            md_lines.append(f"{text}\n")
        elif btype == "bulleted_list_item":
            md_lines.append(f"- {text}")
        elif btype == "numbered_list_item":
            md_lines.append(f"1. {text}")
        elif btype == "quote":
            md_lines.append(f"> {text}\n")
        elif btype == "table":
            # 테이블은 하위 블록에서 처리 필요 — 간단히 스킵
            md_lines.append("[표]")
        elif btype == "divider":
            md_lines.append("\n---\n")

    return "\n".join(md_lines)


def sync():
    if not DB_ID:
        print("❌ ELECTRIC_NOTION_DB 환경변수가 설정되지 않았습니다.")
        print("   export ELECTRIC_NOTION_DB='your-database-id'")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 상태=발행 글 조회
    body = {
        "filter": {"property": "상태", "select": {"equals": "발행"}},
        "sorts": [{"property": "제목", "direction": "ascending"}],
    }
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        headers=HEADERS,
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("results", [])

    print(f"📄 {len(pages)}개 글 동기화 시작")

    for page in pages:
        props = page["properties"]

        title = get_title(props.get("제목", props.get("이름", {})))
        description = get_rich_text(props.get("설명", {}))
        keyword = get_rich_text(props.get("키워드", {}))
        service = get_select(props.get("서비스", {})) or "전기공사"
        region = get_rich_text(props.get("지역", {}))
        slug_text = get_rich_text(props.get("슬러그", {})) or slugify(title)

        if not title:
            continue

        # 본문 가져오기
        body_text = get_blocks_as_markdown(page["id"])

        # frontmatter
        frontmatter = f"""---
title: "{title}"
description: "{description}"
keyword: "{keyword}"
service: "{service}"
region: "{region}"
publishedAt: "{datetime.now().strftime('%Y-%m-%d')}"
---"""

        md_content = f"{frontmatter}\n\n{body_text}"

        filepath = os.path.join(OUTPUT_DIR, f"{slug_text}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  ✅ {slug_text}.md — {title}")

    print(f"\n✅ 동기화 완료 ({len(pages)}개)")


if __name__ == "__main__":
    sync()
