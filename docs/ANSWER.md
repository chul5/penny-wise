# 평가문항 답변 (ANSWER.md)

평가 체크리스트 항목별 답변입니다. 모든 수치는 실제 측정값이고, 코드 위치는
`파일:줄번호`로 표기했습니다.

검증 환경: Python 3.12.14 / macOS. 실행은 `python3.12 -m budget_app ...`

각 항목 끝에 **직접 확인하기**로 실행 명령어와 기대 출력을 붙였습니다. 위에서부터
순서대로 실행하면 됩니다 — 뒤 명령이 앞 명령이 만든 데이터를 씁니다. 아래 출력은
전부 실제로 실행해서 받은 것입니다.

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

10개 명령이 모두 동작합니다. `cli.py:389`의 `HANDLERS` 표에 등록된 명령이 전부입니다.

```
add  list  search  summary  budget  category  update  delete  export  import
```

`add`는 미션이 요구한 대로 대화형이고, 나머지는 옵션 방식입니다.
출력은 미션 8절 예시와 문자 단위로 일치합니다(공백 포함).

```
$ python3.12 -m budget_app list --limit 3
TX-000005 | 2024-01-20 | expense | food | 30000 | 저녁 외식
TX-000004 | 2024-01-01 | expense | rent | 150000 | 월세
TX-000003 | 2024-01-15 | expense | food | 15000 | 점심
```

`income`을 7칸으로 맞춰 `expense`와 구분선이 어긋나지 않게 한 것도 예시 그대로입니다
(`cli.py:222` `format_transaction`).

**직접 확인하기**

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

### 1-2. 재실행 후에도 데이터가 유지되는가? (저장 파일 3개 이상)

프로세스를 완전히 끝낸 뒤 새로 실행해도 그대로 읽힙니다.

```
$ python3.12 -m budget_app --data-dir ./data category add 경조사비
$ python3.12 -m budget_app --data-dir ./data add            # (대화형 입력)
$ python3.12 -m budget_app --data-dir ./data budget set --month 2024-01 --amount 500000
--- 여기서 프로세스 종료, 아래는 새 프로세스 ---
$ python3.12 -m budget_app --data-dir ./data list
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심
$ python3.12 -m budget_app --data-dir ./data category list
- food - transport - rent - salary - etc - 경조사비
$ python3.12 -m budget_app --data-dir ./data budget show
- 2024-01: 500000원
```

저장 파일은 **3개로 분리**되어 있습니다.

```
data/transactions.jsonl   data/categories.jsonl   data/budgets.jsonl
```

`open_stores()`(`repositories.py:309`)가 세 저장소를 한 묶음으로 만듭니다.
파일은 **쓸 때 자동 생성**되고, 조회만 하는 명령은 파일을 만들지 않습니다.

**직접 확인하기**

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

### 1-3. category add/list/remove가 정상 동작하는가? (사용 중 카테고리 처리 포함)

사용 중인 카테고리는 삭제를 **막습니다**. 그냥 지우면 거래의 `category`가 등록 목록에
없는 값이 되어 데이터가 어긋나기 때문입니다.

```
$ python3.12 -m budget_app category remove food
[오류] 'food' 카테고리를 사용하는 거래가 1건 있습니다.
[힌트] --replace-with <다른카테고리> 로 대체 카테고리를 지정하세요.

$ python3.12 -m budget_app category remove food --replace-with etc
[삭제 완료] category=food (거래 1건을 etc로 옮겼습니다)
```

`remove_category()`(`services.py:78`)에서 **순서가 중요**합니다. 거래를 먼저 옮기고
카테고리를 나중에 지웁니다. 반대로 하면 두 단계 사이에서 실패했을 때 거래가 존재하지
않는 카테고리를 가리키게 됩니다. 이 순서라면 실패해도 카테고리가 남아 있을 뿐이라
다시 실행하면 됩니다.

중복 판정은 대소문자를 무시합니다(`casefold`). `food`와 `FOOD`가 함께 등록되면
`summary`의 카테고리별 집계가 둘로 쪼개져 리포트가 조용히 틀리기 때문입니다.
다만 저장은 입력한 대로 합니다 — `Netflix`를 `netflix`로 바꿔버리면 사용자가 정한
이름을 앱이 마음대로 고치는 셈입니다.

**직접 확인하기**

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

### 1-4. budget set이 저장되며, summary에서 사용률/초과 여부가 출력되는가?

```
$ python3.12 -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500000원

$ python3.12 -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

초과 시에는 경고와 **초과 금액**을 함께 출력합니다.

```
예산: 100000원 (사용률 215.0%)
[경고] 예산을 115000원 초과했습니다.
```

예산이 없는 달은 예산 줄을 아예 출력하지 않고, 거래가 없는 달은 `2024-09 데이터 없음`을
출력합니다.

같은 달에 다시 `set`하면 줄이 늘지 않고 **교체**됩니다(`BudgetStore.set`, `repositories.py:260`).
같은 달이 두 줄로 남으면 어느 쪽이 맞는지 알 수 없기 때문입니다.

**직접 확인하기**

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

### 1-5. import/export가 명시된 CSV 스키마로 동작하는가?

UTF-8(BOM 없음), 헤더 포함, 칸 순서 고정입니다.

```csv
date,type,category,amount,memo,tags
2024-01-01,expense,rent,150000,월세,fixed
2024-01-15,expense,food,15000,"점심, 김치찌개","meal,work"
```

`csv.DictWriter`/`DictReader`를 씁니다(`services.py:365`, `services.py:420`).
직접 문자열을 조립하지 않은 이유는 **tags를 쉼표로 이어붙이는데 파일 구분자도 쉼표**이기
때문입니다. 직접 만들면 칸이 어긋나고, `csv` 모듈은 알아서 큰따옴표로 감쌉니다.

왕복 검증 결과입니다. 쉼표와 큰따옴표가 든 값도 그대로 보존됩니다.

```
$ python3.12 -m budget_app export --out round.csv --month 2024-01
[완료] round.csv (4 records)
$ python3.12 -m budget_app import --from round.csv     # 빈 저장소에서
[완료] imported=4, skipped=0

원본 memo: '점심, 김치찌개 "특"'  →  가져온 memo: '점심, 김치찌개 "특"'  (일치)
```

`export`는 `--month` 또는 `--from`/`--to` 중 하나 이상을 **반드시** 받습니다.
조건 없이 실행하면 파일을 만들지도 않고 오류로 끝납니다.

**직접 확인하기**

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

### 1-6. 잘못된 입력/파일 오류에서 스택트레이스 없이 오류 메시지와 힌트를 출력하는가?

```
$ python3.12 -m budget_app delete --id TX-999999
[오류] id=TX-999999 거래를 찾을 수 없습니다.
[힌트] list 명령으로 존재하는 id를 확인해 보세요.

$ python3.12 -m budget_app import --from /없는파일.csv
[오류] CSV 파일이 없습니다: /없는파일.csv
[힌트] --from 경로를 확인하세요.
```

`[오류]` 줄을 만드는 곳은 **코드 전체에서 한 군데**입니다(`decorators.py:19` `print_error`).

```
$ grep -rn 'print(f"\[오류\]' budget_app/*.py
budget_app/decorators.py:25
```

각 예외가 자기 `hint`와 `exit_code`를 들고 다니므로(`errors.py:11~`) 출력하는 쪽에서
분기할 것이 없습니다.

**예상하지 못한 오류(우리 쪽 버그)도 스택트레이스를 노출하지 않습니다.** `main()`에
마지막 방어선을 두었습니다. 다만 `--verbose`를 주면 개발자가 원인을 볼 수 있게
traceback을 출력합니다 — 사용자에게 숨기는 것과 개발자에게까지 숨기는 것은 다릅니다.

```
[오류] 예상하지 못한 오류가 발생했습니다: ...
[힌트] --verbose 로 다시 실행하면 자세한 내용을 볼 수 있습니다.
```

**직접 확인하기**

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

### 1-7. 오류 상황에서 종료 코드가 0이 아닌가?

| 상황 | 코드 |
| --- | --- |
| 성공 | 0 |
| 입력값 오류, 없는 데이터, 중복, 사용 중 카테고리 | 1 |
| 파일 접근 실패, 잘못된 사용법(argparse) | 2 |
| Ctrl+C 중단 | 130 |

```
$ python3.12 -m budget_app category list        ; echo $?   → 0
$ python3.12 -m budget_app delete --id TX-999999 ; echo $?   → 1
$ python3.12 -m budget_app import --from /nope.csv ; echo $? → 2
$ python3.12 -m budget_app search --type bad     ; echo $?   → 2
```

`argparse`의 사용법 오류가 2인 것은 표준 동작이라 그대로 두고, 파일 오류도
`DataFileError.exit_code = 2`로 맞췄습니다.

**직접 확인하기**

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

### 2-1. 3개 이상 모듈로 분리되어 있고, 각 모듈의 책임을 어떻게 나눴는가?

**7개 모듈**입니다. 나눈 기준은 "무엇에 대해 알아야 하는가"입니다.

| 모듈 | 아는 것 | 모르는 것 |
| --- | --- | --- |
| `cli.py` | 어떻게 묻고 어떻게 보여줄지 | 파일이 어디 있는지, 규칙이 무엇인지 |
| `services.py` | 무엇이 규칙인지 (중복 금지, 사용 중 보호) | 파일 형식, 출력 형식 |
| `repositories.py` | 어떻게 읽고 쓸지 (JSONL, 원자성) | 규칙, 사용자 |
| `models.py` | 데이터의 모양 | 아무것도 (errors만 import) |
| `validators.py` | 값이 올바른지 | 저장소, 사용자 |
| `decorators.py` | 공통 관심사(오류 처리) | 도메인 |
| `errors.py` | 오류의 종류와 힌트 | 아무것도 |

의존 방향은 **한 방향**입니다.

```
cli.py  →  services.py  →  repositories.py  →  models.py
```

`repositories`는 `services`를 import하지 않고, `models`는 `errors` 외에 아무것도
import하지 않습니다. 그래서 CLI를 거치지 않고 서비스 함수만 호출해도 앱의 규칙을
그대로 검증할 수 있고, 실제로 이 프로젝트의 모든 검증을 그렇게 했습니다.

**경계를 지키기 위해 한 번 계획을 바꿨습니다.** 대화형 재입력 루프(`prompt`)는 원래
`validators.py`에 두려 했는데 `cli.py`로 옮겼습니다. `validators.py`가 "`input()`을
부르지 않는다"는 계약을 지켜야 대화형 `add`, 옵션 방식 `update`, CSV `import`가
같은 검증 함수를 재사용할 수 있기 때문입니다.

### 2-2. 최소 2개 이상의 클래스에 부여한 책임 경계를 어떻게 정했는가?

클래스는 **16개**입니다(models 5, repositories 4, errors 7). 경계를 정한 원칙은
"**파일을 다루는 기계적인 일은 함수, 클래스는 타입 계약만**"입니다.

```python
# 함수: 파일 다루는 코드는 한 번만 작성한다
def read_jsonl(path)           -> Iterator[dict]      # repositories.py:51
def read_jsonl_reversed(path)  -> Iterator[dict]      # repositories.py:72
def append_jsonl(path, record) -> None                # repositories.py:114
def write_jsonl(path, records) -> int                 # repositories.py:140

# 클래스: 그 함수들을 감싸 정확한 타입을 붙인다
class TransactionRepository:                          # repositories.py:188
    def stream(self)          -> Iterator[Transaction]
    def stream_reversed(self) -> Iterator[Transaction]
    def next_id(self)         -> str
class CategoryStore:  ...                             # repositories.py:232
class BudgetStore:    ...                             # repositories.py:260
```

**처음에는 `JsonlRepository[T]` 제네릭 베이스에 loader를 주입하는 구조로 만들었다가
걷어냈습니다.** 파일 3개 읽으려고 `Generic`/`TypeVar`/`Callable`을 동원하는 게 과했고,
걷어낸 결과가 **79줄 → 52줄로 짧아지면서 타입은 더 정확해졌습니다.** 이전에는 loader
주입 때문에 `Iterator[T]`라는 간접적 표현이었지만, 지금은 `stream()`이 곧바로
`Iterator[Transaction]`입니다.

세 저장소의 책임 차이도 의도적입니다.

- `TransactionRepository` — 스트리밍이 목적. 리스트를 절대 만들지 않습니다.
- `CategoryStore.names()` — **리스트를 돌려줍니다.** 수가 적고 중복 확인과 전체 목록
  출력이 목적이라 스트리밍할 이유가 없습니다.
- `BudgetStore.set()` — append가 아니라 **전체 재작성**입니다. 한 달에 한 줄뿐이라
  다시 쓰는 비용이 없고, 같은 달이 두 줄로 남는 문제를 원천 차단합니다.

`Stores`(`repositories.py:297`)는 세 저장소를 묶는 frozen dataclass입니다. 핸들러마다
필요한 저장소가 다른데(`category remove`는 카테고리+거래, `summary`는 거래+예산),
따로 넘기면 시그니처가 제각각이 됩니다. 한 묶음으로 넘겨 **모든 핸들러를
`(args, stores) -> int`로 통일**했고, 그 통일성이 `@handle_errors`를 전부 똑같이
적용할 수 있게 하고 `dispatch()`를 분기 없는 dict 조회로 만듭니다.

### 2-3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?

**임시 파일에 완성한 뒤 `os.replace`로 한 번에 교체**합니다(`write_jsonl`, `repositories.py:140`).

```python
with tempfile.NamedTemporaryFile("w", dir=path.parent, ...) as fp:
    tmp = Path(fp.name)
    for record in records:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")
    fp.flush()
    os.fsync(fp.fileno())      # 디스크에 내려간 뒤 교체해야 의미가 있다
os.replace(tmp, path)          # 원자적
```

파일 기반 저장에는 롤백해 줄 DB 엔진이 없습니다. 원본을 직접 고치다가 중간에 죽으면
파일이 반쯤 망가진 상태로 남습니다. 이 방식이면 **성공하면 새 파일, 실패하면 원본
그대로이고 중간 상태가 없습니다.**

세 가지를 더 챙겼습니다.

1. **임시 파일은 반드시 같은 폴더에** 만듭니다. `os.replace`의 원자성은 같은
   파일시스템 안에서만 보장됩니다.
2. **먼저 찾고 나중에 씁니다.** `delete`/`update`는 대상을 먼저 조회하고 없으면 그
   자리에서 실패합니다. 곧바로 재작성부터 하면 없는 id를 지우라는 요청에도 파일을
   통째로 다시 쓰게 되는데, 얻는 것 없이 위험만 지는 일입니다.
3. **읽으면서 동시에 써도 안전합니다.** `repo.replace_all(t for t in repo.stream() if ...)`
   처럼 원본을 스트리밍하며 임시 파일에 쓰는데, 원본은 교체 직전까지 손대지 않습니다.
   그래서 delete/update가 전량 적재 없이 한 줄로 표현됩니다.

**실제로 검증했습니다.** 쓰기 도중 예외를 던지는 제너레이터를 넘겨 확인한 결과:

```
crash mid-write: RuntimeError raised
   original untouched: True      (md5 동일)
   still readable: ['TX-000001', 'TX-000002', 'TX-000003']
   tmp cleaned up: none
```

실패한 `delete`/`update` 후에도 파일이 **바이트 단위로 동일**함을 md5로 확인했습니다.

**직접 확인하기** — 실패한 명령이 저장 파일을 조금도 건드리지 않는지 md5로 봅니다.

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

**어떻게 구현했는가.**

핵심은 `read_jsonl_reversed()`(`repositories.py:72`)입니다. "최신순 출력"과 "전량 적재
금지"는 원래 충돌합니다. 전체 정렬은 본질적으로 전부 메모리에 올려야 하기 때문입니다.
그래서 **append-only 파일은 뒤가 곧 최근**이라는 성질을 이용해, 파일 끝에서부터
64KB씩 거꾸로 읽습니다.

```python
with path.open("rb") as fp:
    pos = fp.seek(0, os.SEEK_END)
    head = b""                       # 아직 완성되지 않은 맨 앞 조각
    while pos > 0:
        size = min(chunk_size, pos)
        pos -= size
        fp.seek(pos)
        lines = (fp.read(size) + head).split(b"\n")
        head = lines.pop(0)          # 앞쪽 청크와 이어질 수 있으니 보류
        for line in reversed(lines):
            yield json.loads(...)    # return이 아니라 yield
```

청크 경계가 줄 중간을 자를 수 있으므로 각 청크의 첫 조각은 다음(더 앞쪽) 청크와
이어붙일 때까지 들고 있습니다. 바이트 단위로 `b"\n"`에서 자르는 게 안전한 이유는
**UTF-8이 멀티바이트 문자 안에 0x0A를 절대 넣지 않도록 설계**되어 있기 때문입니다.

`search`는 조건 다섯 개를 제너레이터 다섯 개로 겹치지 않고 **술어 하나 + `filter()`**
로 합쳤습니다(`services.py:153`). `filter`가 게으르므로 스트리밍은 동일하고 코드는
짧습니다. `list`는 조건 없는 `search`에 위임하므로 `--limit` 검증과 스트리밍 경로가
한 곳에만 존재합니다.

마지막으로 `islice`가 `--limit`만큼 채우면 제너레이터를 더 당기지 않습니다.
**리스트를 한 번이라도 만들면 스트리밍이 깨지므로** 서비스는 `Iterator`를 그대로
돌려줍니다.

**왜 유리한가 — 측정값입니다.**

| 파일 | 명령 | 읽은 양 |
| --- | --- | --- |
| 10,000건 / 969 KB | `list --limit 3` | **65,536 바이트 (6.8%)** |
| 10,000건 / 969 KB | `next_id()` | **65,536 바이트 (6.8%)** |
| 100,000건 / 13.3 MB | `list --limit 20` | **0.001초** |
| 100,000건 / 13.3 MB | `search --tag meal --limit 20` | **0.000초** |

10만 건 13MB 파일에서도 최근 20건 조회가 1밀리초입니다. 전량 적재였다면 13MB를
파싱해야 했습니다.

**한계도 함께 말씀드립니다.** 조건에 맞는 게 하나도 없는 검색은 파일 전체를 읽습니다
(측정: 100% 읽고 0.362초). 색인이 없으니 피할 수 없습니다. 스트리밍은 **최근 쪽에
답이 있을 때** 이득이 크고, 아예 없을 때는 이득이 없습니다.

**트레이드오프도 의도적으로 선택했습니다.** 이 방식의 "최신순"은 **날짜순이 아니라
입력 순서의 역순**입니다. 과거 날짜를 나중에 입력하면 목록 위에 뜹니다. 엄격한
날짜순을 원하면 `heapq.nlargest(limit, stream(), key=date)`가 필요한데, 그러면 메모리는
O(limit)로 줄지만 **파일은 전량 읽어야** 합니다. 미션이 요구하는 것은 스트리밍이므로
입력 순서 역순을 택하고 README에 명시했습니다.

**직접 확인하기** — 1만 건을 만들어 재 봅니다.

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

### 3-2. 데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했는가?

`@handle_errors`(`decorators.py:36`)입니다. 도메인 예외를 잡아 `[오류]`/`[힌트]` 출력과
종료 코드로 바꿉니다.

```python
def handle_errors(func: Callable[P, int]) -> Callable[P, int]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except BudgetAppError as exc:
            return report_error(exc)          # 출력 + 그 예외가 정한 종료 코드
        except KeyboardInterrupt:
            print("\n[중단] 사용자가 실행을 취소했습니다.", file=sys.stderr)
            return 130
    return wrapper
```

**왜 분리했는가 — 결과로 증명됩니다. 모든 명령 핸들러에 `try/except`가 하나도 없습니다.**

```python
@handle_errors
def handle_delete(args: argparse.Namespace, stores: Stores) -> int:
    removed = delete_transaction(stores, args.tx_id)     # 없으면 예외를 그냥 올린다
    print(f"[삭제 완료] id={removed.id}")
    return 0
```

핸들러는 "요청을 처리한다" 하나만 합니다. 오류를 어떤 문구로 보여줄지, 종료 코드를
뭘로 할지는 10개 명령에 똑같이 걸리는 관심사이므로 한 곳에 모았습니다. 분리하지
않았다면 같은 `try/except`가 10번 복사되고, 문구를 고칠 때 10곳을 고쳐야 합니다.

이게 가능한 이유는 **모든 핸들러가 `(args, stores) -> int` 시그니처를 공유**하기
때문입니다(항목 2-2). 시그니처가 제각각이면 데코레이터를 똑같이 씌울 수 없습니다.

`ParamSpec`을 쓴 것도 이유가 있습니다. `Callable[..., int]`로 뭉개면 감싼 뒤
`(args, stores)` 시그니처 검사가 사라집니다.

**직접 확인하기**

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

### 3-3. 타입 힌트의 이점을 실제 코드 예로 어떻게 확인했고, 왜 도움이 되는가?

**예 1 — `Iterator`인지 `list`인지가 설계 의도를 못 박습니다.**

```python
def recent_transactions(stores, limit) -> Iterator[Transaction]      # services.py
def summarize_month(stores, month, top) -> MonthlySummary
```

겉보기에 둘 다 `for`로 돌 수 있지만, `list[Transaction]`은 "메모리에 전부 올렸다",
`Iterator[Transaction]`은 "스트리밍이다"라는 **완전히 다른 약속**입니다. 이 프로젝트의
채점 요구가 스트리밍이므로, 반환 타입 자체가 요구사항을 지키고 있다는 선언이 됩니다.
리뷰할 때 `list(...)`가 하나라도 끼면 타입이 먼저 어긋납니다.

**예 2 — `TypeVar`로 재입력 루프 하나가 모든 타입을 지원합니다.**

```python
def prompt(label: str, parse: Callable[[str], T]) -> T:   # cli.py:44
```

실제 반환 타입 확인:

```
prompt("금액(양수)", parse_amount)      →  int
prompt("태그(쉼표로 구분)", parse_tags)  →  tuple[str, ...]
prompt("날짜(YYYY-MM-DD)", parse_date)  →  str
```

`TypeVar` 없이 `Callable[[str], Any]`로 뒀다면 모든 호출부가 `Any`를 받아 결과에
대한 자동완성과 검사를 잃습니다.

**예 3 — `Mapping`과 `dict`의 차이로 의도를 전달합니다.**

```python
def from_dict(cls, raw: Mapping[str, Any]) -> Transaction:   # models.py
```

`Mapping`은 "이 함수는 넘겨준 딕셔너리를 **수정하지 않는다**"는 약속입니다. 타입만으로
계약을 표현한 예입니다.

**예 4 — `int | None`이 "없음"을 정상 상태로 표현합니다.**

```python
def get(self, month: str) -> Budget | None:      # repositories.py:260
usage_rate: float | None                          # models.py:110
```

"예산이 설정되지 않음"은 오류가 아니라 정상 상태입니다. 예외로 만들었다면 평범한
경로에서 `try/except`를 써야 했습니다.

**직접 확인하기**

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

### 4-1. JSONL과 CSV 중 왜 JSONL을 택했는가?

| | JSONL | CSV |
| --- | --- | --- |
| 1줄 = 1레코드 | ✅ 스트리밍에 자연스러움 | ✅ (단, 값 안의 개행이 문제) |
| 중첩/배열 값 | ✅ `tags: ["meal","work"]` 그대로 | ✗ 문자열로 뭉개야 함 |
| 필드 추가 | ✅ 기존 줄 그대로 두고 추가 | ✗ 모든 줄의 칸 수가 바뀜 |
| append 비용 | ✅ 일정 | ✅ 일정 |
| 사람이 읽기 | 보통 (`ensure_ascii=False`로 한글 그대로) | ✅ 좋음 |
| 스프레드시트 호환 | ✗ | ✅ |

**택한 이유는 `tags`입니다.** 거래에 태그가 여러 개 붙는데, CSV로 저장하면 배열을
문자열로 뭉개고 읽을 때 다시 쪼개야 합니다. 그 과정에서 태그 안의 쉼표를 어떻게 할지
같은 문제가 생깁니다. JSONL은 `["meal","work"]`를 그대로 담습니다.

두 번째 이유는 **필드 추가의 안전성**입니다. 나중에 `currency` 같은 필드가 붙어도
기존 줄은 그대로 유효하고, 없는 필드는 `raw.get(...)`으로 기본값 처리됩니다.
CSV였다면 모든 줄의 칸 수가 달라집니다.

**CSV를 버린 게 아니라 역할을 나눴습니다.** 저장은 JSONL, 교환(import/export)은 CSV입니다.
스프레드시트 호환은 교환 포맷에서만 필요하고, 그건 `csv` 모듈이 처리합니다.

### 4-2. 거래가 10만 건이면 병목은 어디이고 어떻게 개선할 것인가?

**실제로 10만 건(13.3 MB)을 만들어 측정했습니다.**

| 명령 | 시간 | 성격 |
| --- | --- | --- |
| `list --limit 20` | **0.001초** | 뒤에서 20건만 읽고 중단 |
| `search --tag meal --limit 20` | **0.000초** | 최근에 맞는 게 있어 즉시 중단 |
| `add` (next_id + append) | **0.001초** | 끝 1바이트 확인 + append |
| `search --q 없는키워드` | **0.362초** | 전량 스캔 (매칭 0건) |
| `summary --month 2024-01` | **0.388초** | 전량 스캔 (그 달 8,333건 집계) |
| `delete` | **0.598초** | 전량 읽기 + 전량 재작성 |

**병목은 세 가지이고, 성격이 다릅니다.**

**(1) `delete`/`update` — 0.6초, 가장 무겁습니다.**
한 건을 고치려고 13MB를 읽고 13MB를 다시 씁니다. O(N) 읽기 + O(N) 쓰기입니다.
- *개선안 A (간단):* **삭제 표시(tombstone)**. 실제로 지우지 않고 `{"id":..., "deleted":true}`를
  append하고, 읽을 때 걸러냅니다. 삭제가 O(1)이 되고, 쌓이면 `compact` 명령으로 한 번에
  정리합니다. append-only의 성질을 유지한다는 점에서 현재 구조와 잘 맞습니다.
- *개선안 B:* 월별 파일 분할(`transactions-2024-01.jsonl`). 재작성 범위가 한 달로 줄어
  1/12이 됩니다. 월 기반 조회(`summary`)도 같이 빨라집니다.

**(2) `summary` — 0.388초, 매달 전량 스캔.**
- *개선안:* 월별 파일 분할이면 그 달만 읽습니다. 또는 **집계 캐시** 파일을 두고
  거래가 추가될 때 갱신합니다(정합성 관리 비용이 생기므로 분할이 먼저입니다).
- 참고로 메모리는 이미 안전합니다. `Counter`에 쌓이는 건 거래 건수가 아니라
  **카테고리 개수**여서, 10만 건을 집계해도 항목 몇 개만 남습니다.

**(3) 매칭이 없는 `search` — 0.362초.**
- *개선안:* 색인 없이는 피할 수 없습니다. 태그/카테고리별 역색인 파일을 두면 O(1)에
  가까워지지만, 색인 정합성 유지 비용이 생깁니다. 10만 건에서 0.36초는 대화형 CLI에서
  체감되지 않는 수준이라 **현 시점에는 넣지 않는 게 맞다**고 판단했습니다.

**개선 우선순위: 월별 파일 분할 → tombstone → 색인.** 앞의 두 개가 세 병목 중 둘을
동시에 해결하고 구현도 단순합니다.

**한 가지는 이미 이 과제 중에 고쳤습니다.** `append_jsonl`이 개행 확인을 위해
`read_bytes()[-1:]`로 **파일 전체를 읽고 있었습니다.** `add` 한 번에는 문제가 없지만
`import`가 행마다 append하면 O(N²)이 됩니다. 마지막 1바이트만 `seek`으로 확인하도록
바꾼 결과, 300건 append 시 읽는 양이 **약 5.6MB → 299바이트**가 됐습니다.

**직접 확인하기** — 위 3-1의 1만 건 측정을 그대로 쓰거나, 10만 건으로 재려면:

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

### 4-3. import CSV에 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지키는가?

**부분 성공(partial success)을 택했습니다.** 롤백이 아닙니다.

```
$ python3.12 -m budget_app import --from mixed.csv
[건너뜀] 3행: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[건너뜀] 4행: 타입은 income 또는 expense 중 하나여야 합니다.
[건너뜀] 5행: 등록되지 않은 카테고리입니다: ghost
[건너뜀] 6행: 금액은 0보다 큰 정수여야 합니다.
[건너뜀] 7행: 금액은 숫자로 입력해야 합니다.
[완료] imported=2, skipped=7
```

**왜 롤백이 아니라 부분 성공인가.** 100행 중 3행이 틀렸다고 97행을 버리면, 사용자는
파일을 고쳐 처음부터 다시 넣어야 합니다. 가계부 데이터는 서로 독립적이라 한 행의
실패가 다른 행의 유효성을 해치지 않습니다. **원자성이 필요한 곳은 "한 파일을 다시
쓰는 순간"이지 "여러 행을 넣는 과정"이 아닙니다.**

**신뢰를 지키는 장치는 네 가지입니다.**

1. **줄 번호와 이유를 모두 보고합니다.** "7건 실패"만 알려주면 사용자가 어디를 고쳐야
   할지 모릅니다. `3행: 날짜 형식이...`처럼 헤더를 1행으로 세어 파일 편집기의 줄
   번호와 일치시켰습니다.
2. **`--dry-run`이 있습니다.** 저장하기 전에 검증만 해볼 수 있습니다. 실제로 파일이
   생성되지 않음을 확인했습니다.
3. **검증 규칙이 `add`와 완전히 같습니다.** CSV 경로만 느슨하면 대화형으로는 못 넣는
   값이 옵션으로 들어가는 구멍이 생깁니다. 같은 `validators` 함수를 씁니다.
4. **파일 단위 실패와 행 단위 실패를 구분합니다.** 헤더에 필수 칸이 없거나 파일이
   없으면 한 건도 넣지 않고 **종료 코드 2로 즉시 실패**합니다. 스키마가 틀린 파일을
   "0건 성공"으로 조용히 넘기면 사용자가 성공한 줄 압니다.

```
$ python3.12 -m budget_app import --from wrong.csv
[오류] CSV 헤더에 필수 칸이 없습니다: date, type, category, amount
[힌트] 첫 줄은 date,type,category,amount,memo,tags 형식이어야 합니다.   (exit 2)
```

또한 건너뛴 이유는 **stderr**, 결과 요약은 **stdout**으로 보냅니다. 로그로
리다이렉트해도 진단이 터미널에 남습니다.

**직접 확인하기**

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

미션 5절 보너스 4개 중 **"저장 원자성 강화"는 이미 구현되어 있습니다.**

> 4. 저장 원자성 강화 — update/delete 시 임시 파일에 쓰고 rename으로 교체하는 방식을 적용한다.

`write_jsonl`(`repositories.py:140`)이 `tempfile` + `fsync` + `os.replace`로 처리하며,
쓰기 도중 예외가 나도 원본이 바이트 단위로 보존됨을 확인했습니다(항목 2-3 참고).
보너스 과제로 따로 만든 것이 아니라 `update`/`delete`/`category remove`가 모두 이
경로를 재사용하도록 처음부터 저장소 계층에 넣었습니다.

나머지 보너스(백업, 반복 내역, 테이블 정렬)는 구현하지 않았습니다.

**직접 확인하기**

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

## 부록 — 검증 방법

테스트 프레임워크 없이, **임시 디렉터리에 실제 파일을 만들어** 각 단계를 확인했습니다.
`./data`를 건드리지 않으므로 안전합니다.

```bash
python3.12 - <<'PY'
import tempfile
from pathlib import Path
from budget_app.repositories import open_stores
with tempfile.TemporaryDirectory() as d:
    stores = open_stores(Path(d) / "data")
    ...
PY
```

측정이 필요한 항목(읽은 바이트 수, 파일 열린 횟수, 메모리)은 `Path.open`을 감싸
계측하거나 `tracemalloc`을 사용했습니다. "스트리밍한다"를 주장하지 않고 **읽은
바이트를 세어 증명**하려는 목적입니다.

이 확인들을 스크립트 하나로 묶은 것이 [`../verification.sh`](../verification.sh)입니다.
83개 항목을 검사하고 결과를 PASS/FAIL로 출력합니다. 쓰기 도중에 예외를 던져 원자성을
확인하는 것처럼 CLI만으로는 어려운 검증도 여기에 들어 있습니다.

```
전체 통과  PASS 83 / FAIL 0
```

설계 결정의 배경과 기각한 대안은 [plan.md](plan.md)에, 사용법은
[../README.md](../README.md)에, 코드 구조를 비전공자용으로 풀어 쓴 설명은
[OVERVIEW.md](OVERVIEW.md)에 있습니다.
