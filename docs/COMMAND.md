# 검증 명령어 모음 (COMMAND.md)

[ANSWER.md](ANSWER.md)의 각 항목을 **직접 쳐서 확인하는 명령어 목록**입니다.
위에서부터 순서대로 실행하면 됩니다 — 뒤 명령이 앞 명령이 만든 데이터를 씁니다.

아래 출력은 전부 **실제로 실행해서 받은 것**입니다. 붙여넣고 그대로 나오는지
비교하시면 됩니다.

코드블록 표기는 두 가지입니다.

| 표기 | 뜻 |
| --- | --- |
| ```` ```bash ```` | **그대로 붙여넣어 실행하는 명령어** |
| ```` ``` ```` (언어 없음) | 그 명령의 **기대 출력** |

> 전부 한 번에 자동으로 돌리려면 [`../verification.sh`](../verification.sh)를 쓰세요.
> 이 문서는 **한 줄씩 눈으로 확인**하기 위한 것입니다.

---

## 목차

- [항목 1 — 기능 동작](#항목-1--기능-동작)
  - [1-1. add/list/search/summary/export/import/update/delete가 요구사항대로 동작하는가?](#1-1-addlistsearchsummaryexportimportupdatedelete가-요구사항대로-동작하는가)
  - [1-2. 재실행 후에도 데이터가 유지되는가? (저장 파일 3개 이상)](#1-2-재실행-후에도-데이터가-유지되는가-저장-파일-3개-이상)
  - [1-3. category add/list/remove가 정상 동작하는가? (사용 중 카테고리 처리 포함)](#1-3-category-addlistremove가-정상-동작하는가-사용-중-카테고리-처리-포함)
  - [1-4. budget set이 저장되며, summary에서 사용률/초과 여부가 출력되는가?](#1-4-budget-set이-저장되며-summary에서-사용률초과-여부가-출력되는가)
  - [1-5. import/export가 명시된 CSV 스키마로 동작하는가?](#1-5-importexport가-명시된-csv-스키마로-동작하는가)
  - [1-6. 잘못된 입력/파일 오류에서 스택트레이스 없이 오류 메시지와 힌트를 출력하는가?](#1-6-잘못된-입력파일-오류에서-스택트레이스-없이-오류-메시지와-힌트를-출력하는가)
  - [1-7. 오류 상황에서 종료 코드가 0이 아닌가?](#1-7-오류-상황에서-종료-코드가-0이-아닌가)
- [항목 2 — 구조와 책임](#항목-2--구조와-책임)
  - [2-3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?](#2-3-파일-기반-updatedelete를-어떻게-안전하게-처리했는가)
- [항목 3 — 제너레이터 / 데코레이터 / 타입 힌트](#항목-3--제너레이터--데코레이터--타입-힌트)
  - [3-1. list/search를 제너레이터로 스트리밍 처리한 방식과, 왜 유리한가?](#3-1-listsearch를-제너레이터로-스트리밍-처리한-방식과-왜-유리한가)
  - [3-2. 데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했는가?](#3-2-데코레이터로-분리한-공통-기능이-무엇이며-왜-분리가-필요했는가)
  - [3-3. 타입 힌트의 이점을 실제 코드 예로 어떻게 확인했고, 왜 도움이 되는가?](#3-3-타입-힌트의-이점을-실제-코드-예로-어떻게-확인했고-왜-도움이-되는가)
- [항목 4 — 설계 근거](#항목-4--설계-근거)
  - [4-2. 거래가 10만 건이면 병목은 어디이고 어떻게 개선할 것인가?](#4-2-거래가-10만-건이면-병목은-어디이고-어떻게-개선할-것인가)
  - [4-3. import CSV에 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지키는가?](#4-3-import-csv에-깨진-행이-섞이면-어떻게-처리해-사용자-신뢰를-지키는가)
- [항목 5 — 보너스](#항목-5--보너스)

---

## 검증 준비

작업용 폴더를 하나 정하고 시작합니다. `./data`를 건드리지 않기 위해서입니다.

```bash
cd <프로젝트 루트>              # python -m budget_app 은 루트에서만 동작합니다
export D=/tmp/pw-verify
rm -rf $D                      # 매번 깨끗한 상태에서 시작
```

끝나고 정리:

```bash
rm -rf /tmp/pw-*
```

**전부 한 번에 자동으로 돌리려면** 저장소 루트의 스크립트를 쓰세요. 아래 명령어를
모두 담아 83개 항목을 검사하고, 실패가 있으면 종료 코드 1로 끝납니다.

```bash
./verification.sh            # 기능 검증 (약 3초)
./verification.sh --bench    # 10만 건 성능 측정 포함
```

---

## 항목 1 — 기능 동작

### 1-1. add/list/search/summary/export/import/update/delete가 요구사항대로 동작하는가?

```bash
python3.12 -m budget_app --help                       # 10개 명령 등록 확인
python3.12 -m budget_app --version                    # budget_app 0.1.0
python3.12 -m budget_app list --help                  # 각 명령의 옵션은 뒤에 --help
```

**① add** — 대화형. 프롬프트가 6번 뜹니다.

```bash
python3.12 -m budget_app --data-dir $D add
```

```
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15,000                ← 쉼표를 넣어도 됩니다
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): 회사
[저장 완료] id=TX-000001
```

손으로 치기 번거로우면 파이프로 밀어 넣습니다. 아래 4건이 이후 검증의 기준 데이터입니다.

```bash
printf '2024-01-15\nexpense\nfood\n15,000\n점심\n회사\n'          | python3.12 -m budget_app --data-dir $D add
printf '2024-01-20\nexpense\nfood\n30000\n저녁 외식\nmeal,work\n' | python3.12 -m budget_app --data-dir $D add
printf '2024-01-25\nincome\nsalary\n3000000\n월급\n\n'            | python3.12 -m budget_app --data-dir $D add
printf '2024-01-01\nexpense\nrent\n150000\n월세\nfixed\n'         | python3.12 -m budget_app --data-dir $D add
```

**② list**

```bash
python3.12 -m budget_app --data-dir $D list
python3.12 -m budget_app --data-dir $D list --limit 2
```

```
TX-000004 | 2024-01-01 | expense | rent | 150000 | 월세
TX-000003 | 2024-01-25 | income  | salary | 3000000 | 월급
TX-000002 | 2024-01-20 | expense | food | 30000 | 저녁 외식
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심
```

`15,000`이 `15000`으로 정규화된 것, `income` 뒤에 공백 1칸이 붙어 `expense`와 칸이
맞는 것, 그리고 날짜가 가장 이른 `TX-000004`가 맨 위인 것(**입력 순서의 역순**)을
함께 확인하세요.

**③ search** — 조건 6가지

```bash
python3.12 -m budget_app --data-dir $D search --category food
python3.12 -m budget_app --data-dir $D search --type income
python3.12 -m budget_app --data-dir $D search --from 2024-01-15 --to 2024-01-20
python3.12 -m budget_app --data-dir $D search --q 저녁
python3.12 -m budget_app --data-dir $D search --tag fixed
python3.12 -m budget_app --data-dir $D search --category food --type expense --limit 1
python3.12 -m budget_app --data-dir $D search --q 없는키워드
```

```
# --type income
TX-000003 | 2024-01-25 | income  | salary | 3000000 | 월급

# --q 저녁 (메모 부분 일치)
TX-000002 | 2024-01-20 | expense | food | 30000 | 저녁 외식

# --tag fixed
TX-000004 | 2024-01-01 | expense | rent | 150000 | 월세

# --q 없는키워드
[안내] 조건에 맞는 거래가 없습니다.
```

안내가 stderr로 나가는지도 같이 봅니다. 0바이트여야 정상입니다.

```bash
python3.12 -m budget_app --data-dir $D search --q 없는키워드 > /tmp/pw-o.txt
wc -c /tmp/pw-o.txt
```

**④ update**

```bash
python3.12 -m budget_app --data-dir $D update --id TX-000001 --amount 18,000 --memo "점심 (수정)"
python3.12 -m budget_app --data-dir $D update --id TX-000001 --category etc --tags "meal,fix"
python3.12 -m budget_app --data-dir $D update --id TX-999999 --amount 100
python3.12 -m budget_app --data-dir $D update --id TX-000001
```

```
[수정 완료] id=TX-000001
TX-000001 | 2024-01-15 | expense | food | 18000 | 점심 (수정)

[수정 완료] id=TX-000001
TX-000001 | 2024-01-15 | expense | etc | 18000 | 점심 (수정)

[오류] id=TX-999999 거래를 찾을 수 없습니다.
[힌트] list 명령으로 존재하는 id를 확인해 보세요.

[오류] 수정할 항목을 하나 이상 지정해야 합니다.
[힌트] 예: update --id TX-000012 --amount 20000
```

**⑤ delete**

```bash
python3.12 -m budget_app --data-dir $D delete --id TX-000004
python3.12 -m budget_app --data-dir $D list
```

```
[삭제 완료] id=TX-000004

TX-000003 | 2024-01-25 | income  | salary | 3000000 | 월급
TX-000002 | 2024-01-20 | expense | etc | 30000 | 저녁 외식
TX-000001 | 2024-01-15 | expense | etc | 18000 | 점심 (수정)
```

**⑥~⑩ budget / category / summary / export / import** 은 아래 각 항목에서 다룹니다.

---

### 1-2. 재실행 후에도 데이터가 유지되는가? (저장 파일 3개 이상)

```bash
ls $D
```

```
categories.jsonl   transactions.jsonl
```

> 아직 `budgets.jsonl`이 없습니다. **파일은 쓸 때 생깁니다.** 예산을 한 번도 설정하지
> 않았으므로 만들지 않은 것이 정상입니다. 아래 1-4에서 `budget set`을 하면 3개가 됩니다.

```bash
cat $D/transactions.jsonl
cat $D/categories.jsonl
```

```
{"id": "TX-000001", "date": "2024-01-15", "type": "expense", "category": "etc", "amount": 18000, "memo": "점심 (수정)", "tags": ["meal", "fix"]}
{"id": "TX-000002", "date": "2024-01-20", "type": "expense", "category": "etc", "amount": 30000, "memo": "저녁 외식", "tags": ["meal", "work"]}
{"id": "TX-000003", "date": "2024-01-25", "type": "income", "category": "salary", "amount": 3000000, "memo": "월급", "tags": []}
```

`python -m budget_app`은 **명령 하나마다 프로세스가 새로 뜨고 죽습니다.** 위에서 친
모든 명령이 이미 별개의 프로세스였으므로, 아래 세 줄이 그대로 지속성의 증거입니다.

```bash
python3.12 -m budget_app --data-dir $D list
python3.12 -m budget_app --data-dir $D category list
python3.12 -m budget_app --data-dir $D budget show
```

---

### 1-3. category add/list/remove가 정상 동작하는가? (사용 중 카테고리 처리 포함)

```bash
python3.12 -m budget_app --data-dir $D category list
```

```
- food
- transport
- rent
- salary
- etc
```

> 등록한 적이 없는데 5개가 있습니다. **빈 카테고리 파일은 기본값을 자동으로 채웁니다.**
> 그러지 않으면 첫 `add`가 "등록된 카테고리가 없습니다"로 막힙니다.

```bash
python3.12 -m budget_app --data-dir $D category add 경조사비
python3.12 -m budget_app --data-dir $D category add food
python3.12 -m budget_app --data-dir $D category add FOOD
```

```
[저장 완료] category=경조사비

[오류] 이미 있는 카테고리입니다: food
[힌트] category list로 현재 목록을 확인하세요.

[오류] 이미 있는 카테고리입니다: food      ← 대소문자만 달라도 중복
[힌트] category list로 현재 목록을 확인하세요.
```

```bash
python3.12 -m budget_app --data-dir $D category remove 경조사비      # 안 쓰는 것: 그냥 삭제
python3.12 -m budget_app --data-dir $D category remove food          # 쓰는 중: 차단
python3.12 -m budget_app --data-dir $D category remove food --replace-with etc
python3.12 -m budget_app --data-dir $D list
python3.12 -m budget_app --data-dir $D category add food             # 원상 복구
```

```
[삭제 완료] category=경조사비

[오류] 'food' 카테고리를 사용하는 거래가 1건 있습니다.
[힌트] --replace-with <다른카테고리> 로 대체 카테고리를 지정하세요.

[삭제 완료] category=food (거래 1건을 etc로 옮겼습니다)

TX-000003 | 2024-01-25 | income  | salary | 3000000 | 월급
TX-000002 | 2024-01-20 | expense | etc | 30000 | 저녁 외식      ← food 였던 것이 etc 로
TX-000001 | 2024-01-15 | expense | etc | 18000 | 점심 (수정)
```

---

### 1-4. budget set이 저장되며, summary에서 사용률/초과 여부가 출력되는가?

```bash
python3.12 -m budget_app --data-dir $D budget set --month 2024-01 --amount 500000
python3.12 -m budget_app --data-dir $D budget show
ls $D                                                    # 이제 budgets.jsonl 이 생겼습니다
python3.12 -m budget_app --data-dir $D summary --month 2024-01 --top 3
```

```
[저장 완료] 2024-01 예산 500000원

- 2024-01: 500000원

budgets.jsonl   categories.jsonl   transactions.jsonl

총 수입: 3000000원
총 지출: 48000원
잔액: 2952000원
예산: 500000원 (사용률 9.6%)

지출 TOP 1
1) etc 48000원
```

예산 초과:

```bash
python3.12 -m budget_app --data-dir $D budget set --month 2024-01 --amount 10000
python3.12 -m budget_app --data-dir $D summary --month 2024-01
```

```
예산: 10000원 (사용률 480.0%)
[경고] 예산을 38000원 초과했습니다.
```

같은 달을 다시 설정하면 줄이 늘지 않고 교체되는지:

```bash
python3.12 -m budget_app --data-dir $D budget set --month 2024-01 --amount 500000
cat $D/budgets.jsonl
```

```
{"month": "2024-01", "amount": 500000}      ← 한 줄만 있어야 정상
```

거래가 없는 달, 그리고 자릿수를 덜 맞춘 월 입력:

```bash
python3.12 -m budget_app --data-dir $D summary --month 2024-09
python3.12 -m budget_app --data-dir $D summary --month 2024-1
```

```
2024-09 데이터 없음

총 수입: 3000000원        ← 2024-1 이 2024-01 로 정규화되어 정상 집계됩니다
```

---

### 1-5. import/export가 명시된 CSV 스키마로 동작하는가?

```bash
python3.12 -m budget_app --data-dir $D export --out /tmp/pw-out.csv --month 2024-01
cat /tmp/pw-out.csv
python3.12 -m budget_app --data-dir $D export --out /tmp/pw-food.csv --from 2024-01-01 --to 2024-01-20
```

```
[완료] /tmp/pw-out.csv (3 records)

date,type,category,amount,memo,tags
2024-01-25,income,salary,3000000,월급,
2024-01-20,expense,etc,30000,저녁 외식,"meal,work"
2024-01-15,expense,etc,18000,점심 (수정),"meal,fix"
```

조건 없는 export 는 거부하고, 파일을 만들지도 않습니다.

```bash
python3.12 -m budget_app --data-dir $D export --out /tmp/pw-x.csv
ls /tmp/pw-x.csv
```

```
[오류] --month 또는 --from/--to 중 하나 이상을 지정해야 합니다.
[힌트] 예: export --out out.csv --month 2024-01

ls: /tmp/pw-x.csv: No such file or directory
```

형식 확인 (BOM 없음 / CRLF):

```bash
head -c 3 /tmp/pw-out.csv | xxd            # 'dat' — efbbbf(BOM) 이 없어야 함
tail -1 /tmp/pw-out.csv | xxd | tail -1    # 줄 끝이 0d0a (CRLF) — RFC 4180
file /tmp/pw-out.csv                       # UTF-8 text
```

**왕복 시험** — 쉼표와 큰따옴표가 든 값:

```bash
printf 'date,type,category,amount,memo,tags\n2024-02-01,expense,food,15000,"점심, 김치찌개 ""특""","meal,work"\n' > /tmp/pw-tricky.csv

rm -rf /tmp/pw-t1
python3.12 -m budget_app --data-dir /tmp/pw-t1 import --from /tmp/pw-tricky.csv
cat /tmp/pw-t1/transactions.jsonl
python3.12 -m budget_app --data-dir /tmp/pw-t1 export --out /tmp/pw-tricky2.csv --month 2024-02
diff <(tail -1 /tmp/pw-tricky.csv) <(tail -1 /tmp/pw-tricky2.csv | tr -d '\r') && echo "왕복 후에도 동일"
```

```
[완료] imported=1, skipped=0
{"id": "TX-000001", ..., "memo": "점심, 김치찌개 \"특\"", "tags": ["meal", "work"]}
[완료] /tmp/pw-tricky2.csv (1 records)
왕복 후에도 동일
```

> `tr -d '\r'` 이 필요한 이유: 우리가 만든 원본은 LF로 끝나는데 `export`는 RFC 4180대로
> **CRLF**로 씁니다. 내용은 같고 줄바꿈 표기만 다릅니다.

---

### 1-6. 잘못된 입력/파일 오류에서 스택트레이스 없이 오류 메시지와 힌트를 출력하는가?

```bash
python3.12 -m budget_app --data-dir $D delete --id TX-999999
python3.12 -m budget_app --data-dir $D import --from /없는파일.csv
python3.12 -m budget_app --data-dir $D budget set --month 2024-01 --amount -500
python3.12 -m budget_app --data-dir "" list
```

```
[오류] id=TX-999999 거래를 찾을 수 없습니다.
[힌트] list 명령으로 존재하는 id를 확인해 보세요.

[오류] CSV 파일이 없습니다: /없는파일.csv
[힌트] --from 경로를 확인하세요.

[오류] 금액은 0보다 큰 정수여야 합니다.
[힌트] 입력값: -500

[오류] --data-dir 경로가 비어 있습니다.
[힌트] 예: --data-dir ./data
```

**어디에도 `Traceback` 이 없어야 합니다.**

잘못된 입력은 되물어서 복구합니다.

```bash
python3.12 -m budget_app --data-dir $D add
```

```
날짜(YYYY-MM-DD): 2024-13-99
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
날짜(YYYY-MM-DD): 2024-02-30              ← 달력에 없는 날짜도 걸립니다
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
날짜(YYYY-MM-DD): 2024-01-05
타입(income/expense): expense
카테고리: etc
금액(양수): 0
[오류] 금액은 0보다 큰 정수여야 합니다.
[힌트] 입력값: 0
금액(양수): 1000
메모(선택):
태그(쉼표로 구분, 없으면 엔터):
[저장 완료] id=TX-000004
```

> 새 id가 **TX-000004**입니다. 앞서 `TX-000004`를 지웠기 때문에 그 번호를 재사용합니다 —
> 의도한 동작입니다(plan.md 0절).

저장 파일 한 줄이 깨졌을 때:

```bash
cp $D/transactions.jsonl /tmp/pw-bk.jsonl
printf '이건 JSON이 아님\n' >> $D/transactions.jsonl
python3.12 -m budget_app --data-dir $D list
cp /tmp/pw-bk.jsonl $D/transactions.jsonl        # 원상 복구
```

```
[경고] transactions.jsonl 한 줄이 JSON 형식이 아닙니다 - 건너뜁니다
TX-000004 | 2024-01-05 | expense | etc | 1000 |
TX-000003 | 2024-01-25 | income  | salary | 3000000 | 월급
TX-000002 | 2024-01-20 | expense | etc | 30000 | 저녁 외식
TX-000001 | 2024-01-15 | expense | etc | 18000 | 점심 (수정)
```

예상하지 못한 오류(우리 쪽 버그)도 감추는지, 그리고 `--verbose`로는 열리는지:

```bash
mkdir -p /tmp/pw-broken && printf '123\n' > /tmp/pw-broken/transactions.jsonl
python3.12 -m budget_app --data-dir /tmp/pw-broken list
python3.12 -m budget_app --data-dir /tmp/pw-broken --verbose list
```

```
# --verbose 없이
[오류] 예상하지 못한 오류가 발생했습니다: 'int' object has no attribute 'get'
[힌트] --verbose 로 다시 실행하면 자세한 내용을 볼 수 있습니다.

# --verbose 를 주면 (개발자용)
  File ".../budget_app/models.py", line 61, in from_dict
    tags = raw.get("tags") or ()
AttributeError: 'int' object has no attribute 'get'
```

`[오류]` 문구를 만드는 코드가 한 군데인지:

```bash
grep -rn 'print(f"\[오류\]' budget_app/*.py
```

```
budget_app/decorators.py:25:    print(f"[오류] {exc.message}", file=sys.stderr)
```

---

### 1-7. 오류 상황에서 종료 코드가 0이 아닌가?

```bash
python3.12 -m budget_app --data-dir $D category list         >/dev/null 2>&1; echo "exit=$?"   # 0
python3.12 -m budget_app --data-dir $D delete --id TX-999999 >/dev/null 2>&1; echo "exit=$?"   # 1
python3.12 -m budget_app --data-dir $D category add food     >/dev/null 2>&1; echo "exit=$?"   # 1
python3.12 -m budget_app --data-dir $D import --from /nope.csv >/dev/null 2>&1; echo "exit=$?" # 2
python3.12 -m budget_app --data-dir $D search --type bad     >/dev/null 2>&1; echo "exit=$?"   # 2
python3.12 -m budget_app --data-dir ""  list                 >/dev/null 2>&1; echo "exit=$?"   # 2
```

Ctrl+C는 대화형에서 직접 눌러 확인합니다.

```bash
python3.12 -m budget_app --data-dir $D add     # 프롬프트에서 Ctrl+C
echo "exit=$?"                                 # 130
```

---

## 항목 2 — 구조와 책임

### 2-3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?

실패한 명령이 저장 파일을 조금도 건드리지 않는지 md5로 봅니다.

```bash
md5 -q $D/transactions.jsonl                              # macOS (리눅스는 md5sum)
python3.12 -m budget_app --data-dir $D delete --id TX-999999
md5 -q $D/transactions.jsonl
```

```
8f5b73e8e1eb487529e81982159caa3f
[오류] id=TX-999999 거래를 찾을 수 없습니다.
[힌트] list 명령으로 존재하는 id를 확인해 보세요.
8f5b73e8e1eb487529e81982159caa3f      ← 위와 완전히 동일
```

해시값 자체는 데이터에 따라 달라집니다. **앞뒤 두 값이 같은지**만 보면 됩니다.

성공한 수정 후 임시 파일이 남지 않았는지:

```bash
python3.12 -m budget_app --data-dir $D update --id TX-000001 --memo "원자성 확인"
ls -a $D
```

```
.  ..  budgets.jsonl  categories.jsonl  transactions.jsonl      ← tmp* 잔여 없음
```

구현 지점:

```bash
grep -n 'NamedTemporaryFile\|os.fsync\|os.replace' budget_app/repositories.py
```

> 쓰기 **도중에** 강제로 죽이는 시험은 CLI만으로는 어렵습니다.
> [`../verification.sh`](../verification.sh)의 `항목 2-3` 블록이 쓰기 중간에 예외를
> 던져 md5가 그대로인지까지 자동으로 확인합니다.

---

## 항목 3 — 제너레이터 / 데코레이터 / 타입 힌트

### 3-1. list/search를 제너레이터로 스트리밍 처리한 방식과, 왜 유리한가?

1만 건을 만들어 재 봅니다.

```bash
rm -rf /tmp/pw-big
(echo "date,type,category,amount,memo,tags"
 seq 1 10000 | awk '{printf "2024-%02d-%02d,expense,food,%d,점심 %d,meal\n", ($1%12)+1, ($1%28)+1, $1, $1}'
) > /tmp/pw-big.csv

time python3.12 -m budget_app --data-dir /tmp/pw-big import --from /tmp/pw-big.csv
ls -lh /tmp/pw-big/transactions.jsonl
```

```
[완료] imported=10000, skipped=0
        1.071 total

-rw-r--r--  1.3M  transactions.jsonl
```

뒤에서부터 읽는 명령 (빠른 쪽):

```bash
time python3.12 -m budget_app --data-dir /tmp/pw-big list --limit 3
time python3.12 -m budget_app --data-dir /tmp/pw-big search --tag meal --limit 3
```

```
TX-010000 | 2024-05-05 | expense | food | 10000 | 점심 10000
TX-009999 | 2024-04-04 | expense | food | 9999 | 점심 9999
TX-009998 | 2024-03-03 | expense | food | 9998 | 점심 9998
        0.048 total          ← 1.3MB 파일인데 파이썬 기동 시간 수준

        0.050 total
```

전량 스캔이 필요한 명령 (느린 쪽):

```bash
time python3.12 -m budget_app --data-dir /tmp/pw-big search --q 없는키워드
time python3.12 -m budget_app --data-dir /tmp/pw-big summary --month 2024-01
time python3.12 -m budget_app --data-dir /tmp/pw-big delete --id TX-000001
```

```
        0.081 total          ← 매칭이 없으면 파일 전체를 읽습니다
        0.084 total
        0.115 total          ← 전량 읽기 + 전량 재작성이라 가장 무겁습니다
```

**`list`(0.048초)와 `delete`(0.115초)의 차이가 스트리밍의 이득**입니다.
읽은 바이트까지 세는 정밀 측정은 스크립트로 합니다.

```bash
./verification.sh | grep -A6 '항목 3-1'
```

```
INFO  파일 크기 (10,000건)          1377788 bytes
INFO  list --limit 3 이 읽은 양     65536 bytes (4.8%)
INFO  next_id() 가 읽은 양          65536 bytes (4.8%)
```

---

### 3-2. 데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했는가?

```bash
grep -c '@handle_errors' budget_app/cli.py            # 핸들러 수만큼
grep -n 'def handle_errors' budget_app/decorators.py

python3.12 -c "
from budget_app import cli
print('핸들러 수:', len(cli.HANDLERS))
print('데코레이터 미적용:', [n for n,f in cli.HANDLERS.items() if not hasattr(f,'__wrapped__')])
print('이름 보존:', cli.HANDLERS['list'].__name__)
"
```

```
핸들러 수: 10
데코레이터 미적용: []
이름 보존: handle_list
```

---

### 3-3. 타입 힌트의 이점을 실제 코드 예로 어떻게 확인했고, 왜 도움이 되는가?

```bash
grep -n 'yield' budget_app/repositories.py       # 제너레이터 지점
grep -n 'Iterator' budget_app/services.py        # 반환 타입으로 스트리밍을 못박은 곳

python3.12 -c "
import inspect
from budget_app import services, repositories
for f in (repositories.read_jsonl, repositories.read_jsonl_reversed,
          services.search_transactions, services.recent_transactions):
    print(f.__name__, '->', inspect.signature(f).return_annotation)
"
```

```
read_jsonl -> Iterator[dict[str, Any]]
read_jsonl_reversed -> Iterator[dict[str, Any]]
search_transactions -> Iterator[Transaction]
recent_transactions -> Iterator[Transaction]
```

`list[...]`가 아니라 `Iterator[...]`라는 것이 **"전량 적재하지 않는다"를 타입으로
못박은 지점**입니다.

---

## 항목 4 — 설계 근거

### 4-2. 거래가 10만 건이면 병목은 어디이고 어떻게 개선할 것인가?

위 3-1의 1만 건 측정을 그대로 쓰거나, 10만 건으로 재려면:

```bash
./verification.sh --bench
```

```
INFO  파일 크기                        13.2 MB (100000건)
INFO  list --limit 20                     0.001초
INFO  search --tag meal --limit 20        0.000초
INFO  next_id() (add 의 비용)             0.000초
INFO  search --q 없는키워드 (전량 스캔)    0.366초
INFO  summary --month 2024-01 (전량 스캔)  0.374초
INFO  delete (전량 읽기 + 전량 재작성)     0.700초
```

---

### 4-3. import CSV에 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지키는가?

```bash
cat > /tmp/pw-mixed.csv <<'CSV'
date,type,category,amount,memo,tags
2024-03-01,expense,food,10000,정상1,
2024-13-99,expense,food,10000,날짜깨짐,
2024-03-02,bad,food,10000,타입깨짐,
2024-03-03,expense,ghost,10000,없는카테고리,
2024-03-04,expense,food,-500,음수금액,
2024-03-05,expense,food,만원,숫자아님,
2024-03-06,expense,food,20000,정상2,
CSV

rm -rf /tmp/pw-mix
python3.12 -m budget_app --data-dir /tmp/pw-mix import --from /tmp/pw-mixed.csv
```

```
[건너뜀] 3행: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[건너뜀] 4행: 타입은 income 또는 expense 중 하나여야 합니다.
[건너뜀] 5행: 등록되지 않은 카테고리입니다: ghost
[건너뜀] 6행: 금액은 0보다 큰 정수여야 합니다.
[건너뜀] 7행: 금액은 숫자로 입력해야 합니다.
[완료] imported=2, skipped=5
```

줄 번호가 **파일 편집기의 줄 번호와 일치**하는지, 실제로 2건만 저장됐는지:

```bash
sed -n '3p' /tmp/pw-mixed.csv                # 2024-13-99,... 가 나와야 함
wc -l < /tmp/pw-mix/transactions.jsonl       # 2
```

stdout / stderr 분리:

```bash
python3.12 -m budget_app --data-dir /tmp/pw-mix2 import --from /tmp/pw-mixed.csv 2>/dev/null
```

```
[완료] imported=2, skipped=5          ← 건너뜀 안내는 stderr 라서 사라집니다
```

`--dry-run`:

```bash
rm -rf /tmp/pw-dry
python3.12 -m budget_app --data-dir /tmp/pw-dry import --from /tmp/pw-mixed.csv --dry-run
ls /tmp/pw-dry
```

```
[검증 완료] imported=2, skipped=5     ← [완료] 가 아니라 [검증 완료]

categories.jsonl                      ← transactions.jsonl 이 없습니다
```

> `categories.jsonl`은 기본 카테고리를 확인하느라 만들어집니다. **거래는 한 건도
> 쓰이지 않습니다.**

헤더가 스키마와 다르면 파일 단위로 즉시 실패:

```bash
printf 'day,kind,cat,won\n2024-03-01,expense,food,1000\n' > /tmp/pw-wrong.csv
python3.12 -m budget_app --data-dir /tmp/pw-bad import --from /tmp/pw-wrong.csv; echo "exit=$?"
ls /tmp/pw-bad
```

```
[오류] CSV 헤더에 필수 칸이 없습니다: date, type, category, amount
[힌트] 첫 줄은 date,type,category,amount,memo,tags 형식이어야 합니다.
exit=2

ls: /tmp/pw-bad: No such file or directory      ← 한 건도 저장하지 않습니다
```

---

## 항목 5 — 보너스

원자성은 항목 2-3의 md5 확인이 그대로 근거입니다.

```bash
grep -n 'NamedTemporaryFile\|os.fsync\|os.replace' budget_app/repositories.py
```

`backup`은 `--help`에는 보이지만 핸들러가 없습니다.

```bash
python3.12 -m budget_app backup
```

```
[오류] 'backup' 명령은 아직 구현되지 않았습니다.
[힌트] 구현 순서는 docs/plan.md 9절을 참고하세요.
```

**전역 옵션 위치** (argparse 서브커맨드 처리의 결과. study.md 5절 참고):

```bash
python3.12 -m budget_app --version                      # budget_app 0.1.0
python3.12 -m budget_app --verbose list --limit 1       # O — 명령보다 앞
python3.12 -m budget_app list --limit 1 --verbose       # X — unrecognized arguments (exit 2)
python3.12 -m budget_app --verbose                      # X — 명령이 빠짐 (exit 2)
```

---

## 정리

```bash
rm -rf /tmp/pw-*
```

전부 자동으로 다시 돌려보려면:

```bash
./verification.sh            # 83개 검증, 약 3초
./verification.sh --bench    # 10만 건 성능 측정 포함
```
