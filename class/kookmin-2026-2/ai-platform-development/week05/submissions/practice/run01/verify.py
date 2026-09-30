#!/usr/bin/env python3
"""최종 검증: 원본 재파싱 → result.json / 중간파일 / report.md 대조."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
DATA = BASE / "practice" / "data"
RUN = Path(__file__).resolve().parent

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)

def parse_md(path):
    """출력형식.md 파싱 규칙대로 | 품목 | 수량 | 표를 (품목, 수량) 리스트로."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        item, qty = cells
        if item in ("품목", "품목명") or set(qty) <= set("- "):
            continue
        if item == "" or "---" in item:
            continue
        try:
            rows.append((item, int(qty)))
        except ValueError:
            continue
    return rows

# 1) 원본 재파싱 (ground truth)
gt = {}
for wh in ("A", "B", "C"):
    gt[wh] = parse_md(DATA / f"warehouse-{wh.lower()}.md")

gt_totals = {wh: sum(q for _, q in rows) for wh, rows in gt.items()}
gt_items = {}
for wh, rows in gt.items():
    d = {}
    for item, q in rows:
        d[item] = d.get(item, 0) + q
    gt_items[wh] = d

gt_item_totals = {}
for wh in ("A", "B", "C"):
    for item, q in gt_items[wh].items():
        gt_item_totals[item] = gt_item_totals.get(item, 0) + q

gt_low = []
for wh in ("A", "B", "C"):
    for item, q in gt[wh]:  # 원본 행 순서 유지
        if q < 5:
            gt_low.append({"warehouse": wh, "item": item, "quantity": q})

# 2) result.json 로드 및 스키마 검증
result = json.loads((RUN / "result.json").read_text(encoding="utf-8"))

required_top = {"warehouses", "item_totals", "low_stock", "low_stock_basis"}
check(set(result.keys()) == required_top,
      f"result.json 최상위 키 불일치: {sorted(result.keys())} != {sorted(required_top)}")
check(set(result["warehouses"].keys()) == {"A", "B", "C"},
      f"warehouses 키 불일치: {sorted(result['warehouses'].keys())}")
for wh in ("A", "B", "C"):
    node = result["warehouses"][wh]
    check(set(node.keys()) == {"total", "items"},
          f"warehouses.{wh} 키 불일치: {sorted(node.keys())}")
    check(isinstance(node["total"], int), f"warehouses.{wh}.total 정수 아님")
    check(isinstance(node["items"], dict), f"warehouses.{wh}.items 객체 아님")
check(result["low_stock_basis"] == "warehouse_row",
      f"low_stock_basis 불일치: {result['low_stock_basis']!r}")
for i, e in enumerate(result["low_stock"]):
    check(set(e.keys()) == {"warehouse", "item", "quantity"},
          f"low_stock[{i}] 키 불일치: {sorted(e.keys())}")

# 3) result.json vs ground truth
for wh in ("A", "B", "C"):
    check(result["warehouses"][wh]["total"] == gt_totals[wh],
          f"창고 {wh} 합계 불일치: result={result['warehouses'][wh]['total']} gt={gt_totals[wh]}")
    check(result["warehouses"][wh]["items"] == gt_items[wh],
          f"창고 {wh} 품목별 수량 불일치")
check(result["item_totals"] == gt_item_totals,
      f"item_totals 불일치: result={result['item_totals']} gt={gt_item_totals}")
check(result["low_stock"] == gt_low,
      f"low_stock 불일치:\n result={result['low_stock']}\n gt={gt_low}")
# 저재고 항목 모두 수량<5 인지
for e in result["low_stock"]:
    check(e["quantity"] < 5, f"저재고 항목 수량>=5: {e}")
# 저재고 정렬 A→B→C
order = {"A": 0, "B": 1, "C": 2}
seq = [order[e["warehouse"]] for e in result["low_stock"]]
check(seq == sorted(seq), f"저재고 창고 순서(A→B→C) 위반: {[e['warehouse'] for e in result['low_stock']]}")

# 4) 중간 파일 합과 대조
inter = {}
for wh in ("A", "B", "C"):
    inter[wh] = json.loads((RUN / f"intermediate_{wh.lower()}.json").read_text(encoding="utf-8"))
# 중간파일 구조는 유연하게 total/items/low_stock 를 찾음
def find_key(d, *names):
    for n in names:
        if n in d:
            return d[n]
    return None
for wh in ("A", "B", "C"):
    it = inter[wh]
    itotal = find_key(it, "total")
    iitems = find_key(it, "items")
    ilow = find_key(it, "low_stock", "low")
    if itotal is not None:
        check(itotal == gt_totals[wh], f"중간 {wh} total 불일치: {itotal} != {gt_totals[wh]}")
    if iitems is not None:
        check(iitems == gt_items[wh], f"중간 {wh} items 불일치")
    if ilow is not None:
        low_qs = [x.get("quantity") for x in ilow]
        check(all(q < 5 for q in low_qs), f"중간 {wh} low_stock 에 수량>=5 존재")

# item_totals 가 중간파일 items 합과 일치
sum_from_inter = {}
for wh in ("A", "B", "C"):
    iitems = find_key(inter[wh], "items") or {}
    for item, q in iitems.items():
        sum_from_inter[item] = sum_from_inter.get(item, 0) + q
if sum_from_inter:
    check(sum_from_inter == result["item_totals"],
          f"중간파일 items 합 != result.item_totals\n {sum_from_inter}\n {result['item_totals']}")

# 5) report.md 수치 대조
report = (RUN / "report.md").read_text(encoding="utf-8")
check("`warehouse_row`" in report or "warehouse_row" in report, "report.md 에 low_stock_basis 표기 없음")
for wh in ("A", "B", "C"):
    check(re.search(rf"\|\s*{wh}\s*\|\s*{gt_totals[wh]}\s*\|", report) is not None,
          f"report.md 창고별 합계 표에 {wh}={gt_totals[wh]} 없음")
for item, q in gt_item_totals.items():
    check(re.search(rf"\|\s*{re.escape(item)}\s*\|\s*{q}\s*\|", report) is not None,
          f"report.md 총수량 표에 {item}={q} 없음")
for e in gt_low:
    check(re.search(rf"\|\s*{e['warehouse']}\s*\|\s*{re.escape(e['item'])}\s*\|\s*{e['quantity']}\s*\|", report) is not None,
          f"report.md 저재고 표에 {e['warehouse']}/{e['item']}/{e['quantity']} 없음")

# 결과 출력
print("=== Ground truth (원본 재파싱) ===")
print("창고별 합계:", gt_totals, "| 전체:", sum(gt_totals.values()))
print("품목별 총수량:", gt_item_totals)
print("저재고 수:", len(gt_low), gt_low)
print()
if errors:
    print(f"❌ 검증 실패 — {len(errors)}건")
    for e in errors:
        print("  -", e)
    sys.exit(1)
else:
    print("✅ 검증 통과: result.json 스키마·수치, 중간파일 합, report.md 모두 일치")
    sys.exit(0)
