"""창고 B 집계 작업 (DAG의 독립 노드; A·C에 의존하지 않음).

practice/data/warehouse-b.md 를 읽어 창고 B의
  - 합계(total)
  - 품목별 수량(items)
  - 저재고 목록(low_stock, 수량 < 5, low_stock_basis='warehouse_row')
을 계산하여 intermediate_b.json 중간 파일로 저장한다.
"""

from __future__ import annotations

import json
import os

import warehouse_common as wc

# 이 스크립트 파일 위치 기준으로 경로 계산 (작업 디렉터리에 무관하게 동작)
HERE = os.path.dirname(os.path.abspath(__file__))
# submissions/practice/run01 -> 프로젝트 루트로 3단계 상위
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

WAREHOUSE_CODE = "B"
SOURCE_PATH = os.path.join(PROJECT_ROOT, "practice", "data", "warehouse-b.md")
OUTPUT_PATH = os.path.join(HERE, "intermediate_b.json")


def main() -> None:
    rows = wc.parse_warehouse(SOURCE_PATH)
    total = wc.compute_total(rows)
    items = wc.compute_items(rows)
    low_stock = wc.compute_low_stock(rows)

    result = {
        "warehouse": WAREHOUSE_CODE,
        "total": total,
        "items": items,
        # 창고 코드를 붙여 통합 단계(combine.py)에서 바로 사용 가능하게 한다.
        "low_stock": [
            {"warehouse": WAREHOUSE_CODE, "item": ls["item"], "quantity": ls["quantity"]}
            for ls in low_stock
        ],
        "low_stock_basis": wc.LOW_STOCK_BASIS,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"[창고 {WAREHOUSE_CODE}] total={total}")
    print(f"[창고 {WAREHOUSE_CODE}] items={items}")
    print(f"[창고 {WAREHOUSE_CODE}] low_stock={result['low_stock']}")
    print(f"[창고 {WAREHOUSE_CODE}] wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
