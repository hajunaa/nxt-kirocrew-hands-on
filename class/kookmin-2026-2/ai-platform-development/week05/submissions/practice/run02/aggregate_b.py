"""창고 B 집계 태스크 (DAG 노드 B — A/C 와 독립 실행 가능).

practice/data/warehouse-b.md 를 읽어 창고 B 의 total 과 품목별 수량을 계산하고
중간 파일 intermediate_b.json 에 저장한다.
"""

from __future__ import annotations

import json
import os

from warehouse_common import compute_items, compute_total, parse_warehouse

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_WEEK_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

WAREHOUSE = "B"
INPUT_MD = os.path.join(_WEEK_ROOT, "practice", "data", "warehouse-b.md")
OUTPUT_JSON = os.path.join(_THIS_DIR, "intermediate_b.json")


def aggregate() -> dict:
    rows = parse_warehouse(INPUT_MD)
    return {
        "warehouse": WAREHOUSE,
        "total": compute_total(rows),
        "items": compute_items(rows),
    }


def main() -> None:
    result = aggregate()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[aggregate_{WAREHOUSE.lower()}] wrote {OUTPUT_JSON}")
    print(f"  warehouse={WAREHOUSE} total={result['total']} items={result['items']}")


if __name__ == "__main__":
    main()
