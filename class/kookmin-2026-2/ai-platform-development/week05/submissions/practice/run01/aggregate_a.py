"""창고 A 집계 작업 (DAG 독립 노드, B·C에 의존하지 않음).

practice/data/warehouse-a.md 를 읽어 창고 A의
- 합계(total)
- 품목별 수량(items)
- 저재고 목록(low_stock, 원본 행 수량 < 5)
을 계산하여 intermediate_a.json 중간 파일로 저장한다.

저재고 판정 기준: warehouse_row (원본에 기록된 창고별 행의 수량 < 5).
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

WAREHOUSE_CODE = "A"

# 이 스크립트 파일 기준 경로 해석 (실행 CWD 에 무관하게 동작)
HERE = os.path.dirname(os.path.abspath(__file__))
# submissions/practice/run01 -> 프로젝트 루트로 3단계 상위
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SOURCE_PATH = os.path.join(PROJECT_ROOT, "practice", "data", "warehouse-a.md")
OUTPUT_PATH = os.path.join(HERE, "intermediate_a.json")


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

    print(f"[aggregate_{WAREHOUSE_CODE.lower()}] wrote {OUTPUT_PATH}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
