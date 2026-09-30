"""창고 재고 집계용 공용 파서 모듈 (run02, 2차 기준).

warehouse-*.md 는 다음 형식의 마크다운 표이다:

    # 창고 X 재고

    | 품목 | 수량 |
    |---|---:|
    | mug | 12 |
    ...

파싱 규칙(practice/출력형식.md 기준):
- `|` 로 분리 후 양끝 공백을 제거하여 (품목, 수량) 2컬럼을 얻는다.
- 헤더 행(`품목`/`수량`), 구분선(`---`, `:---:`) 행, 빈 행, `#` 제목 행은 건너뛴다.
- 수량은 정수로 파싱한다.

run02 저재고 기준(2차): 전 창고 품목별 총수량(item_total)이 5 미만(quantity < 5).
low_stock_basis 값은 항상 "item_total", threshold=5.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# 저재고 판정 기준 상수 (2차 기준)
LOW_STOCK_THRESHOLD = 5
LOW_STOCK_BASIS = "item_total"


def parse_warehouse(path: str) -> List[Tuple[str, int]]:
    """단일 warehouse md 파일을 읽어 (품목명, 수량) 리스트를 원본 행 순서대로 반환한다.

    헤더/구분선/제목/빈 행은 건너뛴다. 수량은 int 로 변환한다.
    """
    rows: List[Tuple[str, int]] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or not line.startswith("|"):
                # 표 행이 아닌 행(제목, 빈 행 등)은 무시
                continue
            # 파이프로 분리하고 양끝 공백 제거. 선행/후행 빈 셀 제거.
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            item, qty = cells[0], cells[1]
            # 헤더 행 건너뛰기
            if item == "품목" and qty == "수량":
                continue
            # 구분선 행(예: --- / :---: ) 건너뛰기
            if set(item) <= set("-: ") and set(qty) <= set("-: "):
                continue
            try:
                quantity = int(qty)
            except ValueError:
                # 수량이 정수가 아니면 데이터 행이 아니므로 건너뛴다.
                continue
            rows.append((item, quantity))
    return rows


def compute_total(rows: List[Tuple[str, int]]) -> int:
    """창고 합계(전체 수량 합)를 계산한다."""
    return sum(qty for _item, qty in rows)


def compute_items(rows: List[Tuple[str, int]]) -> Dict[str, int]:
    """품목별 수량 집계 매핑을 반환한다(같은 품목이 여러 행이면 합산)."""
    items: Dict[str, int] = {}
    for item, qty in rows:
        items[item] = items.get(item, 0) + qty
    return items


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        parsed = parse_warehouse(sys.argv[1])
        print("rows:", parsed)
        print("total:", compute_total(parsed))
        print("items:", compute_items(parsed))
