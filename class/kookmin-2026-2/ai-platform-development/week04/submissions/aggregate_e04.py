#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빛담 가을사진전(E04) 집계 스크립트 (읽기 전용)

근거 문서/조항:
- ACCOUNT-01 제1조: 기간 2026-07-01~2026-09-22, 기초잔액 학교지원금 0 / 동아리회비 800,000
- ACCOUNT-01 제2조: 수입·환불입금 +, 지출·환불지급 -, 모든 금액 양의 정수
- ACCOUNT-01 제3조: 재원별 현재 잔액, E04 순지출 = 지출 + 환불지급 - 환불입금 (수입 제외)
- ACCOUNT-01 제5조 / CLUB-01 제1조: 구매계획 '참가자'=확정인원*계수, '고정'=계수, 별도 시나리오
- CLUB-01 제1조: 물품 구매 기본 인원은 확정 인원
판단은 근거 문서를 따르고, 원본 CSV는 절대 수정하지 않는다.
"""
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

DATA = "/Users/mandahbayruuganbayr/nxt-kirocrew-hands-on/class/kookmin-2026-2/ai-platform-development/week04/data"
OUT = "/Users/mandahbayruuganbayr/nxt-kirocrew-hands-on/class/kookmin-2026-2/ai-platform-development/week04/submissions/e04_집계.json"

EVENT = "E04"
# ACCOUNT-01 제1조: 기초 잔액
OPENING_BALANCE = {"학교지원금": 0, "동아리회비": 800000}
# ACCOUNT-01 제2조: 부호
PLUS_TYPES = {"수입", "환불입금"}
MINUS_TYPES = {"지출", "환불지급"}


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    apply_rows = load(f"{DATA}/참가신청.csv")
    acct_rows = load(f"{DATA}/회계내역.csv")
    plan_rows = load(f"{DATA}/구매계획.csv")

    read_counts = {
        "참가신청": len(apply_rows),
        "회계내역": len(acct_rows),
        "구매계획": len(plan_rows),
    }

    # ---- 1) 참가 상태별 인원 (CLUB-01 제1조) ----
    status = Counter(r["신청상태"] for r in apply_rows if r["행사_ID"] == EVENT)
    confirmed = status.get("확정", 0)

    # ---- 2) 확정자의 선택 (인화체험 / 식음료) ----
    confirmed_rows = [r for r in apply_rows if r["행사_ID"] == EVENT and r["신청상태"] == "확정"]
    choice = {
        "인화체험": dict(Counter(r["인화체험"] for r in confirmed_rows)),
        "식음료": dict(Counter(r["식음료"] for r in confirmed_rows)),
    }

    # ---- 3) 회계: 재원별 현재 잔액 (ACCOUNT-01 제2·3조, 전체 E01~E04) ----
    def signed(r):
        amt = int(r["금액"])
        if r["유형"] in PLUS_TYPES:
            return amt
        if r["유형"] in MINUS_TYPES:
            return -amt
        raise ValueError(f"미분류 유형: {r['유형']} ({r['거래_ID']})")

    balance = dict(OPENING_BALANCE)
    fund_flow = defaultdict(lambda: defaultdict(int))  # 재원 -> 유형 -> 합
    for r in acct_rows:
        fund = r["재원"]
        balance[fund] = balance.get(fund, 0) + signed(r)
        fund_flow[fund][r["유형"]] += int(r["금액"])

    # ---- 4) E04 재원별 순지출 (ACCOUNT-01 제3조: 지출 + 환불지급 - 환불입금, 수입 제외) ----
    e04 = [r for r in acct_rows if r["행사_ID"] == EVENT]
    net_spend = defaultdict(int)
    e04_flow = defaultdict(lambda: defaultdict(int))
    for r in e04:
        fund = r["재원"]
        t = r["유형"]
        amt = int(r["금액"])
        e04_flow[fund][t] += amt
        if t == "지출":
            net_spend[fund] += amt
        elif t == "환불지급":
            net_spend[fund] += amt
        elif t == "환불입금":
            net_spend[fund] -= amt
        # 수입은 순지출에서 제외

    # ---- 5) 구매계획: 140/160/180명 시나리오 (ACCOUNT-01 제5조) ----
    # '참가자' 기준 = 인원 * 계수 * 단가, '고정' = 계수 * 단가 (인원 무관)
    def plan_cost(headcount):
        by_fund = defaultdict(int)
        detail = []
        total = 0
        for p in plan_rows:
            coef = int(p["계수"])
            unit = int(p["단가"])
            if p["수량기준"] == "참가자":
                qty = headcount * coef
            elif p["수량기준"] == "고정":
                qty = coef
            else:
                raise ValueError(f"미분류 수량기준: {p['수량기준']} ({p['항목_ID']})")
            cost = qty * unit
            by_fund[p["예정재원"]] += cost
            total += cost
            detail.append({
                "항목_ID": p["항목_ID"], "물품": p["물품"], "수량기준": p["수량기준"],
                "수량": qty, "단가": unit, "예정비용": cost, "예정재원": p["예정재원"],
            })
        return {"총예정비용": total, "재원별": dict(by_fund), "상세": detail}

    # 확정 인원(140)은 CLUB-01 제1조의 기본 인원. 160/180은 정원 시나리오(별도 계산).
    scenarios = {
        "140_확정인원": plan_cost(140),
        "160_승인정원": plan_cost(160),
        "180_홍보정원": plan_cost(180),
    }

    kst = timezone(timedelta(hours=9))
    result = {
        "행사_ID": EVENT,
        "생성시각_KST": datetime.now(kst).isoformat(timespec="seconds"),
        "기준일": "2026-09-22",
        "읽은_행수": read_counts,
        "참가상태별_인원": dict(status),
        "확정인원": confirmed,
        "확정자_선택": choice,
        "회계": {
            "기초잔액": OPENING_BALANCE,
            "재원별_현재잔액": dict(balance),
            "재원별_유형합계_전체": {k: dict(v) for k, v in fund_flow.items()},
            "동아리회비_현재잔액": balance.get("동아리회비"),
            "학교지원금_현재잔액": balance.get("학교지원금"),
        },
        "E04_순지출": {
            "재원별_유형합계": {k: dict(v) for k, v in e04_flow.items()},
            "재원별_순지출": dict(net_spend),
            "순지출_합계": sum(net_spend.values()),
        },
        "구매계획_시나리오": scenarios,
        "근거": {
            "참가상태": "CLUB-01 제1조 (신청상태 확정·대기·취소, 기본 인원=확정)",
            "확정자선택": "참가신청.csv 인화체험/식음료 컬럼",
            "부호": "ACCOUNT-01 제2조 (수입·환불입금 +, 지출·환불지급 -)",
            "기초잔액": "ACCOUNT-01 제1조 (학교지원금 0, 동아리회비 800,000)",
            "현재잔액": "ACCOUNT-01 제3조",
            "E04순지출": "ACCOUNT-01 제3조 (지출+환불지급-환불입금, 수입 제외)",
            "구매계획": "ACCOUNT-01 제5조 (참가자=확정인원*계수, 고정=계수), 회계에 미합산",
            "행사범위": "ACCOUNT-01 제1조 (E01~E04 혼재, 잔액은 전체·순지출은 E04만)",
        },
        "확인_필요": [
            "T095 인화비 50,000원: 용도 미기재 → RULE-01 제4조에 따라 지원 적격 여부 보류(확인 필요). 순지출 계산에는 지출로 포함됨.",
            "T097 전시패널 30,000원: 증빙 '없음' → RULE-01 제4조 확인 필요.",
            "T094 기념품 70,000원(학교지원금): RULE-01 제3조상 지원 제외 대상 → 적격성 확인 필요.",
            "160/180명 시나리오: 유효한 정원 변경 승인서 미확인(MEMO-04) → 확정 아님, 별도 계산치.",
        ],
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("읽은 행 수:", read_counts)
    print("참가상태별:", dict(status), "확정:", confirmed)
    print("확정자 선택:", choice)
    print("재원별 현재잔액:", dict(balance))
    print("E04 순지출(재원별):", dict(net_spend), "합계:", sum(net_spend.values()))
    for name, sc in scenarios.items():
        print(f"구매계획 {name}: 총 {sc['총예정비용']:,}원 재원별 {sc['재원별']}")
    print("저장:", OUT)


if __name__ == "__main__":
    main()
