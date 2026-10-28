"""WEJイベントDB（Googleスプレッドシート）から公開用 events.json を生成する。

- スプレッドシートを正本とし、イベントはIDで照合する。
- 既存の掲載イベントがシートで「掲載」になっていない場合は削除せず停止する。
- 内部管理欄（備考など）は一切使用しない。公開欄に内部情報があれば停止する。
- いずれの失敗時も events.json は書き換えない。

使い方:
  python scripts/sync_events.py            # 同期して events.json を更新
  python scripts/sync_events.py --dry-run  # 照合結果の表示のみ（書き換えない）
  python scripts/sync_events.py --check    # 現在の events.json を検証のみ
"""

import argparse
import csv
import io
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SHEET_ID = "1_A0aQ2elKC4Rs_SET6WIHqwHbgAUZSnaB6A2TfvEzhs"
SHEET_GID = "1399683849"
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/export?format=csv&gid={SHEET_GID}"
)
OUTPUT = Path("events.json")
BACKUP = Path("events.json.backup")
MIN_EVENTS = 8

REQUIRED = {
    "ID", "掲載判定", "イベント名", "開催日",
    "カテゴリ", "都道府県", "会場", "公式URL"
}

# 公開サイトに出す項目。これ以外の列（備考・ステータス等）は公開データに使わない。
PUBLIC_TEXT_FIELDS = (
    "title", "dateLabel", "region", "category",
    "venue", "price", "publicDescription"
)
URL_FIELDS = ("url", "ticketUrl", "imageUrl")

# 公開欄の既定値。内部情報の検出対象から除外する。
PLACEHOLDERS = {"公式で確認"}

# 内部管理メモ・制作記録とみなす表現。見つかった場合は公開処理を停止する。
INTERNAL_PATTERNS = [
    (r"canva", "Canva"),
    (r"WEJ-", "管理ID（WEJ-）"),
    (r"github", "GitHub"),
    (r"Webサイト変更", "サイト作業記録"),
    (r"フィード\s*[0-9０-９]*\s*(?:枚|ページ)目", "Instagram制作記録"),
    (r"ストーリーズ", "Instagram制作記録"),
    (r"(?:イベント|既存)\s*DB|DB\s*(?:掲載|登録|未登録|未確認)", "DB管理記録"),
    (r"制作(?:記録|メモ)|内部(?:メモ|管理)|編集メモ|備考", "内部メモ"),
    (r"作業記録|未確認メモ|TODO|要確認メモ", "作業メモ"),
    (r"情報発表日|新規発見|新規把握|登録済み", "調査記録"),
    (r"【(?:新規|既存|重要更新)", "調査記録"),

]
INTERNAL_REGEXES = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in INTERNAL_PATTERNS
]


class SyncError(Exception):
    """同期を停止すべき問題。problems に個別の内容を持つ。"""

    def __init__(self, summary, problems=()):
        super().__init__(summary)
        self.problems = list(problems)


def find_internal_text(value):
    """公開欄の文字列に含まれる内部情報の種類を返す。"""
    text = str(value or "").strip()
    if not text or text in PLACEHOLDERS:
        return []
    found = []
    for regex, label in INTERNAL_REGEXES:
        match = regex.search(text)
        if match and label not in [item[0] for item in found]:
            found.append((label, match.group(0) or "（末尾）"))
    return found


def validate_events(events, *, check_internal=True):
    """公開用イベントデータを検証し、問題の一覧を返す（空なら合格）。"""
    problems = []
    seen = set()

    if not isinstance(events, list):
        return ["events.json がリスト形式ではありません。"]

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            problems.append(f"{index + 1}件目: オブジェクトではありません。")
            continue
        allowed = {"id", "date", "addedAt", *PUBLIC_TEXT_FIELDS, *URL_FIELDS}
        if set(event) - allowed:
            problems.append(f"{index + 1}件目: 未定義の公開フィールドがあります。")
        if any(not isinstance(value, str) for value in event.values()):
            problems.append(f"{index + 1}件目: 値は文字列である必要があります。")
            continue
        event_id = str(event.get("id") or "").strip()
        where = event_id or f"{index + 1}件目"

        if not re.fullmatch(r"WEJ-20\d{2}-\d{3,}", event_id):
            problems.append(f"{where}: IDがありません。")
        elif event_id in seen:
            problems.append(f"{where}: IDが重複しています。")
        seen.add(event_id)

        try:
            value = event.get("date", "")
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except ValueError:
            problems.append(f"{where}: 開催日(date)が不正です。")
        if not str(event.get("title") or "").strip():
            problems.append(f"{where}: イベント名がありません。")

        for field in PUBLIC_TEXT_FIELDS if check_internal else ():
            for label, hit in find_internal_text(event.get(field)):
                problems.append(
                    f"{where}: {field} に内部情報（{label}：「{hit}」）が含まれています。"
                )

        added = event.get("addedAt", "")
        if added:
            try:
                date.fromisoformat(added)
            except ValueError:
                problems.append(f"{where}: addedAt が不正です。")

        for field in URL_FIELDS:
            value = str(event.get(field) or "")
            if field == "url" and not value:
                problems.append(f"{where}: 公式URLがありません。")
            elif value and not is_https_url(value):
                problems.append(f"{where}: {field} がhttpsのURLではありません。")

    return problems


def is_https_url(value):
    try:
        parsed = urlparse(value)
        _ = parsed.port
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and not re.search(r"[\s\x00-\x1f\x7f]", value))
    except ValueError:
        return False


def cell(row, name):
    return (row.get(name) or "").strip()


def build_events(csv_text, existing):
    """シートCSVと既存の公開データから新しい公開データを作る。

    問題があれば SyncError を送出する（呼び出し側はファイルを書き換えない）。
    """
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")), strict=True)

    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        missing = sorted(REQUIRED - set(reader.fieldnames or []))
        raise SyncError("シートの見出しが不正です。", [f"不足している列: {missing}"])

    problems = validate_events(existing, check_internal=False)
    if problems:
        raise SyncError("既存公開データが不正です。", problems)
    if not existing:
        raise SyncError("既存公開データが空です。初期化は明示的なレビューが必要です。")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise SyncError("シートの見出しが重複しています。")
    existing_by_id = {}
    problems = []
    for item in existing:
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            problems.append(f"既存データにIDのないイベントがあります: {item.get('title')}")
            continue
        existing_by_id[item_id] = item

    events = []
    sheet_status = {}
    seen_ids = set()

    for line, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            problems.append(f"シート{line}行目: 列数が見出しと一致しません。")
            continue
        event_id = cell(row, "ID")
        if event_id:
            if event_id in seen_ids:
                problems.append(f"シート{line}行目（{event_id}）: IDが重複しています。")
            seen_ids.add(event_id)
        judgement = cell(row, "掲載判定")
        if event_id and event_id not in sheet_status:
            sheet_status[event_id] = judgement
        if judgement != "掲載":
            continue

        where = f"シート{line}行目（{event_id or 'ID未入力'}）"
        name = cell(row, "イベント名")
        raw_date = cell(row, "開催日")
        url = cell(row, "公式URL")

        if not event_id:
            problems.append(f"{where}: IDがありません。")
            continue
        if any(e["id"] == event_id for e in events):
            problems.append(f"{where}: 掲載行のIDが重複しています。")
            continue
        if not name:
            problems.append(f"{where}: イベント名がありません。")
            continue

        match = re.match(r"(20\d{2})/(\d{1,2})(?:/(\d{1,2}))?(?![\d/])", raw_date)
        try:
            event_date = date(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3) or 1)
            ).isoformat()
        except (AttributeError, ValueError):
            problems.append(f"{where}: 開催日「{raw_date}」を読み取れません。")
            continue

        if not is_https_url(url):
            problems.append(f"{where}: 公式URLがhttpsのURLではありません。")
            continue

        old = existing_by_id.get(event_id, {})

        # 公開用説明が未登録なら、既存の承認済み説明文を保持する（切り取りはしない）。
        description = cell(row, "公開用説明")
        if description and description == cell(row, "備考"):
            problems.append(f"{where}: 公開用説明が備考（内部メモ）と同一です。")
        if not description:
            description = str(old.get("publicDescription") or "")

        events.append({
            "id": event_id,
            "title": name,
            "date": event_date,
            "addedAt": (cell(row, "最終更新日") or cell(row, "確認日")).replace("/", "-"),
            "imageUrl": keep_https(cell(row, "画像URL"), old.get("imageUrl")),
            "dateLabel": raw_date,
            "region": cell(row, "都道府県"),
            "category": cell(row, "カテゴリ") or "その他",
            "venue": cell(row, "会場") or "公式で確認",
            "price": cell(row, "料金") or "公式で確認",
            "publicDescription": description,
            "ticketUrl": keep_https(cell(row, "チケットURL"), old.get("ticketUrl")),
            "url": url
        })

    # 既存の掲載イベントがシートで掲載になっていなければ、削除せず停止する。
    published_ids = {e["id"] for e in events}
    for item_id, item in existing_by_id.items():
        if item_id in published_ids:
            continue
        state = sheet_status.get(item_id)
        reason = "シートに行がありません" if state is None else f"掲載判定が「{state or '空欄'}」です"
        problems.append(
            f"{item_id}（{item.get('title')}）: 現在公開中ですが、{reason}。"
        )

    if problems:
        raise SyncError("シートのデータに問題があるため同期を停止しました。", problems)

    if len(events) < MIN_EVENTS:
        raise SyncError(f"掲載イベントが{len(events)}件しかありません（最低{MIN_EVENTS}件）。")

    problems = validate_events(events)
    if problems:
        raise SyncError("公開データに内部情報または不正な値があるため同期を停止しました。", problems)

    events.sort(key=lambda item: (item["date"], item["title"]))
    return events


def keep_https(new_value, old_value):
    """https のURLのみ採用し、未登録なら既存の値を保持する。"""
    value = new_value or str(old_value or "")
    return value  # 不正URLは削除で隠さず validate_events で安全停止する


def fetch_csv():
    request = urllib.request.Request(
        CSV_URL,
        headers={"User-Agent": "WEJ-Event-Sync/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise SyncError("CSVが大きすぎます。")
    return raw.decode("utf-8-sig")


def load_existing():
    if not OUTPUT.exists():
        raise SyncError("既存の events.json がありません。同期を停止します。")
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def describe_changes(old_events, new_events):
    old_by_id = {e.get("id"): e for e in old_events}
    lines = []
    for event in new_events:
        before = old_by_id.get(event["id"])
        if before is None:
            lines.append(f"追加: {event['id']} {event['title']}")
            continue
        changed = [key for key in event if event[key] != before.get(key)]
        if changed:
            lines.append(f"更新: {event['id']} {', '.join(changed)}")
    return lines


def report_error(error):
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "エラー: "
    print(f"{prefix}{error}", file=sys.stderr)
    for problem in getattr(error, "problems", []):
        print(f"{prefix}  - {problem}", file=sys.stderr)
    print("既存の events.json は変更していません。", file=sys.stderr)


def check():
    try:
        events = load_existing()
        problems = validate_events(events)
        if not events or problems:
            raise SyncError("events.json に問題があります。", problems)
    except Exception as error:
        report_error(error)
        return 1
    print("events.json の検証に合格しました。")
    return 0


def sync(dry_run=False, fetch=fetch_csv):
    try:
        existing = load_existing()
        if not dry_run and OUTPUT.exists():
            shutil.copy2(OUTPUT, BACKUP)
        events = build_events(fetch(), existing)
    except Exception as error:  # 失敗時は events.json に一切触れない
        report_error(error)
        return 1

    for line in describe_changes(existing, events):
        print(line)

    if dry_run:
        print(f"照合のみ実行しました（{len(events)}件）。events.json は変更していません。")
        return 0

    temporary = OUTPUT.with_suffix(".json.tmp")
    try:
        temporary.write_text(
            json.dumps(events, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        temporary.replace(OUTPUT)
    except Exception as error:
        temporary.unlink(missing_ok=True)
        report_error(error)
        return 1

    print(f"Synced {len(events)} published events.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return check() if args.check else sync(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
