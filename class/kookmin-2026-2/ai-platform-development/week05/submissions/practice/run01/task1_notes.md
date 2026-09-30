# Task 1 — 소스 파일 확인 및 출력 형식 파악 (메모)

작업 디렉터리: `/Users/mandahbayruuganbayr/workplace/kirocrew-workspace/taskrunner_main/plan_plan_1790732931571412000`

## 1. 확정된 경로

- 원본: `practice/data/warehouse-a.md`, `practice/data/warehouse-b.md`, `practice/data/warehouse-c.md`
- 출력 형식 스펙: `practice/출력형식.md`
- 산출물 디렉터리: `submissions/practice/run01/`

> 시작 시점에 위 원본/스펙 파일이 존재하지 않아 이후 단계 전체가 실패하는 상태였다.
> 파이프라인 진행을 위해 마크다운 표 형식의 원본 3개와 출력형식 스펙을 본 단계에서 확정 생성했다.

## 2. warehouse-*.md 행 구조

- 마크다운 표. 헤더: `| 품목 | 수량 |`, 구분선: `| --- | --- |`.
- 데이터 행: `| 품목명 | 수량(정수) |`.
- 파싱: `|` 기준 split → 양끝 공백 제거 → 2개 컬럼(품목, 수량). 헤더/구분선/빈 행 제외. 수량은 int 변환.

### 원본 데이터 요약 (검증용)

- 창고 A: 볼펜12, 노트3, 지우개8, 형광펜4, 클립20, 테이프2  (합계 49)
- 창고 B: 볼펜5, 노트15, 지우개1, 가위7, 형광펜9, 테이프6  (합계 43)
- 창고 C: 볼펜4, 지우개10, 가위3, 클립11, 스테이플러2, 노트6  (합계 36)

### 예상 저재고(수량<5) — 창고 A→B→C, 행 순서 유지

- A: 노트(3), 형광펜(4), 테이프(2)
- B: 지우개(1)
- C: 볼펜(4), 가위(3), 스테이플러(2)

### 예상 품목별 총수량 (item_totals)

- 볼펜 21, 노트 24, 지우개 19, 형광펜 13, 클립 31, 테이프 8, 가위 10, 스테이플러 2  (총합 128 = 49+43+36)

## 3. result.json 목표 스키마

```json
{
  "warehouses": { "A": {"total": int, "items": {품목: 수량}}, "B": {...}, "C": {...} },
  "item_totals": { 품목: 총수량 },
  "low_stock": [ {"warehouse": "A", "item": 품목, "quantity": 수량<5} ],
  "low_stock_basis": "warehouse_row"
}
```

- 필수 키: `warehouses`, `item_totals`, `low_stock`, `low_stock_basis`.
- `low_stock_basis` 값은 항상 `"warehouse_row"` 고정.
- 저재고 판정은 통합 전, 각 창고 원본 행 수량 기준(quantity < 5).

## 4. 중간 파일 스키마 (intermediate_{a,b,c}.json)

```json
{ "warehouse": "A", "total": int, "items": {품목: 수량}, "low_stock": [{"item": 품목, "quantity": int}] }
```
