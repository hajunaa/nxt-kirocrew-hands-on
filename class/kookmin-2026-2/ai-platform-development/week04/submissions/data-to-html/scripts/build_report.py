#!/usr/bin/env python3
"""리포트 JSON을 검사하고, 통과하면 단일 HTML 리포트로 생성한다.

판단·요약은 하지 않는다. AI가 만든 JSON의 구조를 검사(validate)하고,
통과하면 자립형 HTML을 만든다(build).

스키마는 ../SKILL.md 참고.
"""

import argparse
import datetime
import html
import json
import sys


class ValidationError(Exception):
    """검사 실패. 사용자에게 보여줄 이유를 담는다."""


def _require(cond, msg):
    if not cond:
        raise ValidationError(msg)


def _check_str(value, where):
    _require(isinstance(value, str), f"{where}: 문자열이어야 합니다 (받은 값: {type(value).__name__})")
    return value


def _check_str_list(value, where):
    _require(isinstance(value, list), f"{where}: 목록이어야 합니다 (받은 값: {type(value).__name__})")
    for i, item in enumerate(value):
        _require(isinstance(item, str), f"{where}[{i}]: 목록 원소는 문자열이어야 합니다 (받은 값: {type(item).__name__})")
    return value


def _check_date(value, where):
    _check_str(value, where)
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise ValidationError(f"{where}: YYYY-MM-DD 형식의 실제 날짜여야 합니다 (받은 값: {value!r})")
    return value


ALLOWED_TOP = {"title", "generated_at", "documents", "tables"}
ALLOWED_DOC = {"source", "summary"}
ALLOWED_TABLE = {"source", "caption", "columns", "rows"}


def _check_extra_keys(obj, allowed, where):
    extra = set(obj) - allowed
    _require(not extra, f"{where}: 허용되지 않은 항목이 있습니다: {sorted(extra)}")
    missing = allowed - set(obj)
    _require(not missing, f"{where}: 필수 항목이 없습니다: {sorted(missing)}")


def validate(data):
    """리포트 JSON을 검사하고 정규화된 dict를 돌려준다. 실패 시 ValidationError."""
    _require(isinstance(data, dict), "최상위 값은 객체(JSON object)여야 합니다")
    _check_extra_keys(data, ALLOWED_TOP, "최상위")

    _check_str(data["title"], "title")
    _check_date(data["generated_at"], "generated_at")

    documents = data["documents"]
    _require(isinstance(documents, list), "documents: 목록이어야 합니다")
    for i, doc in enumerate(documents):
        where = f"documents[{i}]"
        _require(isinstance(doc, dict), f"{where}: 객체여야 합니다")
        _check_extra_keys(doc, ALLOWED_DOC, where)
        _check_str(doc["source"], f"{where}.source")
        _check_str_list(doc["summary"], f"{where}.summary")

    tables = data["tables"]
    _require(isinstance(tables, list), "tables: 목록이어야 합니다")
    for i, table in enumerate(tables):
        where = f"tables[{i}]"
        _require(isinstance(table, dict), f"{where}: 객체여야 합니다")
        _check_extra_keys(table, ALLOWED_TABLE, where)
        _check_str(table["source"], f"{where}.source")
        _check_str(table["caption"], f"{where}.caption")
        columns = _check_str_list(table["columns"], f"{where}.columns")
        _require(len(columns) > 0, f"{where}.columns: 최소 한 개의 열이 필요합니다")
        rows = table["rows"]
        _require(isinstance(rows, list), f"{where}.rows: 목록이어야 합니다")
        for j, row in enumerate(rows):
            _check_str_list(row, f"{where}.rows[{j}]")
            _require(
                len(row) == len(columns),
                f"{where}.rows[{j}]: 셀 개수({len(row)})가 columns 개수({len(columns)})와 다릅니다",
            )

    _require(
        len(documents) > 0 or len(tables) > 0,
        "documents와 tables가 둘 다 비어 있습니다. 최소 하나는 있어야 합니다",
    )
    return data


def _esc(s):
    return html.escape(str(s), quote=True)


def build_html(data):
    """검사에 통과한 dict를 자립형 HTML 문자열로 만든다."""
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ko">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append(f"<title>{_esc(data['title'])}</title>")
    parts.append("<style>")
    parts.append(
        "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;"
        "max-width:860px;margin:0 auto;padding:2rem 1.25rem;line-height:1.6;color:#1a1a1a}"
        "h1{font-size:1.6rem;margin-bottom:0.25rem}"
        ".meta{color:#666;font-size:0.9rem;margin-bottom:2rem}"
        "h2{font-size:1.2rem;margin-top:2.5rem;border-bottom:2px solid #eee;padding-bottom:0.3rem}"
        "h3{font-size:1.02rem;margin-top:1.5rem;margin-bottom:0.4rem}"
        "ul{margin-top:0.3rem}"
        "table{border-collapse:collapse;width:100%;margin:0.5rem 0 1.5rem;font-size:0.92rem}"
        "caption{text-align:left;color:#555;font-size:0.88rem;margin-bottom:0.4rem;caption-side:top}"
        "th,td{border:1px solid #ddd;padding:0.4rem 0.6rem;text-align:left;vertical-align:top}"
        "th{background:#f5f5f5;font-weight:600}"
        "tr:nth-child(even) td{background:#fafafa}"
    )
    parts.append("</style>")
    parts.append("</head>")
    parts.append("<body>")

    parts.append(f"<h1>{_esc(data['title'])}</h1>")
    parts.append(f'<div class="meta">생성일: {_esc(data["generated_at"])}</div>')

    if data["documents"]:
        parts.append("<h2>문서 요약</h2>")
        for doc in data["documents"]:
            parts.append(f"<h3>{_esc(doc['source'])}</h3>")
            if doc["summary"]:
                parts.append("<ul>")
                for line in doc["summary"]:
                    parts.append(f"<li>{_esc(line)}</li>")
                parts.append("</ul>")
            else:
                parts.append("<p><em>요약 없음</em></p>")

    if data["tables"]:
        parts.append("<h2>핵심 표</h2>")
        for table in data["tables"]:
            parts.append("<table>")
            cap = table["caption"] or table["source"]
            parts.append(f"<caption>{_esc(cap)} <small>({_esc(table['source'])})</small></caption>")
            parts.append("<thead><tr>")
            for col in table["columns"]:
                parts.append(f"<th>{_esc(col)}</th>")
            parts.append("</tr></thead>")
            parts.append("<tbody>")
            for row in table["rows"]:
                parts.append("<tr>")
                for cell in row:
                    parts.append(f"<td>{_esc(cell)}</td>")
                parts.append("</tr>")
            parts.append("</tbody>")
            parts.append("</table>")

    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="리포트 JSON을 검사하고 HTML을 생성한다")
    ap.add_argument("--in", dest="infile", help="입력 리포트 JSON 파일 (없으면 stdin)")
    ap.add_argument("--out", dest="outfile", help="출력 HTML 파일 (없으면 stdout)")
    ap.add_argument("--check-only", action="store_true", help="검사만 하고 HTML은 만들지 않는다")
    args = ap.parse_args(argv)

    raw = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}", file=sys.stderr)
        return 1

    try:
        data = validate(data)
    except ValidationError as e:
        print(f"검사 실패: {e}", file=sys.stderr)
        return 1

    if args.check_only:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    document = build_html(data)
    if args.outfile:
        with open(args.outfile, "w", encoding="utf-8") as f:
            f.write(document)
        print(f"HTML 리포트를 저장했습니다: {args.outfile}", file=sys.stderr)
    else:
        sys.stdout.write(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
