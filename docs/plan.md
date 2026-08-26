# 구현 계획 (plan.md)

`docs/mission.md`의 콘솔 가계부(`budget_app`)를 어떤 구조로, 어떤 순서로 구현할지 정리한 문서.

---

## 0. 선행 조건 / 확정 결정 사항

### 환경
- 미션 요구: **Python 3.10 이상**. 이 머신에는 Homebrew **Python 3.12.14**가 설치되어 있다(`/opt/homebrew/bin/python3.12`).
  - 기본 `python3`는 시스템 3.9.6이므로, 실행/검증은 **반드시** `python3.12 -m budget_app ...` 로 한다.
  - 3.10+ 문법을 그대로 사용한다(`X | None`, `dataclass(slots=True)`).
- 표준 라이브러리만 사용 (`argparse`, `dataclasses`, `json`, `csv`, `datetime`, `pathlib`, `os`, `tempfile`, `functools`, `logging`, `typing`, `collections`, `itertools`, `unittest`).

### 미션이 "택 1 후 문서에 고정"하라고 한 항목 → 아래로 확정
| 항목 | 선택 | 이유 |
| --- | --- | --- |
| 저장 포맷 | **JSONL** | 1줄 = 1레코드로 제너레이터 스트리밍에 가장 자연스럽고, tags 같은 리스트 필드를 손실 없이 담을 수 있음. (CSV는 import/export 전용) |
| `update` 입력 방식 | **(안 A) 옵션 기반** | `update --id TX-000012 --amount 20000` 형태. 스크립트/재현성이 좋고 CLI 파싱 로직을 한 곳에 모을 수 있음. |
| 카테고리 파일이 비었을 때 | **(안 A) 기본 카테고리 자동 생성** (`food`, `transport`, `rent`, `salary`, `etc`) | 첫 실행에서 바로 `add`가 가능해 사용 흐름이 끊기지 않음. |
| 데이터 폴더 | 기본 `./data`, 전역 옵션 `--data-dir PATH`로 변경 가능 | |
| 옵션 표기 | 전부 `--` 롱옵션만 사용 (단축 옵션 없음) | 미션의 리눅스 표준 통일 요구 |

---

## 1. 디렉터리 / 모듈 구조

책임을 **CLI → 서비스 → 저장소 → 모델** 4계층으로 나눈다. (미션 14번: 최소 3모듈 → 실제 8모듈)

```
penny-wise/
├── README.md                 # 실행법, 저장 파일 위치/형식, 명령 예시, CSV 스키마
├── docs/
│   ├── mission.md
│   └── plan.md
├── data/                     # 런타임 생성 (.gitignore 처리, .gitkeep만 커밋)
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   └── budgets.jsonl
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py           # 엔트리포인트: python -m budget_app
│   ├── cli.py                # argparse 서브커맨드 정의 + 대화형 입력(prompt) + 종료 코드
│   ├── services.py           # 유스케이스 조합(TransactionService/BudgetService/CategoryService/PortService)
│   ├── repositories.py       # 파일 I/O + 제너레이터 스트리밍 + 원자적 교체
│   ├── models.py             # dataclass: Transaction / Category / Budget
│   ├── validators.py         # 날짜/금액/타입 검증 (순수 함수, input() 없음)
│   ├── decorators.py         # @handle_errors / @log_call / @timed
│   ├── formatters.py         # 테이블 정렬 출력 (보너스 3)
│   └── errors.py             # 도메인 예외 계층
└── tests/
    ├── test_repositories.py
    ├── test_services.py
    └── test_validators.py
```

**의존 방향은 한 방향으로만**: `cli → services → repositories → models`.
`repositories`는 `services`를 모르고, `models`는 아무것도 모른다. (테스트 용이성 확보)

> 대화형 재입력 루프(`prompt`)는 애초에 `validators.py`에 두려 했으나 `cli.py`로 옮겼다.
> `validators.py`가 "`input()`을 부르지 않는다"는 계약을 지켜야 옵션 방식 `update`와
> CSV `import`가 같은 검증 함수를 재사용할 수 있다. 묻고 보여주는 일은 표현 계층 몫이다.

---

## 2. 데이터 모델 (`models.py`)

```python
@dataclass(frozen=True, slots=True)
class Transaction:
    id: str                      # "TX-000012"
    date: str                    # "YYYY-MM-DD" (문자열 정렬 == 시간순이라 그대로 씀)
    type: Literal["income", "expense"]
    category: str
    amount: int                  # 양수 정수(원 단위)
    memo: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]: ...
    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "Transaction": ...
    @property
    def month(self) -> str:      # "2024-01"
        return self.date[:7]

@dataclass(frozen=True, slots=True)
class Category:
    name: str

@dataclass(frozen=True, slots=True)
class Budget:
    month: str                   # "YYYY-MM"
    amount: int
```

- `frozen=True`: 거래는 불변으로 다루고, `update`는 `dataclasses.replace()`로 새 객체를 만들어 교체 → 부분 수정 중 깨진 상태가 남지 않음.
- **타입 힌트는 전 함수 시그니처에 필수.** 특히 제너레이터 반환은 `Iterator[Transaction]`로 명시해서 "리스트가 아니라 스트림"이라는 계약을 코드로 드러낸다.
- 요약 결과도 `@dataclass MonthlySummary(total_income, total_expense, balance, top_categories, budget, usage_rate)`로 정의해 CLI와 서비스 간 계약을 고정.

### 저장 파일 스키마 (JSONL, UTF-8, 1줄 1레코드)
```jsonl
# transactions.jsonl
{"id":"TX-000012","date":"2024-01-15","type":"expense","category":"food","amount":15000,"memo":"점심","tags":["meal"]}
# categories.jsonl
{"name":"food"}
# budgets.jsonl
{"month":"2024-01","amount":500000}
```

### id 생성 규칙
`TX-` + 6자리 zero-pad. 항상 append하므로 **파일 맨 뒤 레코드가 가장 큰 번호**를 갖는다.
`stream_reversed()`로 뒤에서 한 건만 읽어 +1 한다(10,000건 파일에서 6.8%만 읽음).

주의: 가장 최근 거래를 삭제하면 그 번호가 재사용된다. 남아 있는 거래끼리는 여전히 유일하므로
그대로 둔다. 완전한 단조 증가를 원하면 카운터를 따로 저장해야 하는데 그 복잡도를 살 이득이 없다.

---

## 3. 저장소 계층 (`repositories.py`) — 핵심 난이도

### 3.1 스트리밍 읽기 (미션 5·7번의 필수 요구)
```python
def stream(self) -> Iterator[Transaction]:
    """파일을 한 줄씩 읽어 yield. 전체를 메모리에 올리지 않는다."""
    if not self._path.exists():
        return
    with self._path.open(encoding="utf-8") as fp:
        for lineno, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield Transaction.from_dict(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                # 손상된 한 줄이 전체 조회를 죽이지 않게 경고 후 skip
                log_corrupt_line(self._path, lineno)
```

- 필터는 제너레이터를 다섯 개로 겹치지 않고 **술어 하나 + `filter()`** 로 합쳤다.
  `filter`가 게으르므로 스트리밍은 그대로고, 함수 다섯 개보다 짧다(services.`search_transactions`).
- `--limit N`은 `itertools.islice`로 **N개 확보 후 즉시 중단** (파일 끝까지 읽지 않음).

### 3.2 "최신순" 출력과 스트리밍의 충돌 — 해결 방안
전체 정렬은 본질적으로 전량 적재를 요구한다. 그래서:
- **append-only + 파일 뒤에서부터 역방향 청크 읽기**(`seek`으로 끝에서 64KB씩 거꾸로 읽어 줄 단위 yield)로 `stream_reversed()`를 구현.
- 파일은 항상 시간 도착 순으로 append되므로 역순 스트림이 곧 "최근 입력순". 날짜가 뒤섞인 입력을 정확히 최신순 정렬해야 하는 경우엔 `--limit` 상한만큼만 **힙(`heapq.nlargest(limit, stream(), key=date)`)** 으로 유지 → 메모리 O(limit).
- 이 트레이드오프(역순 스트림 vs 힙 상한)는 README에 명시.

### 3.3 update/delete의 원자적 교체 (미션 6번 + 보너스 4)
```python
def rewrite(self, transform: Callable[[Iterator[T]], Iterator[T]]) -> int:
    """임시 파일에 스트리밍으로 다시 쓰고 os.replace로 원자적 교체."""
    tmp = tempfile.NamedTemporaryFile("w", dir=self._path.parent,
                                      delete=False, encoding="utf-8")
    with tmp:
        for item in transform(self.stream()):
            tmp.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        tmp.flush(); os.fsync(tmp.fileno())
    os.replace(tmp.name, self._path)   # 같은 파일시스템 → 원자적
```
- 실패 시 원본은 손상되지 않고 임시 파일만 남음 → `finally`에서 정리.
- `delete`/`update`/`category remove`(대체 카테고리 적용)가 모두 이 한 메서드를 재사용.

### 3.4 구성 (실제 구현)

처음에는 `JsonlRepository[T]` 제네릭 베이스에 loader를 주입하는 구조로 만들었는데, 파일 3개를
읽으려고 `Generic`/`TypeVar`/`Callable`을 동원하는 게 과해서 걷어냈다. **파일 기계적 처리는 함수,
타입은 얇은 클래스**로 나눈 결과가 더 짧고(79줄 → 52줄) 타입도 더 정확하다.

모듈 함수 (파일 다루는 코드는 한 번만 작성):
- `ensure_file(path)` — 상위 폴더까지 생성
- `read_jsonl(path)` — 앞에서부터 스트리밍
- `read_jsonl_reversed(path, chunk_size)` — 뒤에서부터 청크 단위 스트리밍
- `append_jsonl(path, record)` — 끝에 한 줄 추가 (개행 누락 보충)
- `write_jsonl(path, records)` — 임시 파일 + `os.replace` 원자적 교체
- `parse_line(...)` / `load_models(...)` — 깨진 줄 경고 후 건너뛰기 (양쪽 리더가 공유)
- `warn(message)` — stderr 출력. `logging` 설정이 필요 없어 3줄로 끝냈다

클래스 (정확한 타입 계약만 담당):
- `TransactionRepository` — `stream()` / `stream_reversed()` / `append()` / `replace_all()` / `next_id()`
- `CategoryStore` — `stream()` / `names() -> list[str]` / `append()` / `replace_all()`
- `BudgetStore` — `stream()` / `get(month) -> Budget | None` / `set(month, amount)` / `replace_all()`

`CategoryStore.names()`는 스트리밍하지 않고 리스트를 준다. 카테고리는 수가 적고 중복 확인과
전체 목록 출력이 목적이라 스트리밍할 이유가 없다. `dict.fromkeys()`로 등록 순서를 지키며 중복 제거.

`BudgetStore.set()`은 append가 아니라 전체 재작성이다. 같은 달이 두 줄로 남으면 어느 쪽이
맞는지 알 수 없다. 한 달에 한 줄뿐이라 다시 쓰는 비용이 없고, 월 순 정렬도 함께 얻는다.

---

## 4. 데코레이터 (`decorators.py`, 미션 12번)

3개 구현, `functools.wraps`로 메타데이터 보존, 타입은 `ParamSpec`/`TypeVar`로 유지.

| 데코레이터 | 역할 | 적용 위치 |
| --- | --- | --- |
| `@handle_errors` | 도메인 예외를 잡아 `[오류] 원인` + `[힌트] 해결법`만 출력하고 exit code 1 반환. **스택트레이스 출력 금지**(미션 13번) | `cli.py`의 각 커맨드 핸들러 |
| `@log_call` | 커맨드명·인자·결과를 `logging`으로 기록(기본 WARNING, `--verbose`면 DEBUG) | 서비스 메서드 |
| `@timed` | 실행 시간(ms) 측정, `--verbose`일 때만 출력 | `summary`, `import`, `export` 등 무거운 작업 |

핵심은 "CLI 핸들러 본문에 try/except가 하나도 없는 상태"를 만드는 것 — 관심사 분리를 코드로 증명.

---

## 5. 예외 계층 (`errors.py`) 과 종료 코드 (미션 13번)

> `UnknownCategoryError`는 `ValidationError`를 상속한다. 미등록 카테고리는 사용자가 다시
> 입력하면 해결되는 종류의 오류이고, 미션 4번이 "없으면 안내 후 재입력"을 요구한다.
> 상속시켜 두면 `cli.prompt`가 이미 `ValidationError`를 잡아 되묻기 때문에 추가 코드가 없다.

```python
class BudgetAppError(Exception):
    exit_code = 1
    hint: str = ""
class ValidationError(BudgetAppError): ...          # 날짜/금액/타입 형식 오류
class NotFoundError(BudgetAppError): ...            # 없는 id
class UnknownCategoryError(BudgetAppError): ...     # 미등록 카테고리
class CategoryInUseError(BudgetAppError): ...       # 사용 중 카테고리 삭제
class DataFileError(BudgetAppError): ...            # 권한/손상
```
- 각 예외가 `hint`를 들고 다녀서 출력 문구가 한 곳(데코레이터)에서 일관되게 만들어진다.
- 정상 종료 `sys.exit(0)`, 오류 `sys.exit(e.exit_code)`. `argparse` 사용법 오류는 argparse 기본값 2 유지.
- `KeyboardInterrupt`도 잡아 `[중단]` 메시지 + exit 130.

---

## 6. CLI 설계 (`cli.py`)

> **stdout / stderr 구분 규칙.** 데이터는 stdout, 그 외는 stderr다.
> `list`/`search`/`budget show`의 "없습니다" 안내는 stderr로 보낸다 -
> `list > out.txt` 했을 때 데이터 파일에 문구가 섞이면 안 되기 때문이다.
> 반대로 `summary`는 전부 stdout이다. "데이터 없음"과 초과 경고 자체가
> 리포트의 내용이므로 `summary > report.txt`에 들어가야 맞다.
> 손상된 줄 경고(`repositories.warn`)는 항상 stderr.

`argparse` + `add_subparsers(dest="command", required=True)`. 모든 서브커맨드에 `--help` 자동 제공.

```
python -m budget_app [--data-dir ./data] [--verbose] <command> [options]

add                                          # 대화형 입력 (미션 고정)
list       [--limit N=20]
search     [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--category C] [--type income|expense]
           [--q KEYWORD] [--tag TAG] [--limit N]
summary    --month YYYY-MM [--top N=3]
update     --id ID [--date .. --type .. --category .. --amount .. --memo .. --tags ..]
delete     --id ID
budget     set  --month YYYY-MM --amount N
budget     show [--month YYYY-MM]
category   add [NAME]        # NAME 생략 시 대화형
category   list
category   remove NAME [--replace-with OTHER]
export     --out FILE.csv  (--month YYYY-MM | --from .. --to ..)   # 조건 1개 이상 필수
import     --from FILE.csv [--dry-run]
backup                                       # 보너스 1
```

- `add`만 순수 대화형(`input()`), 나머지는 옵션 방식. `category add`는 인자 생략 시 대화형으로 폴백.
- 대화형 입력은 `validators.prompt_until_valid(label, parse_fn)`로 통일 → 잘못 입력하면 `[오류]/[힌트]` 출력 후 **같은 항목 재입력**(미션 결과 예시와 동일한 UX).
- 각 핸들러는 `(args, container) -> int` 시그니처로 통일하고, 실제 로직은 서비스 호출 + 포매터 출력 2줄만 남긴다.

---

## 7. 서비스 계층 (`services.py`)

- `CategoryService`: `list_names()`, `add(name)`(중복/공백 검증), `remove(name, replace_with)` — 사용 중이면 `--replace-with` 없을 때 `CategoryInUseError`, 있으면 `rewrite`로 일괄 치환 후 삭제.
- `TransactionService`: `add(...)`(카테고리 존재 검증 → `next_id()` → `append`), `recent(limit)`, `search(criteria)`, `update(id, patch)`(없으면 `NotFoundError`, 필드 개별 재검증), `delete(id)`.
  - `SearchCriteria` dataclass로 검색 조건을 캡슐화해 CLI ↔ 서비스 계약을 타입으로 고정.
- `BudgetService`: `set(month, amount)`, `get(month)`, `evaluate(month, expense_total) -> BudgetStatus(usage_rate, over)`.
- `SummaryService`: 해당 월 거래를 **한 번의 스트리밍 패스**로 훑어 수입/지출 합계 + `Counter`로 카테고리별 지출 집계 → `most_common(top)`. 거래 0건이면 `MonthlySummary(empty=True)`로 "데이터 없음" 표시. 예산이 있으면 사용률/초과 경고 결합.
- `PortService`: CSV import/export.
  - CSV 스키마 고정: `date,type,category,amount,memo,tags` (UTF-8, 헤더 포함, tags는 쉼표 구분 → 필드 자체를 큰따옴표로 감쌈).
  - `import`: 행 단위 검증, 실패 행은 이유와 함께 집계해 `imported=N, skipped=M` 출력. 성공 행만 append(부분 성공 허용). `--dry-run`으로 검증만.
  - `export`: `--month` 또는 `--from/--to` 중 하나 이상 없으면 `ValidationError`. `csv.DictWriter`로 스트리밍 기록 후 건수 출력.

---

## 8. 출력 포맷 (`formatters.py`, 보너스 3)

- `format_table(rows, headers)`: 각 열 최대 폭을 계산해 `str.ljust/rjust`로 정렬. 금액은 우측 정렬 + `f"{amount:,}"` 천단위 구분.
- 한글 폭 보정: `unicodedata.east_asian_width`가 `W`/`F`인 문자를 2칸으로 계산하는 `display_width()` 헬퍼 — 메모에 한글이 섞여도 열이 안 밀린다.
- 미션 결과 예시(`TX-000012 | 2024-01-15 | expense | food | 15000 | 점심`)의 파이프 구분 형태를 기본으로, `summary`는 블록 형태로 별도 포맷.

---

## 9. 구현 순서

작업 단위는 **한 파일 안의 논리 단위 하나**(대략 40~80줄, 검증 명령 1~2개)로 잡고,
매 단위마다 리뷰와 커밋을 받는다. 여러 파일을 한 번에 내면 검증할 게 너무 많아진다.

### 순서를 바꾼 이유

원래 계획은 "데코레이터 + 검증기"를 3단계에 두고 명령 구현을 그 뒤로 미뤘다. 그런데
`@handle_errors`는 **각 명령 핸들러를 감싸는** 장치다. 핸들러를 먼저 11개 만들면 나중에
전부 되돌아가 손봐야 한다. 그래서 데코레이터를 명령 구현보다 **앞으로** 당긴다.

`category`를 첫 명령으로 두는 이유는 `add`가 등록된 카테고리 목록을 검증해야 하므로
`category`가 선행 조건이고, 둘 중 더 작기 때문이다.

### 완료 (Done)

| # | 작업 | 산출물 |
| --- | --- | --- |
| 1 | 패키지 뼈대 + 예외 계층 + 데이터 모델 | `errors.py`, `models.py`, `cli.py` 파서 골격 |
| 2 | JSONL 스트리밍 읽기 | `read_jsonl`, `TransactionRepository.stream` |
| 3 | 손상된 줄 건너뛰기 + 경고 | `parse_line`, `warn` |
| 4 | append 저장 | `append_jsonl`, `.append()` |
| 5 | 원자적 전체 재작성 | `write_jsonl`, `.replace_all()` |
| 6 | 역방향 청크 읽기 (최신순) | `read_jsonl_reversed`, `.stream_reversed()` |
| 7 | 다음 id 할당 | `.next_id()` |
| 8 | 카테고리 저장소 | `CategoryStore` |
| 9 | 예산 저장소 (월별 upsert) | `BudgetStore` |
| 10 | 순수 입력 검증 함수 | `validators.py` |
| 11 | 대화형 재입력 루프 | `cli.prompt` |
| 12 | 디스패치 연결 (`--data-dir` → 저장소 묶음) | `Stores`, `open_stores`, `HANDLERS` |
| 13 | 오류 처리 데코레이터 | `decorators.py` (`@handle_errors`, `print_error`) |
| 14 | `category add` / `list` + 기본 카테고리 시딩 | `services.py`, `cli.handle_category` |
| 15 | `category remove` (차단 / `--replace-with` 치환) | `resolve_category`, `remove_category` |
| 16 | `add` (대화형 거래 입력) | `add_transaction`, `cli.handle_add` |
| 17 | `list --limit` (최근 입력순 스트리밍) | `recent_transactions`, `cli.handle_list` |
| 18 | `search` (조건 5종 + `--limit`) | `search_transactions`, `cli.handle_search` |
| 19 | `delete --id` | `delete_transaction`, `cli.handle_delete` |
| 20 | `update --id` (옵션 기반, 항목별 재검증) | `update_transaction`, `cli.handle_update` |
| 21 | `budget set` / `show` | `set_budget`, `get_budget`, `list_budgets` |
| 22 | `summary --month --top` + 예산 사용률/초과 경고 | `MonthlySummary`, `summarize_month`, `cli.handle_summary` |

여기까지로 **저장소·검증 계층이 완성**되고 **`category` 전체, `add`, `list`, `search`, `delete`, `update`, `budget`, `summary`가 동작**한다.
미션 최종 결과물 10가지 중 **8가지**(1·2·3·4·5·6·7·8번)가 끝났다.
남은 것은 9번(import/export)과 10번(README)뿐이다. 미션 요구 중
스트리밍(5·7번), 원자성(6번), dataclass 모델(2번), 3파일 분리(3번), 모듈화(14번),
데코레이터(12번), 종료 코드(13번)가 충족된다.

`@log_call` / `@timed`는 만들지 않았다. 미션 12번은 "1개 이상"이고 `@handle_errors`가
실제 일을 하며 그것을 충족한다. 나머지 둘은 `--verbose`에서만 출력되고 아직 요구하는
호출자가 없다. 시간 측정이 의미를 갖는 `summary`/`import` 단계에서 다시 판단한다.

### 남은 작업 (To do)

| # | 작업 | 왜 이 순서인가 | 검증 |
| --- | --- | --- | --- |
| 23 | `export --out` (CSV) | | 조건 없이 실행하면 오류 |
| 24 | `import --from` (CSV) | export가 만든 파일로 검증 | 왕복 건수 일치 |
| 25 | `README.md` | | 실행법/파일 위치/명령 예시/CSV 스키마 |

### 보너스 (선택)

| # | 작업 |
| --- | --- |
| 26 | `formatters.py` 테이블 정렬 (한글 폭 보정 포함) |
| 27 | `backup` 명령 |
| 28 | 반복 내역 기능 |
| 29 | `tests/` 단위 테스트 |

원자성 강화(보너스 4)는 5단계에서 이미 완료됐다.

---

## 10. 테스트 전략

- `unittest` + `tempfile.TemporaryDirectory()`로 매 테스트마다 격리된 `data-dir` 사용 → 실제 파일 I/O를 그대로 검증(모킹 최소화).
- 스트리밍 검증: 제너레이터를 리스트로 소비하지 않고 `next()`를 2번만 호출한 뒤 파일 읽은 바이트 수를 확인하는 방식으로 "전량 로드하지 않음"을 실제로 증명.
- 실행: `python3.12 -m unittest discover -s tests`

## 11. 리스크 / 주의점

1. **"스트리밍" + "최신순"** — 3.2절의 트레이드오프를 README에 반드시 설명. 채점 포인트 중 하나(과제 목표 3번).
   `stream_reversed()`는 **기록 순서의 역순**이지 날짜 순이 아니다. 과거 날짜를 나중에 입력하면
   목록 맨 위에 뜬다. 날짜순을 엄격히 원하면 `heapq.nlargest(limit, stream(), key=date)`가 필요하고
   이때 메모리는 O(limit), 파일은 전량 읽는다. **`list`는 기록 역순으로 간다** (미션의 스트리밍 요구에 맞음).
2. **원자적 교체는 같은 파일시스템에서만 원자적** — 임시 파일을 반드시 `data-dir` 안에 생성.
3. **CSV의 tags 필드** — 쉼표 구분 문자열이 CSV 구분자와 충돌. `csv` 모듈이 자동 인용 처리하므로 직접 문자열 조립 금지.
4. **인터프리터** — 실행/검증은 `python3.12`로 한다. 현재 PATH에서는 `python3`도 3.12를 가리키지만,
   `/usr/bin/python3`는 여전히 3.9.6이고 거기서는 `slots=True`가 즉시 실패한다.
5. **금액은 int(원 단위)** 로 고정 — float 누적 오차 회피. `parse_amount`는 현재 소수 입력을 거부한다.
   CSV import에서 `"15000.0"`을 받아야 하면 그때 소수부 0인 경우만 허용하도록 넓힌다(호출자가 생길 때).
6. **데코레이터 누락 주의** — 미션 12번은 채점 요구사항이다. 13단계에서 반드시 만들고 실제로 적용한다.
7. **최신 거래 삭제 시 id 재사용** — 2절 참고. 남은 거래끼리는 유일하지만, 과거 export CSV의 id가
   다른 거래를 가리킬 수 있다. README에 명시한다.
