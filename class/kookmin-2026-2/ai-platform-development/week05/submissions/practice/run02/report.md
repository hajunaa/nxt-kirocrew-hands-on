# 창고 재고 통합 리포트 (2차)

- 저재고 기준(low_stock_basis): `item_total` (전 창고 품목별 총수량 < 5)
- 사용 입력: warehouse-a.md, warehouse-b.md, warehouse-c.md

## 창고별 합계
| 창고 | 합계 |
| --- | ---: |
| A | 22 |
| B | 16 |
| C | 16 |

## 전 창고 품목별 총수량
| 품목 | 총수량 |
| --- | ---: |
| mug | 17 |
| bottle | 12 |
| sensor | 11 |
| hub | 13 |
| cable | 1 |

전체 총 수량(grand_total): 54

## 저재고 목록 (총수량 < 5)
| 품목 | 총수량 |
| --- | ---: |
| cable | 1 |

판정 기준: low_stock_basis=item_total, threshold=5
