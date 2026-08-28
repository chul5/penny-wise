# budget_app — 콘솔 가계부

수입/지출 내역을 파일에 영구 저장하고, 검색·월별 요약·예산 관리·CSV 입출력까지
지원하는 콘솔 프로그램입니다. **표준 라이브러리만** 사용합니다(설치할 패키지 없음).

## 실행 방법

Python **3.10 이상**이 필요합니다.

```bash
cd penny-wise
python3.12 -m budget_app --help          # 전체 명령 목록
python3.12 -m budget_app <command> --help  # 명령별 사용법
```

> `python3`가 3.10 미만을 가리키는 환경이 있어 문서에서는 `python3.12`로 적었습니다.
> `python3 --version`이 3.10 이상이면 `python3 -m budget_app ...` 로 실행해도 됩니다.

### 전역 옵션

| 옵션 | 설명 |
| --- | --- |
| `--data-dir PATH` | 저장 폴더 (기본 `./data`) |
| `--verbose` | 예상하지 못한 오류가 났을 때 상세 내용까지 출력 |
| `--version` | 버전 출력 |
| `--help` | 사용법 출력 |

전역 옵션은 **명령보다 앞**에 와야 합니다.

```bash
python3.12 -m budget_app --data-dir ./mydata list   # OK
python3.12 -m budget_app list --data-dir ./mydata   # 오류
```

## 저장 파일 위치와 형식

기본 저장 폴더는 `./data`이며 `--data-dir`로 바꿀 수 있습니다. 형식은 **JSONL**로,
한 줄이 레코드 하나입니다(UTF-8, 한글은 그대로 저장되어 눈으로 읽을 수 있습니다).

```
data/
├── transactions.jsonl   # 거래 내역
├── categories.jsonl     # 카테고리 목록
└── budgets.jsonl        # 월 예산
```

파일은 **필요할 때 자동 생성**됩니다. 처음 실행할 때 따로 준비할 것이 없고,
조회만 하는 명령은 파일을 만들지 않습니다. 카테고리 파일이 비어 있으면
기본 카테고리(`food` `transport` `rent` `salary` `etc`)가 자동으로 채워집니다.

```jsonl
# transactions.jsonl
{"id": "TX-000003", "date": "2024-01-15", "type": "expense", "category": "food", "amount": 15000, "memo": "점심", "tags": ["meal"]}
# categories.jsonl
{"name": "food"}
# budgets.jsonl
{"month": "2024-01", "amount": 500000}
```

| 필드 | 설명 |
| --- | --- |
| `id` | `TX-` + 6자리 일련번호 |
| `date` | `YYYY-MM-DD` |
| `type` | `income` / `expense` |
| `category` | 등록된 카테고리 이름 |
| `amount` | 양수 정수(원). 소수점을 쓰지 않아 반올림 오차가 없습니다 |
| `memo` | 선택 |
| `tags` | 선택, 문자열 배열 |

## 주요 명령 예시

아래 출력은 모두 실제 실행 결과입니다.

### 거래 추가 (대화형)

```
$ python3.12 -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000003
```

잘못 입력하면 그 항목만 다시 묻습니다.

```
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
날짜(YYYY-MM-DD):
```

입력값은 정규화됩니다. `2024-1-5` → `2024-01-05`, `EXPENSE` → `expense`,
`15,000` → `15000`, 태그 `meal, meal, 식사` → `meal, 식사`.

### 목록 조회

```
$ python3.12 -m budget_app list --limit 3
TX-000005 | 2024-01-20 | expense | food | 30000 | 저녁 외식
TX-000004 | 2024-01-01 | expense | rent | 150000 | 월세
TX-000003 | 2024-01-15 | expense | food | 15000 | 점심
```

`--limit` 기본값은 20입니다. 정렬 기준은 **입력한 순서의 역순**입니다(아래 "알아두면 좋은 점" 참고).

### 검색

```
$ python3.12 -m budget_app search --category food --tag meal
TX-000005 | 2024-01-20 | expense | food | 30000 | 저녁 외식
TX-000003 | 2024-01-15 | expense | food | 15000 | 점심
```

| 옵션 | 설명 |
| --- | --- |
| `--from` / `--to` | 기간 (양끝 포함) |
| `--category` | 카테고리 |
| `--type` | `income` / `expense` |
| `--q` | 메모 키워드 (부분 일치, 대소문자 무시) |
| `--tag` | 태그 |
| `--limit` | 출력 건수 (기본 20) |

### 예산 + 월별 요약

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

예산을 넘기면 경고가 함께 나옵니다.

```
예산: 100000원 (사용률 215.0%)
[경고] 예산을 115000원 초과했습니다.
```

거래가 없는 달은 이렇게 출력합니다.

```
$ python3.12 -m budget_app summary --month 2024-09
2024-09 데이터 없음
```

`budget show`로 저장된 예산을 확인할 수 있습니다(`--month` 생략 시 전체).

### 수정 / 삭제

`update`는 **옵션 방식**으로 고정되어 있습니다. 지정한 항목만 바뀝니다.

```
$ python3.12 -m budget_app update --id TX-000005 --amount 25000
[수정 완료] id=TX-000005
TX-000005 | 2024-01-20 | expense | food | 25000 | 저녁 외식

$ python3.12 -m budget_app delete --id TX-000005
[삭제 완료] id=TX-000005
```

`--memo ""` 처럼 빈 문자열을 주면 그 항목을 비웁니다. 없는 id는 오류로 처리하고
종료 코드 1을 돌려주며, 파일은 전혀 건드리지 않습니다.

### 카테고리 관리

```
$ python3.12 -m budget_app category list
- food
- transport
- rent
- salary
- etc

$ python3.12 -m budget_app category add 경조사비
[저장 완료] category=경조사비
```

사용 중인 카테고리는 그냥 지울 수 없습니다. 지우려면 대체 카테고리를 지정합니다.

```
$ python3.12 -m budget_app category remove food
[오류] 'food' 카테고리를 사용하는 거래가 1건 있습니다.
[힌트] --replace-with <다른카테고리> 로 대체 카테고리를 지정하세요.

$ python3.12 -m budget_app category remove food --replace-with etc
[삭제 완료] category=food (거래 1건을 etc로 옮겼습니다)
```

### 내보내기 / 가져오기

```
$ python3.12 -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (4 records)

$ python3.12 -m budget_app import --from export.csv
[완료] imported=4, skipped=0
```

`export`는 `--month` 또는 `--from`/`--to` 중 **하나 이상을 반드시** 받습니다.
`import`는 잘못된 행만 건너뛰고 나머지는 저장하며, 건너뛴 이유를 줄 번호와 함께 알려줍니다.

```
$ python3.12 -m budget_app import --from mixed.csv
[건너뜀] 3행: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[건너뜀] 5행: 등록되지 않은 카테고리입니다: ghost
[완료] imported=2, skipped=2
```

`--dry-run`을 주면 검증만 하고 저장하지 않습니다.

## import / export CSV 스키마

UTF-8, 헤더 포함, 칸 순서 고정입니다.

| column | 필수 | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

```csv
date,type,category,amount,memo,tags
2024-01-01,expense,rent,150000,월세,fixed
2024-01-15,expense,food,15000,"점심, 김치찌개","meal,work"
```

- `id`는 스키마에 없습니다. `import`할 때 새로 발급합니다.
- 값에 쉼표나 큰따옴표가 있으면 CSV 규칙대로 인용됩니다. `csv` 모듈로 읽고 쓰므로
  `export` → `import` 왕복에서 값이 그대로 보존됩니다.
- 줄바꿈은 CSV 표준(RFC 4180)인 CRLF입니다. 읽을 때는 CRLF/LF 모두 처리합니다.

## 종료 코드

| 코드 | 의미 |
| --- | --- |
| 0 | 성공 |
| 1 | 입력값 오류, 없는 데이터 등 |
| 2 | 파일 접근 실패, 잘못된 명령 사용법(argparse) |
| 130 | 사용자가 Ctrl+C로 중단 |

오류는 스택트레이스 대신 원인과 해결 힌트로 출력합니다.

```
$ python3.12 -m budget_app delete --id TX-999999
[오류] id=TX-999999 거래를 찾을 수 없습니다.
[힌트] list 명령으로 존재하는 id를 확인해 보세요.
```

데이터는 stdout, 안내·경고·오류는 stderr로 나갑니다. 그래서
`list > out.txt` 하면 파일에는 거래만 들어갑니다. 다만 `summary`는 "데이터 없음"과
예산 초과 경고까지 리포트의 내용이므로 전부 stdout으로 보냅니다.

## 알아두면 좋은 점

- **정렬 기준은 날짜가 아니라 입력 순서입니다.** 파일 끝에서부터 거꾸로 읽어
  `--limit`만큼만 읽고 멈추기 때문입니다(1만 건 파일에서 최근 3건 조회 시 약 7%만 읽습니다).
  과거 날짜를 나중에 입력하면 목록 위쪽에 나타납니다.
- **가장 최근 거래를 지우면 그 번호가 재사용됩니다.** 남아 있는 거래끼리는 항상
  고유하지만, 예전에 내보낸 CSV의 id가 다른 거래를 가리킬 수 있습니다.
- **깨진 줄은 건너뛰고 경고만 남깁니다.** 한 줄이 손상돼도 나머지는 계속 읽을 수 있습니다.
  다만 `update`/`delete`/`category remove`는 파일을 다시 쓰므로, 그 시점에 깨진 줄이
  사라집니다. 중요한 데이터는 미리 복사해 두세요.
- **저장은 임시 파일에 쓴 뒤 교체하는 방식**이라, 쓰는 도중 중단돼도 원본이
  반쯤 망가지지 않습니다.

## 프로젝트 구조

```
budget_app/
├── cli.py           # argparse 정의, 대화형 입력, 명령 디스패치
├── services.py      # 유스케이스와 규칙 (중복 금지, 사용 중 카테고리 보호 등)
├── repositories.py  # JSONL 파일 입출력, 제너레이터 스트리밍, 원자적 교체
├── models.py        # Transaction / Category / Budget / 요약·가져오기 결과
├── validators.py    # 입력 검증 (순수 함수)
├── decorators.py    # @handle_errors — 예외를 메시지와 종료 코드로
└── errors.py        # 도메인 예외 (각자 힌트와 종료 코드를 가짐)
```

의존 방향은 `cli → services → repositories → models` 한 방향입니다.
설계 배경과 선택 이유는 [docs/plan.md](docs/plan.md), 과제 명세는
[docs/mission.md](docs/mission.md)에 있습니다.
