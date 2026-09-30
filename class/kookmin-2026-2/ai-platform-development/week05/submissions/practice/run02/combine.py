"""통합 태스크 (DAG 통합 노드 — 집계 A/B/C 모두에 의존).

집계 중간 파일 intermediate_a.json / _b.json / _c.json 세 개를 읽어:
  1. 창고별 합계(warehouse_totals)와 전 창고 품목별 총수량(item_totals)을 계산하고
  2. 2차 기준(item_total)으로 총수량 < threshold(5) 인 품목을 저재고로 판정하고
  3. practice/출력형식.md 스키마에 맞춰 result.json 을 작성하고
  4. 짧은 report.md 를 생성한다.

이 태스크는 aggregate_a/b/c 세 중간 결과 모두에 의존한다.
판정 기준: low_stock_basis="item_total", threshold=5.
"""

from __future__ import annotations

import json
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

THRESHOLD = 5
LOW_STOCK_BASIS = "item_total"

# 창고 ID → 중간 결과 JSON (집계 태스크 A/B/C 산출물)
INTERMEDIATE_FILES = {
    "A": os.path.join(_THIS_DIR, "intermediate_a.json"),
    "B": os.path.join(_THIS_DIR, "intermediate_b.json"),
    "C": os.path.join(_THIS_DIR, "intermediate_c.json"),
}
# source_files 는 입력 파일명(정렬)으로 기록한다.
SOURCE_FILES = ["warehouse-a.md", "warehouse-b.md", "warehouse-c.md"]

RESULT_JSON = os.path.join(_THIS_DIR, "result.json")
REPORT_MD = os.path.join(_THIS_DIR, "report.md")


def load_intermediate(path: str) -> dict:
    """중간 파일 하나를 읽어 {warehouse, total, items} dict 를 반환한다."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ("warehouse", "total", "items"):
        if key not in data:
            raise ValueError(f"{path}: 필수 키 '{key}' 누락 (집계 태스크 미실행?)")
    return data


def integrate() -> tuple[dict, dict]:
    """세 중간 파일을 읽어 result.json dict 와 창고별 items 맵을 구성한다."""
    warehouse_totals: dict[str, int] = {}
    warehouse_items: dict[str, dict[str, int]] = {}
    item_totals: dict[str, int] = {}

    for wid in ("A", "B", "C"):
        data = load_intermediate(INTERMEDIATE_FILES[wid])
        items = {name: int(qty) for name, qty in data["items"].items()}
        warehouse_totals[wid] = int(data["total"])
        warehouse_items[wid] = items
        # 전 창고 품목별 총수량 누적 (원본 등장 순서 유지)
        for name, qty in items.items():
            item_totals[name] = item_totals.get(name, 0) + qty

    grand_total = sum(warehouse_totals.values())

    # 2차 기준: item_total < threshold. 검사기는 순서 무관이나 이름 오름차순으로 안정 출력.
    low_stock = [
        {"item": name, "quantity": item_totals[name]}
        for name in sorted(item_totals)
        if item_totals[name] < THRESHOLD
    ]

    result = {
        "source_files": SOURCE_FILES,
        "warehouse_totals": warehouse_totals,
        "item_totals": item_totals,
        "grand_total": grand_total,
        "low_stock_basis": LOW_STOCK_BASIS,
        "threshold": THRESHOLD,
        "low_stock": low_stock,
    }
    return result, warehouse_items


def build_report(result: dict, warehouse_items: dict[str, dict[str, int]]) -> str:
    """result dict 로부터 report.md 문자열을 생성한다."""
    lines: list[str] = []
    lines.append("# 창고 재고 통합 리포트 (2차)")
    lines.append("")
    lines.append(f"- 저재고 기준(low_stock_basis): `{result['low_stock_basis']}` "
                 f"(전 창고 품목별 총수량 < {result['threshold']})")
    lines.append(f"- 사용 입력: {', '.join(result['source_files'])}")
    lines.append("")

    lines.append("## 창고별 합계")
    lines.append("| 창고 | 합계 |")
    lines.append("| --- | ---: |")
    for wid in ("A", "B", "C"):
        lines.append(f"| {wid} | {result['warehouse_totals'][wid]} |")
    lines.append("")

    lines.append("## 전 창고 품목별 총수량")
    lines.append("| 품목 | 총수량 |")
    lines.append("| --- | ---: |")
    for name, qty in result["item_totals"].items():
        lines.append(f"| {name} | {qty} |")
    lines.append("")
    lines.append(f"전체 총 수량(grand_total): {result['grand_total']}")
    lines.append("")

    lines.append(f"## 저재고 목록 (총수량 < {result['threshold']})")
    if result["low_stock"]:
        lines.append("| 품목 | 총수량 |")
        lines.append("| --- | ---: |")
        for row in result["low_stock"]:
            lines.append(f"| {row['item']} | {row['quantity']} |")
    else:
        lines.append("- (없음)")
    lines.append("")
    lines.append(
        f"판정 기준: low_stock_basis={result['low_stock_basis']}, "
        f"threshold={result['threshold']}"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    result, warehouse_items = integrate()

    with open(RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[combine] wrote {RESULT_JSON}")

    report = build_report(result, warehouse_items)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[combine] wrote {REPORT_MD}")

    print(f"  warehouse_totals={result['warehouse_totals']}")
    print(f"  grand_total={result['grand_total']}")
    print(f"  item_totals={result['item_totals']}")
    print(f"  low_stock={result['low_stock']}")


if __name__ == "__main__":
    main()
