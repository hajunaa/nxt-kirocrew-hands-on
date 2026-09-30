"""창고 C 집계 작업 (A·B에 독립).

practice/data/warehouse-c.md 를 읽어 창고 C의 합계, 품목별 수량,
저재고 목록(수량<5)을 계산하고 intermediate_c.json 으로 저장한다.
"""

from __future__ import annotations

import json
import os

from warehouse_common import (
    LOW_STOCK_BASIS,
    compute_items,
    compute_low_stock,
    compute_total,
    parse_warehouse,
)

WAREHOUSE_CODE = "C"

# 이 스크립트 위치 기준으로 경로를 계산 (실행 CWD 에 무관하게 동작)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# submissions/practice/run01 -> 프로젝트 루트로 3단계 상위
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SOURCE_PATH = os.path.join(PROJECT_ROOT, "practice", "data", "warehouse-c.md")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "intermediate_c.json")


def main() -> None:
    rows = parse_warehouse(SOURCE_PATH)

    result = {
        "warehouse": WAREHOUSE_CODE,
        "total": compute_total(rows),
        "items": compute_items(rows),
        "low_stock": compute_low_stock(rows),
        "low_stock_basis": LOW_STOCK_BASIS,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"[창고 {WAREHOUSE_CODE}] intermediate 저장: {OUTPUT_PATH}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
