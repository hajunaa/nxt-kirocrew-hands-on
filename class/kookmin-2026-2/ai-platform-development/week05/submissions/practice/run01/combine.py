"""세 중간 파일(intermediate_a/b/c.json)을 통합하여 result.json 과 report.md 를 생성한다.

practice/출력형식.md 구조를 그대로 따른다:
- warehouses: {코드: {total, items}}
- item_totals: 전 창고 품목별 총수량 합산
- low_stock: 창고 A→B→C 순, 각 창고 내 원본 행 순서 유지.
             각 원소는 {warehouse, item, quantity}.
- low_stock_basis: 항상 "warehouse_row".

저재고 기준: 원본에 기록된 창고별 행의 수량이 5 미만(quantity < 5).
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

LOW_STOCK_BASIS = "warehouse_row"
WAREHOUSE_ORDER = ["A", "B", "C"]

HERE = os.path.dirname(os.path.abspath(__file__))


def load_intermediate(code: str) -> dict:
    path = os.path.join(HERE, f"intermediate_{code.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_result() -> dict:
    warehouses: Dict[str, dict] = {}
    item_totals: Dict[str, int] = {}
    low_stock: List[dict] = []

    for code in WAREHOUSE_ORDER:
        data = load_intermediate(code)
        total = int(data["total"])
        items = {str(k): int(v) for k, v in data["items"].items()}

        warehouses[code] = {"total": total, "items": items}

        # 전 창고 품목별 총수량 합산
        for item, qty in items.items():
            item_totals[item] = item_totals.get(item, 0) + qty

        # 저재고 병합: warehouse 코드 주입, 원본 행 순서 유지
        for entry in data["low_stock"]:
            low_stock.append(
                {
                    "warehouse": code,
                    "item": entry["item"],
                    "quantity": int(entry["quantity"]),
                }
            )

    return {
        "warehouses": warehouses,
        "item_totals": item_totals,
        "low_stock": low_stock,
        "low_stock_basis": LOW_STOCK_BASIS,
    }


def write_result_json(result: dict) -> str:
    path = os.path.join(HERE, "result.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def write_report_md(result: dict) -> str:
    path = os.path.join(HERE, "report.md")
    lines: List[str] = []
    lines.append("# 창고 재고 집계 리포트")
    lines.append("")
    lines.append(f"- 저재고 기준(low_stock_basis): `{result['low_stock_basis']}` (창고별 행 수량 < 5)")
    lines.append("")

    # 창고별 합계
    lines.append("## 창고별 합계")
    lines.append("")
    lines.append("| 창고 | 합계 |")
    lines.append("| --- | --- |")
    for code in WAREHOUSE_ORDER:
        lines.append(f"| {code} | {result['warehouses'][code]['total']} |")
    lines.append("")

    # 창고별 품목 수량
    for code in WAREHOUSE_ORDER:
        lines.append(f"## 창고 {code} 품목별 수량")
        lines.append("")
        lines.append("| 품목 | 수량 |")
        lines.append("| --- | --- |")
        for item, qty in result["warehouses"][code]["items"].items():
            lines.append(f"| {item} | {qty} |")
        lines.append("")

    # 품목별 총수량
    lines.append("## 전 창고 품목별 총수량")
    lines.append("")
    lines.append("| 품목 | 총수량 |")
    lines.append("| --- | --- |")
    for item, qty in result["item_totals"].items():
        lines.append(f"| {item} | {qty} |")
    lines.append("")

    # 저재고 목록
    lines.append("## 저재고 목록 (수량 < 5)")
    lines.append("")
    lines.append("| 창고 | 품목 | 수량 |")
    lines.append("| --- | --- | --- |")
    for entry in result["low_stock"]:
        lines.append(f"| {entry['warehouse']} | {entry['item']} | {entry['quantity']} |")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main() -> None:
    result = build_result()
    rj = write_result_json(result)
    rm = write_report_md(result)
    print("wrote:", rj)
    print("wrote:", rm)
    print("item_totals:", result["item_totals"])
    print("low_stock count:", len(result["low_stock"]))


if __name__ == "__main__":
    main()
