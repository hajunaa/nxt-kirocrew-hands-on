---
name: data-to-html
description: 여러 MD 문서와 CSV를 읽어, 문서 요약과 CSV 핵심 표를 담은 단일 HTML 리포트로 만든다
triggers: 문서 요약 리포트, MD CSV HTML, 문서 요약 HTML, 리포트 생성
---

# 문서·데이터 HTML 리포트

여러 MD 문서와 하나 이상의 CSV를 입력으로 받아, 아래 두 가지를 담은
**단일 HTML 파일** 하나로 정리한다.

1. 각 MD 문서의 요약
2. 각 CSV의 핵심 표

## 역할 분담

`memo-to-json` 스킬과 같은 원칙을 따른다. **판단은 AI, 검증·생성은 Python.**

- **AI 담당(판단):**
  - 각 MD 문서를 읽고 요약을 만든다.
  - 각 CSV에서 어떤 컬럼·행이 "핵심"인지 판단해 골라낸다.
  - 결과를 아래 고정 스키마의 JSON으로 만든다.
- **Python 담당(검증·생성):**
  - AI가 만든 JSON의 구조를 검사한다.
  - 통과하면 HTML 리포트 파일을 생성한다. 판단·요약은 하지 않는다.

## 중간 산출물: 리포트 JSON (고정 스키마)

AI는 먼저 아래 구조의 JSON을 만든다. 이 JSON이 Python 검사기와 생성기의 입력이다.

```json
{
  "title": "리포트 제목",
  "generated_at": "2026-09-23",
  "documents": [
    {
      "source": "설계.md",
      "summary": ["요약 문장 1", "요약 문장 2"]
    }
  ],
  "tables": [
    {
      "source": "매출.csv",
      "caption": "이 표가 무엇인지 한 줄 설명",
      "columns": ["열 이름1", "열 이름2"],
      "rows": [
        ["값1", "값2"],
        ["값3", "값4"]
      ]
    }
  ]
}
```

| 항목 | 자료형 |
|---|---|
| `title` | 문자열 |
| `generated_at` | `"YYYY-MM-DD"` 문자열 |
| `documents` | 객체 목록 (비면 `[]`) |
| `documents[].source` | 문자열 (원본 MD 파일명) |
| `documents[].summary` | 문자열 목록 (한 문장 = 한 원소) |
| `tables` | 객체 목록 (비면 `[]`) |
| `tables[].source` | 문자열 (원본 CSV 파일명) |
| `tables[].caption` | 문자열 |
| `tables[].columns` | 문자열 목록 |
| `tables[].rows` | 목록의 목록. 각 행의 길이는 `columns` 길이와 같아야 한다 |

- `documents`와 `tables`가 둘 다 비면 안 된다(최소 하나는 있어야 리포트가 성립).
- 행의 셀 값은 문자열로 넣는다(숫자도 문자열로).

## 실행 절차

1. AI가 입력 MD들과 CSV들을 읽고, 위 스키마대로 리포트 JSON을 만든다.
   - MD: 문서마다 핵심을 몇 문장으로 요약(`summary`).
   - CSV: 원본을 그대로 옮기지 말고, 핵심 컬럼·행만 골라 `columns`/`rows`에 담는다.
     무엇을 왜 골랐는지는 `caption` 한 줄로 남긴다.
   - 읽기 애매하거나 근거가 불확실한 내용은 지어내지 말고, 해당 요약 문장에
     `(확인 필요)`를 붙여 그대로 표시한다.
2. 그 JSON을 `scripts/build_report.py`에 넘겨 **구조를 검사**한다.
   Python은 요약·판단을 하지 않고 **검사와 생성만** 한다.
3. 검사 통과 시 HTML 리포트를 생성한다. 실패 시 생성하지 않고,
   어떤 항목이 왜 잘못됐는지 알린다.

```bash
cd "$(dirname "$0")/scripts" 2>/dev/null || cd scripts

# 검사만 (통과하면 정규화된 JSON을 stdout으로 출력, HTML은 만들지 않음)
cat report.json | python3 build_report.py --check-only

# 검사 후 통과하면 HTML 파일로 저장
python3 build_report.py --in report.json --out 리포트.html
```

- 종료 코드 `0` = 검사 통과(생성), `1` = 검사 실패(생성 안 함, 이유는 stderr).
- 검사기가 거부하는 경우: 항목 누락, 허용되지 않은 항목 추가, 자료형 오류
  (문자열 아님·목록 아님·목록 원소 자료형 오류), `generated_at`가 YYYY-MM-DD 아님
  또는 달력에 없는 날짜, 어떤 행의 길이가 `columns` 길이와 다름,
  `documents`와 `tables`가 둘 다 비어 있음, JSON 파싱 실패.
- 거부되면 HTML 파일은 만들어지지 않는다. 메시지를 보고 JSON을 고쳐 다시 넘긴다.

## HTML 출력 형태

- 자립형 단일 HTML(외부 CSS/JS 링크 없음, 스타일은 문서 안에 인라인).
- 상단에 제목과 생성일, 이어서 "문서 요약" 절(문서별 소제목 + 요약 목록),
  마지막에 "핵심 표" 절(표별 caption + `<table>`).
- 표의 값은 이스케이프해서 넣는다(HTML 인젝션 방지).
