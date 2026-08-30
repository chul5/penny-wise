# 평가문항 답변 (ANSWER.md)

평가 체크리스트 항목별 답변입니다. 모든 수치는 실제 측정값이고, 코드 위치는
`파일:줄번호`로 표기했습니다.

검증 환경: Python 3.12.14 / macOS. 실행은 `python3.12 -m budget_app ...`

각 항목을 **직접 쳐서 확인하는 명령어와 기대 출력**은 [COMMAND.md](COMMAND.md)에
따로 있습니다. 항목마다 해당 절로 가는 링크를 달아 두었습니다.
전부 한 번에 자동으로 돌리려면 [`../verification.sh`](../verification.sh)를 쓰세요.

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
  - [2-1. 3개 이상 모듈로 분리되어 있고, 각 모듈의 책임을 어떻게 나눴는가?](#2-1-3개-이상-모듈로-분리되어-있고-각-모듈의-책임을-어떻게-나눴는가)
  - [2-2. 최소 2개 이상의 클래스에 부여한 책임 경계를 어떻게 정했는가?](#2-2-최소-2개-이상의-클래스에-부여한-책임-경계를-어떻게-정했는가)
  - [2-3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?](#2-3-파일-기반-updatedelete를-어떻게-안전하게-처리했는가)
- [항목 3 — 제너레이터 / 데코레이터 / 타입 힌트](#항목-3--제너레이터--데코레이터--타입-힌트)
  - [3-1. list/search를 제너레이터로 스트리밍 처리한 방식과, 왜 유리한가?](#3-1-listsearch를-제너레이터로-스트리밍-처리한-방식과-왜-유리한가)
  - [3-2. 데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했는가?](#3-2-데코레이터로-분리한-공통-기능이-무엇이며-왜-분리가-필요했는가)
  - [3-3. 타입 힌트의 이점을 실제 코드 예로 어떻게 확인했고, 왜 도움이 되는가?](#3-3-타입-힌트의-이점을-실제-코드-예로-어떻게-확인했고-왜-도움이-되는가)
- [항목 4 — 설계 근거](#항목-4--설계-근거)
  - [4-1. JSONL과 CSV 중 왜 JSONL을 택했는가?](#4-1-jsonl과-csv-중-왜-jsonl을-택했는가)
  - [4-2. 거래가 10만 건이면 병목은 어디이고 어떻게 개선할 것인가?](#4-2-거래가-10만-건이면-병목은-어디이고-어떻게-개선할-것인가)
  - [4-3. import CSV에 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지키는가?](#4-3-import-csv에-깨진-행이-섞이면-어떻게-처리해-사용자-신뢰를-지키는가)
- [항목 5 — 보너스](#항목-5--보너스)
- [부록 — 검증 방법](#부록--검증-방법)

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

> **직접 확인하기** → [COMMAND.md — 1-1](COMMAND.md#1-1-addlistsearchsummaryexportimportupdatedelete가-요구사항대로-동작하는가)

### 1-2. 재실행 후에도 데이터가 유지되는가? (저장 파일 3개 이상)

프로세스를 완전히 끝낸 뒤 새로 실행해도 그대로 읽힙니다. 아래는 빈 폴더에서
시작하는 자체 완결 예시입니다 — 그대로 붙여넣어 확인할 수 있습니다.

```bash
P=/tmp/pw-persist && rm -rf $P                  # 빈 상태에서 시작

python3.12 -m budget_app --data-dir $P category add 경조사비
printf '2024-01-15\nexpense\nfood\n15,000\n점심\n회사\n' \
  | python3.12 -m budget_app --data-dir $P add
python3.12 -m budget_app --data-dir $P budget set --month 2024-01 --amount 500000
```

```
[저장 완료] category=경조사비
날짜(YYYY-MM-DD): 타입(income/expense): 카테고리: 금액(양수): 메모(선택): 태그(쉼표로 구분, 없으면 엔터): [저장 완료] id=TX-000001
[저장 완료] 2024-01 예산 500000원
```

**세 명령은 이미 각각 별개의 프로세스였습니다.** `python -m budget_app`은 명령 하나가
끝나면 프로세스가 죽으므로, 아래 조회는 앞의 세 프로세스가 모두 종료된 뒤에 뜬 새
프로세스가 파일에서 읽어 온 결과입니다.

```bash
python3.12 -m budget_app --data-dir $P list
python3.12 -m budget_app --data-dir $P category list
python3.12 -m budget_app --data-dir $P budget show
```

```
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심

- food
- transport
- rent
- salary
- etc
- 경조사비

- 2024-01: 500000원
```

저장 파일은 **3개로 분리**되어 있습니다.

```bash
ls $P
```

```
budgets.jsonl   categories.jsonl   transactions.jsonl
```

```
data/transactions.jsonl   data/categories.jsonl   data/budgets.jsonl
```

`open_stores()`(`repositories.py:309`)가 세 저장소를 한 묶음으로 만듭니다.
파일은 **쓸 때 자동 생성**되고, 조회만 하는 명령은 파일을 만들지 않습니다.

> **직접 확인하기** → [COMMAND.md — 1-2](COMMAND.md#1-2-재실행-후에도-데이터가-유지되는가-저장-파일-3개-이상)

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

> **직접 확인하기** → [COMMAND.md — 1-3](COMMAND.md#1-3-category-addlistremove가-정상-동작하는가-사용-중-카테고리-처리-포함)

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

> **직접 확인하기** → [COMMAND.md — 1-4](COMMAND.md#1-4-budget-set이-저장되며-summary에서-사용률초과-여부가-출력되는가)

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

> **직접 확인하기** → [COMMAND.md — 1-5](COMMAND.md#1-5-importexport가-명시된-csv-스키마로-동작하는가)

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

> **직접 확인하기** → [COMMAND.md — 1-6](COMMAND.md#1-6-잘못된-입력파일-오류에서-스택트레이스-없이-오류-메시지와-힌트를-출력하는가)

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

> **직접 확인하기** → [COMMAND.md — 1-7](COMMAND.md#1-7-오류-상황에서-종료-코드가-0이-아닌가)

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

> **직접 확인하기** → [COMMAND.md — 2-3](COMMAND.md#2-3-파일-기반-updatedelete를-어떻게-안전하게-처리했는가)

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

> **직접 확인하기** → [COMMAND.md — 3-1](COMMAND.md#3-1-listsearch를-제너레이터로-스트리밍-처리한-방식과-왜-유리한가)

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

> **직접 확인하기** → [COMMAND.md — 3-2](COMMAND.md#3-2-데코레이터로-분리한-공통-기능이-무엇이며-왜-분리가-필요했는가)

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

> **직접 확인하기** → [COMMAND.md — 3-3](COMMAND.md#3-3-타입-힌트의-이점을-실제-코드-예로-어떻게-확인했고-왜-도움이-되는가)

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

> **직접 확인하기** → [COMMAND.md — 4-2](COMMAND.md#4-2-거래가-10만-건이면-병목은-어디이고-어떻게-개선할-것인가)

### 4-3. import CSV에 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지키는가?

**부분 성공(partial success)을 택했습니다.** 롤백이 아닙니다.

```
$ python3.12 -m budget_app import --from mixed.csv
[건너뜀] 3행: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[건너뜀] 4행: 타입은 income 또는 expense 중 하나여야 합니다.
[건너뜀] 5행: 등록되지 않은 카테고리입니다: ghost
[건너뜀] 6행: 금액은 0보다 큰 정수여야 합니다.
[건너뜀] 7행: 금액은 숫자로 입력해야 합니다.
[완료] imported=2, skipped=5
```

**왜 롤백이 아니라 부분 성공인가.** 100행 중 3행이 틀렸다고 97행을 버리면, 사용자는
파일을 고쳐 처음부터 다시 넣어야 합니다. 가계부 데이터는 서로 독립적이라 한 행의
실패가 다른 행의 유효성을 해치지 않습니다. **원자성이 필요한 곳은 "한 파일을 다시
쓰는 순간"이지 "여러 행을 넣는 과정"이 아닙니다.**

**신뢰를 지키는 장치는 네 가지입니다.**

1. **줄 번호와 이유를 모두 보고합니다.** "5건 실패"만 알려주면 사용자가 어디를 고쳐야
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

> **직접 확인하기** → [COMMAND.md — 4-3](COMMAND.md#4-3-import-csv에-깨진-행이-섞이면-어떻게-처리해-사용자-신뢰를-지키는가)

---

## 항목 5 — 보너스

미션 5절 보너스 4개 중 **"저장 원자성 강화"는 이미 구현되어 있습니다.**

> 4. 저장 원자성 강화 — update/delete 시 임시 파일에 쓰고 rename으로 교체하는 방식을 적용한다.

`write_jsonl`(`repositories.py:140`)이 `tempfile` + `fsync` + `os.replace`로 처리하며,
쓰기 도중 예외가 나도 원본이 바이트 단위로 보존됨을 확인했습니다(항목 2-3 참고).
보너스 과제로 따로 만든 것이 아니라 `update`/`delete`/`category remove`가 모두 이
경로를 재사용하도록 처음부터 저장소 계층에 넣었습니다.

나머지 보너스(백업, 반복 내역, 테이블 정렬)는 구현하지 않았습니다.

> **직접 확인하기** → [COMMAND.md — 항목 5 — 보너스](COMMAND.md#항목-5--보너스)

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

항목별로 손으로 재현하는 명령어는 [COMMAND.md](COMMAND.md)에, 그것을 스크립트 하나로
묶은 것이 [`../verification.sh`](../verification.sh)입니다. 스크립트는 83개 항목을 검사하고
결과를 PASS/FAIL로 출력합니다. 쓰기 도중에 예외를 던져 원자성을 확인하는 것처럼
CLI만으로는 어려운 검증도 여기에 들어 있습니다.

```
전체 통과  PASS 83 / FAIL 0
```

설계 결정의 배경과 기각한 대안은 [plan.md](plan.md)에, 사용법은
[../README.md](../README.md)에, 코드 구조를 비전공자용으로 풀어 쓴 설명은
[OVERVIEW.md](OVERVIEW.md)에 있습니다.
