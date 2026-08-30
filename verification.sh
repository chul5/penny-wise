#!/usr/bin/env bash
#
# ANSWER.md 에 적어둔 주장 중 "실행하면 확인되는 것"을 한 번에 검증한다.
#
#   ./verification.sh           기능 검증만 (수 초)
#   ./verification.sh --bench   10만 건 성능 측정까지 (수십 초)
#
# 모든 검증은 임시 디렉터리에서 이뤄지므로 ./data 는 건드리지 않는다.

set -uo pipefail
cd "$(dirname "$0")" || exit 2

PY=${PY:-python3.12}
BENCH=0
[ "${1:-}" = "--bench" ] && BENCH=1

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
OUTF="$WORK/.checkout"

if [ -t 1 ]; then G=$'\033[32m'; R=$'\033[31m'; B=$'\033[1m'; Y=$'\033[33m'; N=$'\033[0m'
else G=; R=; B=; Y=; N=; fi

PASS=0; FAIL=0

sect() { printf '\n%s%s%s\n' "$B" "$1" "$N"; }
ok()   { PASS=$((PASS+1)); printf '  %sPASS%s  %s\n' "$G" "$N" "$1"; }
ng()   { FAIL=$((FAIL+1)); printf '  %sFAIL%s  %s\n' "$R" "$N" "$1"
         printf '          기대: %s\n          실제: %s\n' "$2" "$(printf '%s' "$3" | head -3 | tr '\n' ' ')"; }
info() { printf '  %sINFO%s  %-44s %s\n' "$Y" "$N" "$1" "$2"; }

# has "설명" "포함되어야 할 문자열" "실제 출력"
has() { case "$3" in *"$2"*) ok "$1";; *) ng "$1" "'$2' 포함" "$3";; esac; }
# hasnt "설명" "없어야 할 문자열" "실제 출력"
hasnt() { case "$3" in *"$2"*) ng "$1" "'$2' 없음" "$3";; *) ok "$1";; esac; }
# eq "설명" 기대 실제
eq() { if [ "$2" = "$3" ]; then ok "$1"; else ng "$1" "$2" "$3"; fi; }

# 파이썬으로 하는 검증. 표준입력으로 코드를 받고, 코드는 PASS|설명 / FAIL|설명|기대|실제 /
# INFO|설명|값 을 한 줄씩 출력한다.
pycheck() {
    if ! $PY - >"$OUTF" 2>"$WORK/.err"; then
        ng "파이썬 검증 블록 실행" "정상 종료" "$(tail -3 "$WORK/.err")"; return
    fi
    while IFS='|' read -r st desc exp act; do
        [ -z "${st:-}" ] && continue
        case "$st" in
            PASS) ok "$desc" ;;
            FAIL) ng "$desc" "$exp" "$act" ;;
            INFO) info "$desc" "$exp" ;;
        esac
    done < "$OUTF"
}

PYHELP='
import sys
def check(desc, expected, actual):
    print("PASS|" + desc if expected == actual else "FAIL|%s|%s|%s" % (desc, expected, actual))
def info(desc, value):
    print("INFO|%s|%s" % (desc, value))
'

D="$WORK/data"
app() { $PY -m budget_app --data-dir "$D" "$@"; }

printf '%s검증 대상:%s ANSWER.md 항목 1~5 중 실행으로 확인되는 것\n' "$B" "$N"
printf '%s실행 환경:%s %s / 임시 데이터 %s\n' "$B" "$N" "$($PY -V)" "$D"

# ---------------------------------------------------------------- 항목 1-1
sect "항목 1-1  10개 명령이 등록되어 있는가"
help_out=$($PY -m budget_app --help 2>&1)
missing=""
for c in add list search summary update delete budget category export import; do
    case "$help_out" in *"    $c "*) ;; *) missing="$missing $c";; esac
done
eq "add/list/search/summary/update/delete/budget/category/export/import 등록" "" "$missing"

# ---------------------------------------------------------------- 항목 1-2
sect "항목 1-2  재실행 후에도 데이터가 유지되는가 (저장 파일 3개)"
printf '2024-01-15\nexpense\nfood\n15,000\n점심\n회사\n' | app add >/dev/null 2>&1
app budget set --month 2024-01 --amount 500000 >/dev/null
app category add 경조사비 >/dev/null
# --- 여기까지가 한 프로세스. 아래는 전부 새 프로세스 ---
eq "transactions.jsonl 생성" "yes" "$([ -f "$D/transactions.jsonl" ] && echo yes || echo no)"
eq "categories.jsonl 생성"   "yes" "$([ -f "$D/categories.jsonl" ] && echo yes || echo no)"
eq "budgets.jsonl 생성"      "yes" "$([ -f "$D/budgets.jsonl" ] && echo yes || echo no)"
has "새 프로세스에서 거래가 그대로 읽힘" "TX-000001 | 2024-01-15 | expense | food | 15000 | 점심" "$(app list 2>&1)"
has "새 프로세스에서 예산이 그대로 읽힘" "2024-01: 500000원" "$(app budget show 2>&1)"
has "새 프로세스에서 카테고리가 그대로 읽힘" "경조사비" "$(app category list 2>&1)"
has "금액 '15,000' 이 15000 으로 정규화됨" "| 15000 |" "$(app list 2>&1)"

# ---------------------------------------------------------------- 항목 1-1 출력 형식
sect "항목 1-1  출력 형식 (income 을 7칸으로 맞춰 구분선 정렬)"
printf '2024-01-25\nincome\nsalary\n3000000\n월급\n\n' | app add >/dev/null 2>&1
has "income 뒤에 공백 1칸이 붙어 expense 와 폭이 같음" "| income  | salary |" "$(app list 2>&1)"

# ---------------------------------------------------------------- 항목 1-3
sect "항목 1-3  category add / list / remove"
has "중복 카테고리 거부" "이미 있는 카테고리" "$(app category add food 2>&1)"
has "대소문자만 다른 중복도 거부 (FOOD)" "이미 있는 카테고리" "$(app category add FOOD 2>&1)"
has "사용 중인 카테고리는 삭제 차단" "거래가 1건 있습니다" "$(app category remove food 2>&1)"
has "차단 시 --replace-with 힌트 제공" "--replace-with" "$(app category remove food 2>&1)"
has "--replace-with 로 거래를 옮기고 삭제" "etc로 옮겼습니다" "$(app category remove food --replace-with etc 2>&1)"
has "옮겨진 거래의 카테고리가 etc 로 바뀜" "| etc |" "$(app list 2>&1)"
hasnt "목록에서 food 가 사라짐" "- food" "$(app category list 2>&1)"
app category add food >/dev/null

# ---------------------------------------------------------------- 항목 1-4
sect "항목 1-4  budget set 저장 + summary 사용률 / 초과 경고"
sum_out=$(app summary --month 2024-01 --top 3 2>&1)
has "총 수입 출력"   "총 수입: 3000000원" "$sum_out"
has "총 지출 출력"   "총 지출: 15000원"   "$sum_out"
has "잔액 출력"      "잔액: 2985000원"    "$sum_out"
has "예산/사용률 출력" "예산: 500000원 (사용률 3.0%)" "$sum_out"
has "카테고리별 지출 TOP 출력" "1) etc 15000원" "$sum_out"
app budget set --month 2024-01 --amount 10000 >/dev/null
over_out=$(app summary --month 2024-01 2>&1)
has "예산 초과 시 경고와 초과 금액 출력" "[경고] 예산을 5000원 초과했습니다." "$over_out"
eq "같은 달 재설정 시 줄이 늘지 않고 교체됨" "1" "$(grep -c '2024-01' "$D/budgets.jsonl")"
has "거래가 없는 달은 '데이터 없음'" "2024-09 데이터 없음" "$(app summary --month 2024-09 2>&1)"
app budget set --month 2024-01 --amount 500000 >/dev/null

# ---------------------------------------------------------------- 항목 1-5
sect "항목 1-5  CSV 스키마 / 왕복 보존"
app export --out "$WORK/round.csv" --month 2024-01 >/dev/null
eq "헤더가 미션 스키마와 일치" "date,type,category,amount,memo,tags" "$(head -1 "$WORK/round.csv" | tr -d '\r')"
eq "UTF-8 BOM 없음" "0" "$(head -c 3 "$WORK/round.csv" | grep -c $'\xef\xbb\xbf')"
has "export 는 조건 없이 실행하면 실패" "--month 또는 --from/--to" "$(app export --out "$WORK/x.csv" 2>&1)"
eq "조건 없는 export 는 파일을 만들지 않음" "no" "$([ -f "$WORK/x.csv" ] && echo yes || echo no)"

D2="$WORK/data2"
printf 'date,type,category,amount,memo,tags\n2024-02-01,expense,food,15000,"점심, 김치찌개 ""특""","meal,work"\n' > "$WORK/tricky.csv"
$PY -m budget_app --data-dir "$D2" import --from "$WORK/tricky.csv" >/dev/null 2>&1
$PY -m budget_app --data-dir "$D2" export --out "$WORK/tricky-out.csv" --month 2024-02 >/dev/null
D3="$WORK/data3"
$PY -m budget_app --data-dir "$D3" import --from "$WORK/tricky-out.csv" >/dev/null 2>&1
export BW_D2="$D2" BW_D3="$D3"
pycheck <<PY
$PYHELP
import json, os
def one(d):
    with open(os.path.join(d, "transactions.jsonl"), encoding="utf-8") as fp:
        r = json.loads(fp.readline())
    return r["memo"], r["tags"]
before, after = one(os.environ["BW_D2"]), one(os.environ["BW_D3"])
check("CSV 왕복 후 memo 의 쉼표/큰따옴표 보존", before[0], after[0])
check("CSV 왕복 후 tags 보존", before[1], after[1])
check("memo 원문이 그대로인지", '점심, 김치찌개 "특"', after[0])
PY

# ---------------------------------------------------------------- 항목 1-6
sect "항목 1-6  스택트레이스 없이 [오류] + [힌트]"
err_out=$(app delete --id TX-999999 2>&1)
hasnt "없는 id 삭제 - 스택트레이스 없음" "Traceback" "$err_out"
has   "없는 id 삭제 - [오류] 출력" "[오류]" "$err_out"
has   "없는 id 삭제 - [힌트] 출력" "[힌트]" "$err_out"
err_out=$(app import --from "$WORK/없는파일.csv" 2>&1)
hasnt "없는 CSV - 스택트레이스 없음" "Traceback" "$err_out"
has   "없는 CSV - 원인과 힌트 출력" "[힌트] --from 경로를 확인하세요." "$err_out"
err_out=$(printf '2024-13-99\n2024-02-30\n2024-01-05\nexpense\netc\n1000\n\n\n' | app add 2>&1)
has   "잘못된 날짜는 되물어서 복구 (2024-13-99, 2월30일 거부)" "[오류] 날짜 형식이 올바르지 않습니다" "$err_out"
has   "재입력 후 정상 저장" "[저장 완료]" "$err_out"
eq    "[오류] 문구를 만드는 코드가 전체에서 한 군데" "1" "$(grep -rc 'print(f"\[오류\]' budget_app/*.py | grep -v ':0' | wc -l | tr -d ' ')"

# 예상하지 못한 오류에도 스택트레이스를 감추고, --verbose 일 때만 연다
BAD="$WORK/broken"; mkdir -p "$BAD"; printf '123\n' > "$BAD/transactions.jsonl"
plain=$($PY -m budget_app --data-dir "$BAD" list 2>&1)
verbo=$($PY -m budget_app --data-dir "$BAD" --verbose list 2>&1)
hasnt "예상 못 한 오류 - 기본은 스택트레이스 숨김" "Traceback" "$plain"
has   "예상 못 한 오류 - 원인과 --verbose 안내" "--verbose 로 다시 실행하면" "$plain"
has   "--verbose 를 주면 스택트레이스 공개" "Traceback" "$verbo"

# ---------------------------------------------------------------- 항목 1-7
sect "항목 1-7  종료 코드"
app category list >/dev/null 2>&1;                    eq "성공 → 0"                 "0" "$?"
app delete --id TX-999999 >/dev/null 2>&1;            eq "없는 데이터 → 1"          "1" "$?"
app category add food >/dev/null 2>&1;                eq "중복 카테고리 → 1"        "1" "$?"
app import --from "$WORK/nope.csv" >/dev/null 2>&1;   eq "파일 접근 실패 → 2"       "2" "$?"
app search --type bad >/dev/null 2>&1;                eq "잘못된 사용법(argparse) → 2" "2" "$?"

# ---------------------------------------------------------------- 항목 2-3
sect "항목 2-3  update/delete 원자성 (임시파일 + fsync + os.replace)"
pycheck <<'PY'
import sys
def check(desc, expected, actual):
    print("PASS|" + desc if expected == actual else "FAIL|%s|%s|%s" % (desc, expected, actual))

import hashlib, tempfile
from pathlib import Path
from budget_app.repositories import open_stores
from budget_app.models import Transaction

with tempfile.TemporaryDirectory() as d:
    stores = open_stores(Path(d) / "data")
    repo = stores.transactions
    for i in (1, 2, 3):
        repo.append(Transaction(id=f"TX-{i:06d}", date="2024-01-0%d" % i,
                                type="expense", category="food", amount=1000 * i))
    path = repo.path
    before = hashlib.md5(path.read_bytes()).hexdigest()

    def exploding():
        """한 건만 쓰고 도중에 터지는 제너레이터 - 쓰기 중 크래시를 흉내낸다."""
        yield Transaction(id="TX-000001", date="2024-01-01", type="expense",
                          category="food", amount=1000)
        raise RuntimeError("쓰기 도중 강제 실패")

    try:
        repo.replace_all(exploding())
    except RuntimeError:
        pass

    after = hashlib.md5(path.read_bytes()).hexdigest()
    check("쓰기 도중 실패해도 원본이 바이트 단위로 동일", before, after)
    check("실패 후에도 전체가 그대로 읽힘", ["TX-000001", "TX-000002", "TX-000003"],
          [t.id for t in repo.stream()])
    leftovers = [p.name for p in path.parent.iterdir() if p.name != path.name]
    check("임시 파일이 남지 않음", [], leftovers)
PY
before_md5=$(md5 -q "$D/transactions.jsonl" 2>/dev/null || md5sum "$D/transactions.jsonl" | cut -d' ' -f1)
app delete --id TX-999999 >/dev/null 2>&1
after_md5=$(md5 -q "$D/transactions.jsonl" 2>/dev/null || md5sum "$D/transactions.jsonl" | cut -d' ' -f1)
eq "실패한 delete 후 저장 파일이 바이트 단위로 동일" "$before_md5" "$after_md5"
eq "data 폴더에 임시 파일 잔여 없음" "3" "$(ls "$D" | wc -l | tr -d ' ')"

# ---------------------------------------------------------------- 항목 3-1
sect "항목 3-1  제너레이터 스트리밍 (읽은 바이트를 실제로 센다)"
pycheck <<'PY'
import sys
def check(desc, expected, actual):
    print("PASS|" + desc if expected == actual else "FAIL|%s|%s|%s" % (desc, expected, actual))
def info(desc, value):
    print("INFO|%s|%s" % (desc, value))

import itertools, tempfile
from pathlib import Path
from budget_app.repositories import open_stores
from budget_app.models import Transaction

real_open = Path.open

counter = [0]

class Counting:
    """read()/순회로 실제로 읽은 바이트만 센다."""
    def __init__(self, fp): self._fp = fp
    def read(self, n=-1):
        data = self._fp.read(n)
        counter[0] += len(data)
        return data
    def __iter__(self):
        for line in self._fp:
            counter[0] += len(line)
            yield line
    def __getattr__(self, name): return getattr(self._fp, name)
    def __enter__(self): self._fp.__enter__(); return self
    def __exit__(self, *a): return self._fp.__exit__(*a)

def counting_open(self, *a, **kw):
    return Counting(real_open(self, *a, **kw))

with tempfile.TemporaryDirectory() as d:
    stores = open_stores(Path(d) / "data")
    repo = stores.transactions
    repo.path.parent.mkdir(parents=True, exist_ok=True)
    with repo.path.open("a", encoding="utf-8") as fp:
        import json
        for i in range(1, 10001):
            fp.write(json.dumps({"id": "TX-%06d" % i, "date": "2024-01-%02d" % (i % 28 + 1),
                                 "type": "expense", "category": "food", "amount": i,
                                 "memo": "점심 %d" % i, "tags": ["meal"]}, ensure_ascii=False) + "\n")
    size = repo.path.stat().st_size

    Path.open = counting_open
    counter[0] = 0
    rows = list(itertools.islice(repo.stream_reversed(), 3))
    listed = counter[0]
    counter[0] = 0
    repo.next_id()
    nextid = counter[0]
    Path.open = real_open

    info("파일 크기 (10,000건)", "%d bytes" % size)
    info("list --limit 3 이 읽은 양", "%d bytes (%.1f%%)" % (listed, listed * 100 / size))
    info("next_id() 가 읽은 양", "%d bytes (%.1f%%)" % (nextid, nextid * 100 / size))
    check("최신 3건을 정확히 가져옴", ["TX-010000", "TX-009999", "TX-009998"], [t.id for t in rows])
    check("list --limit 3 이 파일의 10% 미만만 읽음", True, listed < size * 0.10)
    check("next_id() 가 파일의 10% 미만만 읽음", True, nextid < size * 0.10)
PY

# ---------------------------------------------------------------- 항목 3-2 / 3-3
sect "항목 3-2 / 3-3  데코레이터 적용 범위와 타입 힌트"
pycheck <<'PY'
import sys
def check(desc, expected, actual):
    print("PASS|" + desc if expected == actual else "FAIL|%s|%s|%s" % (desc, expected, actual))

import inspect
from budget_app import cli, repositories, services

undecorated = [name for name, fn in cli.HANDLERS.items() if not hasattr(fn, "__wrapped__")]
check("모든 핸들러에 @handle_errors 적용", [], undecorated)
check("등록된 핸들러 수", 10, len(cli.HANDLERS))
check("@wraps 로 원래 이름 보존", "handle_list", cli.HANDLERS["list"].__name__)

sigs = {
    "read_jsonl": repositories.read_jsonl,
    "read_jsonl_reversed": repositories.read_jsonl_reversed,
    "search_transactions": services.search_transactions,
    "recent_transactions": services.recent_transactions,
}
for name, fn in sigs.items():
    ret = str(inspect.signature(fn).return_annotation)
    check("%s 의 반환 타입이 Iterator (전량 적재 아님을 타입으로 명시)" % name,
          True, "Iterator" in ret)

missing = [name for name, fn in vars(services).items()
           if inspect.isfunction(fn) and fn.__module__ == "budget_app.services"
           and inspect.signature(fn).return_annotation is inspect.Signature.empty]
check("services 의 모든 공개 함수에 반환 타입 힌트 존재", [], missing)
PY

# ---------------------------------------------------------------- 항목 4-3
sect "항목 4-3  import 부분 성공 (깨진 행 처리)"
cat > "$WORK/mixed.csv" <<'CSV'
date,type,category,amount,memo,tags
2024-03-01,expense,food,10000,정상1,
2024-13-99,expense,food,10000,날짜깨짐,
2024-03-02,bad,food,10000,타입깨짐,
2024-03-03,expense,ghost,10000,없는카테고리,
2024-03-04,expense,food,-500,음수금액,
2024-03-05,expense,food,만원,숫자아님,
2024-03-06,expense,food,20000,정상2,
CSV
D4="$WORK/data4"
mix_out=$($PY -m budget_app --data-dir "$D4" import --from "$WORK/mixed.csv" 2>&1); mix_code=$?
has "정상 행은 저장하고 나머지만 건너뜀" "[완료] imported=2, skipped=5" "$mix_out"
has "건너뛴 행의 줄 번호를 보고 (3행)" "[건너뜀] 3행:" "$mix_out"
has "건너뛴 이유도 함께 보고 (날짜)" "날짜 형식이 올바르지 않습니다" "$mix_out"
has "없는 카테고리도 걸러냄" "등록되지 않은 카테고리입니다: ghost" "$mix_out"
has "음수 금액도 걸러냄" "금액은 0보다 큰 정수여야 합니다" "$mix_out"
eq  "부분 성공은 종료 코드 0" "0" "$mix_code"
eq  "저장된 건수는 정확히 2건" "2" "$(wc -l < "$D4/transactions.jsonl" | tr -d ' ')"
eq  "건너뜀 안내는 stderr 로 분리" "0" "$($PY -m budget_app --data-dir "$WORK/data5" import --from "$WORK/mixed.csv" 2>/dev/null | grep -c '건너뜀')"
has "결과 요약은 stdout 으로" "[완료]" "$($PY -m budget_app --data-dir "$WORK/data6" import --from "$WORK/mixed.csv" 2>/dev/null)"

D7="$WORK/data7"
dry_out=$($PY -m budget_app --data-dir "$D7" import --from "$WORK/mixed.csv" --dry-run 2>&1)
has "--dry-run 도 같은 검증 결과를 보고" "imported=2, skipped=5" "$dry_out"
eq  "--dry-run 은 파일을 만들지 않음" "no" "$([ -f "$D7/transactions.jsonl" ] && echo yes || echo no)"

printf 'day,kind,cat,won\n2024-03-01,expense,food,1000\n' > "$WORK/wrong.csv"
D8="$WORK/data8"
bad_out=$($PY -m budget_app --data-dir "$D8" import --from "$WORK/wrong.csv" 2>&1); bad_code=$?
has "헤더가 스키마와 다르면 즉시 실패" "CSV 헤더에 필수 칸이 없습니다" "$bad_out"
eq  "파일 단위 실패는 종료 코드 2" "2" "$bad_code"
eq  "파일 단위 실패 시 한 건도 저장하지 않음" "no" "$([ -f "$D8/transactions.jsonl" ] && echo yes || echo no)"

# ---------------------------------------------------------------- 항목 4-2 (선택)
if [ "$BENCH" = 1 ]; then
sect "항목 4-2  10만 건 성능 측정 (--bench)"
pycheck <<'PY'
import sys
def check(desc, expected, actual):
    print("PASS|" + desc if expected == actual else "FAIL|%s|%s|%s" % (desc, expected, actual))
def info(desc, value):
    print("INFO|%s|%s" % (desc, value))

import itertools, json, tempfile, time
from pathlib import Path
from budget_app.repositories import open_stores
from budget_app import services

N = 100_000
with tempfile.TemporaryDirectory() as d:
    stores = open_stores(Path(d) / "data")
    repo = stores.transactions
    repo.path.parent.mkdir(parents=True, exist_ok=True)
    with repo.path.open("a", encoding="utf-8") as fp:
        for i in range(1, N + 1):
            fp.write(json.dumps({"id": "TX-%06d" % i, "date": "2024-%02d-%02d" % (i % 12 + 1, i % 28 + 1),
                                 "type": "expense", "category": "food", "amount": 1000,
                                 "memo": "점심 %d" % i, "tags": ["meal"]}, ensure_ascii=False) + "\n")
    size = repo.path.stat().st_size
    info("파일 크기", "%.1f MB (%d건)" % (size / 1024 / 1024, N))

    def timed(label, fn, bound):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        info(label, "%.3f초" % dt)
        check("%s 가 %.1f초 이내" % (label, bound), True, dt < bound)

    timed("list --limit 20", lambda: list(itertools.islice(repo.stream_reversed(), 20)), 0.5)
    timed("search --tag meal --limit 20",
          lambda: list(services.search_transactions(stores, limit=20, tag="meal")), 0.5)
    timed("next_id() (add 의 비용)", lambda: repo.next_id(), 0.5)
    timed("search --q 없는키워드 (전량 스캔)",
          lambda: list(services.search_transactions(stores, limit=20, q="존재하지않는키워드")), 5.0)
    timed("summary --month 2024-01 (전량 스캔)",
          lambda: services.summarize_month(stores, "2024-01", 3), 5.0)
    timed("delete (전량 읽기 + 전량 재작성)",
          lambda: services.delete_transaction(stores, "TX-000001"), 10.0)
PY
else
sect "항목 4-2  10만 건 성능 측정"
info "건너뜀" "--bench 를 붙이면 실행합니다"
fi

# ---------------------------------------------------------------- 결과
printf '\n%s────────────────────────────────────────%s\n' "$B" "$N"
if [ "$FAIL" -eq 0 ]; then
    printf '%s전체 통과%s  PASS %d / FAIL %d\n' "$G" "$N" "$PASS" "$FAIL"
    exit 0
else
    printf '%s실패 있음%s  PASS %d / FAIL %d\n' "$R" "$N" "$PASS" "$FAIL"
    exit 1
fi
