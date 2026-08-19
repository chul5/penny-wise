# 구현 계획 (plan.md)

`docs/mission.md`의 콘솔 가계부(`budget_app`)를 어떤 구조로, 어떤 순서로 구현할지 정리한 문서.

---

## 0. 선행 조건 / 확정 결정 사항

### 환경
- 미션 요구: **Python 3.10 이상**. 현재 머신의 `python3`는 **3.9.6** 뿐이므로 먼저 3.10+ 설치 필요.
  - 예: `brew install python@3.12` → 이후 모든 실행은 `python3.12 -m budget_app ...`
  - **코드는 3.9에서도 실행되도록 작성**한다(`from __future__ import annotations` + `dataclass(slots=True)` 미사용).
    각 단계를 현재 머신에서 바로 스모크 테스트할 수 있어야 하기 때문. 문서상 지원 버전은 3.10+로 표기.
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
│   ├── cli.py                # argparse 서브커맨드 정의 + 대화형 입력 + 종료 코드
│   ├── services.py           # 유스케이스 조합(TransactionService/BudgetService/CategoryService/PortService)
│   ├── repositories.py       # 파일 I/O + 제너레이터 스트리밍 + 원자적 교체
│   ├── models.py             # dataclass: Transaction / Category / Budget
│   ├── validators.py         # 날짜/금액/타입/카테고리 검증 + 대화형 재입력 루프
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

---

## 2. 데이터 모델 (`models.py`)

```python
@dataclass(frozen=True)
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

@dataclass(frozen=True)
class Category:
    name: str

@dataclass(frozen=True)
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
`TX-` + 6자리 zero-pad. 마지막 줄 기준 최대 seq를 스트리밍으로 한 번 훑어 구함(파일 전체 로드 없음). 동일 파일에 대해 append 직전에 계산.

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

- 필터도 제너레이터 체인으로: `stream() → filter_by_period() → filter_by_category() → ...` 각각 `Iterator[Transaction]`을 받아 `Iterator[Transaction]`을 반환.
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

### 3.4 클래스 구성
- `JsonlRepository[T]` (제네릭 베이스: `stream` / `stream_reversed` / `append` / `rewrite` / `ensure_file`)
- `TransactionRepository(JsonlRepository[Transaction])` — `next_id()`, 필터 제너레이터
- `CategoryStore(JsonlRepository[Category])` — `names() -> set[str]`, 기본 카테고리 시딩
- `BudgetStore(JsonlRepository[Budget])` — `get(month)`, `upsert(month, amount)`

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

## 9. 구현 순서 (커밋 단위)

| # | 작업 | 산출물 | 검증 |
| --- | --- | --- | --- |
| 1 | 뼈대 + 모델 | `models.py`, `errors.py`, 패키지 스캐폴딩 | `python -m budget_app --help` 동작 |
| 2 | 저장소 (스트리밍/append/원자적 rewrite) | `repositories.py` | `tests/test_repositories.py`: 손상 줄 skip, `rewrite` 원자성, `stream_reversed` |
| 3 | 데코레이터 + 검증기 | `decorators.py`, `validators.py` | 잘못된 날짜/금액에서 스택트레이스 없이 종료코드 1 |
| 4 | category (add/list/remove) + 기본 시딩 | `services.py` 일부, CLI | 사용 중 카테고리 삭제 차단 / `--replace-with` 치환 |
| 5 | add + list (`--limit`, 스트리밍) | | 미션 8절 예시와 동일한 출력 |
| 6 | search (5개 조건 조합) | | 조건 교차 케이스 테스트 |
| 7 | update / delete (rewrite 재사용) | | 없는 id → `[오류]` + exit 1 |
| 8 | budget set/show + summary(예산 사용률/초과 경고) | | 데이터 없는 달 "데이터 없음", 초과 시 경고 |
| 9 | import / export CSV | `formatters.py` 포함 | export → import 왕복(round-trip) 건수 일치 |
| 10 | README.md | | 실행법/파일 위치/명령 예시/CSV 스키마 4항목 포함 |
| 11 | 보너스: backup, 반복 내역, 테이블 정렬, (원자성은 2단계에 이미 포함) | | |

---

## 10. 테스트 전략

- `unittest` + `tempfile.TemporaryDirectory()`로 매 테스트마다 격리된 `data-dir` 사용 → 실제 파일 I/O를 그대로 검증(모킹 최소화).
- 스트리밍 검증: 제너레이터를 리스트로 소비하지 않고 `next()`를 2번만 호출한 뒤 파일 읽은 바이트 수를 확인하는 방식으로 "전량 로드하지 않음"을 실제로 증명.
- 실행: `python3.12 -m unittest discover -s tests`

## 11. 리스크 / 주의점

1. **"스트리밍" + "최신순"** — 3.2절의 트레이드오프를 README에 반드시 설명. 채점 포인트 중 하나(과제 목표 3번).
2. **원자적 교체는 같은 파일시스템에서만 원자적** — 임시 파일을 반드시 `data-dir` 안에 생성.
3. **CSV의 tags 필드** — 쉼표 구분 문자열이 CSV 구분자와 충돌. `csv` 모듈이 자동 인용 처리하므로 직접 문자열 조립 금지.
4. **Python 3.9 환경** — 제출/문서 기준은 3.10+지만, 개발 중 검증을 위해 3.9 호환 문법을 유지한다(0절 참고).
5. **금액은 int(원 단위)** 로 고정 — float 누적 오차 회피. import 시 `"15000.0"` 같은 입력은 소수부 0일 때만 허용.
