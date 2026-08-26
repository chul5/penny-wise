"""CLI 계층: argparse 파서 정의와 명령 디스패치.

이 계층의 책임은 세 가지뿐이다.
  1) 문자열 인자를 파싱한다
  2) 서비스에 위임한다
  3) 결과를 출력하고 종료 코드를 정한다

도메인 로직은 절대 여기 오지 않는다.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from typing import Callable, Sequence, TypeVar

from . import __version__
from .decorators import handle_errors, print_error, report_error
from .errors import BudgetAppError, ValidationError
from .repositories import Stores, open_stores
from .services import (add_category, add_transaction, list_categories, recent_transactions,
                       remove_category, resolve_category)
from .validators import (parse_amount, parse_category_name, parse_date, parse_tags,
                         parse_type)

DEFAULT_DATA_DIR = "./data"
DEFAULT_LIST_LIMIT = 20
DEFAULT_TOP_N = 3

PROG = "python -m budget_app"

# prompt()가 넘겨받은 검증 함수의 반환 타입을 그대로 돌려주게 하는 타입 변수.
T = TypeVar("T")

# 모든 핸들러가 공유하는 시그니처. 이 통일성이 @handle_errors를 전부 똑같이
# 적용할 수 있게 하고, dispatch를 dict 조회 한 줄로 만든다.
Handler = Callable[[argparse.Namespace, Stores], int]


def prompt(label: str, parse: Callable[[str], T]) -> T:
    """올바른 값이 들어올 때까지 되묻는다.

    검증은 validators의 순수 함수가 하고, 여기서는 물어보고 오류를 보여주는
    일만 한다. 그래서 같은 검증 함수를 옵션 방식이나 CSV import에서도 쓴다.

    TypeVar 덕분에 prompt("금액", parse_amount)의 결과가 int로,
    prompt("태그", parse_tags)의 결과가 tuple[str, ...]로 좁혀진다.
    """
    while True:
        try:
            return parse(input(f"{label}: "))
        except ValidationError as exc:
            print_error(exc)
        except EOFError:
            # Ctrl+D 로 입력이 끊긴 경우. 스택트레이스 대신 안내로 끝낸다.
            raise BudgetAppError(
                "입력이 중단되었습니다.", hint="다시 실행해 주세요."
            ) from None


def build_parser() -> argparse.ArgumentParser:
    """모든 서브커맨드를 등록한 파서를 만든다.

    옵션은 미션 규칙에 따라 롱옵션(--)만 사용한다. 단축 옵션은 두지 않는다.
    """
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="파일 기반 콘솔 가계부",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="예: %(prog)s add / %(prog)s list --limit 10 / %(prog)s summary --month 2024-01",
    )
    parser.add_argument("--version", action="version", version=f"budget_app {__version__}")
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        metavar="PATH",
        help=f"저장 폴더 (기본: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="실행 로그와 소요 시간을 함께 출력",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    # --- add: 대화형 전용 (미션에서 입력 기본 방식으로 고정) ---
    sub.add_parser("add", help="거래 추가 (대화형 입력)")

    # --- list ---
    p_list = sub.add_parser("list", help="거래 목록 조회 (최신순)")
    p_list.add_argument(
        "--limit", type=int, default=DEFAULT_LIST_LIMIT, metavar="N",
        help=f"출력 건수 (기본: {DEFAULT_LIST_LIMIT})",
    )

    # --- search ---
    p_search = sub.add_parser("search", help="조건 검색 (최신순)")
    p_search.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="시작일(포함)")
    p_search.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="종료일(포함)")
    p_search.add_argument("--category", metavar="NAME", help="카테고리")
    p_search.add_argument("--type", dest="tx_type", choices=("income", "expense"), help="거래 타입")
    p_search.add_argument("--q", metavar="KEYWORD", help="메모 키워드 부분 일치")
    p_search.add_argument("--tag", metavar="TAG", help="태그 일치")
    p_search.add_argument(
        "--limit", type=int, default=DEFAULT_LIST_LIMIT, metavar="N",
        help=f"출력 건수 (기본: {DEFAULT_LIST_LIMIT})",
    )

    # --- summary ---
    p_summary = sub.add_parser("summary", help="월별 요약 + 예산 사용률")
    p_summary.add_argument("--month", required=True, metavar="YYYY-MM", help="대상 월")
    p_summary.add_argument(
        "--top", type=int, default=DEFAULT_TOP_N, metavar="N",
        help=f"카테고리별 지출 상위 N건 (기본: {DEFAULT_TOP_N})",
    )

    # --- update: 옵션 기반으로 고정 (안 A) ---
    p_update = sub.add_parser("update", help="거래 수정 (옵션 기반)")
    p_update.add_argument("--id", dest="tx_id", required=True, metavar="ID", help="수정할 거래 id")
    p_update.add_argument("--date", metavar="YYYY-MM-DD")
    p_update.add_argument("--type", dest="tx_type", choices=("income", "expense"))
    p_update.add_argument("--category", metavar="NAME")
    p_update.add_argument("--amount", type=int, metavar="N")
    p_update.add_argument("--memo", metavar="TEXT")
    p_update.add_argument("--tags", metavar="A,B", help="쉼표로 구분")

    # --- delete ---
    p_delete = sub.add_parser("delete", help="거래 삭제")
    p_delete.add_argument("--id", dest="tx_id", required=True, metavar="ID", help="삭제할 거래 id")

    # --- budget set / show ---
    p_budget = sub.add_parser("budget", help="월 예산 설정/조회")
    budget_sub = p_budget.add_subparsers(dest="budget_action", metavar="<action>", required=True)
    p_budget_set = budget_sub.add_parser("set", help="월 예산 저장")
    p_budget_set.add_argument("--month", required=True, metavar="YYYY-MM")
    p_budget_set.add_argument("--amount", type=int, required=True, metavar="N")
    p_budget_show = budget_sub.add_parser("show", help="저장된 예산 조회")
    p_budget_show.add_argument("--month", metavar="YYYY-MM", help="생략하면 전체 목록")

    # --- category add / list / remove ---
    p_category = sub.add_parser("category", help="카테고리 관리")
    category_sub = p_category.add_subparsers(dest="category_action", metavar="<action>", required=True)
    p_cat_add = category_sub.add_parser("add", help="카테고리 추가 (이름 생략 시 대화형)")
    p_cat_add.add_argument("name", nargs="?", metavar="NAME")
    category_sub.add_parser("list", help="카테고리 목록")
    p_cat_remove = category_sub.add_parser("remove", help="카테고리 삭제")
    p_cat_remove.add_argument("name", metavar="NAME")
    p_cat_remove.add_argument(
        "--replace-with", dest="replace_with", metavar="NAME",
        help="사용 중인 카테고리일 때 대체할 카테고리",
    )

    # --- export / import ---
    p_export = sub.add_parser("export", help="조건에 맞는 거래를 CSV로 내보내기")
    p_export.add_argument("--out", required=True, metavar="FILE.csv", help="출력 파일 경로")
    p_export.add_argument("--month", metavar="YYYY-MM", help="대상 월")
    p_export.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD")
    p_export.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD")

    p_import = sub.add_parser("import", help="CSV에서 거래 일괄 등록")
    p_import.add_argument("--from", dest="src", required=True, metavar="FILE.csv", help="입력 파일 경로")
    p_import.add_argument("--dry-run", action="store_true", help="저장하지 않고 검증만 수행")

    # --- backup (보너스) ---
    sub.add_parser("backup", help="타임스탬프가 붙은 백업 파일 생성")

    return parser


@handle_errors
def handle_category(args: argparse.Namespace, stores: Stores) -> int:
    """category add / list / remove.

    본문에 try/except가 없다. 중복이나 잘못된 이름, 사용 중 삭제는 서비스가
    예외로 올리고 @handle_errors가 [오류]/[힌트] 출력과 종료 코드로 바꾼다.
    """
    if args.category_action == "list":
        for name in list_categories(stores.categories):
            print(f"- {name}")
        return 0

    if args.category_action == "add":
        # 이름을 인자로 주면 그대로, 생략하면 물어본다(미션 8절 예시).
        name = args.name or prompt("카테고리명", parse_category_name)
        print(f"[저장 완료] category={add_category(stores.categories, name)}")
        return 0

    name, substitute, moved = remove_category(stores, args.name, args.replace_with)
    if moved:
        print(f"[삭제 완료] category={name} (거래 {moved}건을 {substitute}로 옮겼습니다)")
    else:
        print(f"[삭제 완료] category={name}")
    return 0


@handle_errors
def handle_add(args: argparse.Namespace, stores: Stores) -> int:
    """add - 대화형으로 거래를 입력받아 저장한다 (미션 4번).

    라벨과 순서는 미션 8절 예시를 그대로 따른다. 각 항목은 올바른 값이 들어올
    때까지 되묻는다. 카테고리도 마찬가지다 - 미등록 이름이면 안내 후 재입력.
    """
    transaction = add_transaction(
        stores,
        date=prompt("날짜(YYYY-MM-DD)", parse_date),
        type=prompt("타입(income/expense)", parse_type),
        category=prompt("카테고리", lambda value: resolve_category(stores.categories, value)),
        amount=prompt("금액(양수)", parse_amount),
        memo=prompt("메모(선택)", str.strip),
        tags=prompt("태그(쉼표로 구분, 없으면 엔터)", parse_tags),
    )
    print(f"[저장 완료] id={transaction.id}")
    return 0


@handle_errors
def handle_list(args: argparse.Namespace, stores: Stores) -> int:
    """list - 최근 입력순으로 거래를 출력한다 (미션 5번).

    출력 형식은 미션 8절 예시를 따른다. type을 7칸으로 맞추는 건 income과
    expense의 길이가 달라 구분선이 어긋나기 때문이다.
    """
    found = False
    for transaction in recent_transactions(stores, args.limit):
        found = True
        print(
            f"{transaction.id} | {transaction.date} | {transaction.type:<7} | "
            f"{transaction.category} | {transaction.amount} | {transaction.memo}".rstrip()
        )
    if not found:
        # 데이터가 아니라 안내이므로 stderr로 보낸다. list > out.txt 했을 때
        # 파일에 안내 문구가 섞이면 안 된다.
        print("[안내] 저장된 거래가 없습니다.", file=sys.stderr)
    return 0


# 명령 이름 -> 핸들러. 명령을 추가할 때 핸들러를 위에 정의하고 여기 한 줄을
# 더한다. 선언과 값을 한 곳에 모아 두면 지금 무슨 명령이 동작하는지 이 표만
# 보면 된다. (파이썬은 위에서 아래로 실행하므로 함수 이름을 쓰는 이 표는
# 핸들러 정의보다 뒤에 와야 한다.)
HANDLERS: dict[str, Handler] = {
    "category": handle_category,
    "add": handle_add,
    "list": handle_list,
}


def dispatch(args: argparse.Namespace) -> int:
    """파싱된 인자를 핸들러로 넘긴다. 반환값이 그대로 종료 코드가 된다.

    모든 핸들러가 (args, stores) 시그니처를 공유하므로 여기서 분기할 게 없다.
    저장소는 --data-dir 로 그때그때 만들어 넘긴다.
    """
    handler = HANDLERS.get(args.command)
    if handler is None:
        raise BudgetAppError(
            f"'{args.command}' 명령은 아직 구현되지 않았습니다.",
            hint="구현 순서는 docs/plan.md 9절을 참고하세요.",
        )
    return handler(args, open_stores(args.data_dir))


def main(argv: Sequence[str] | None = None) -> int:
    """엔트리포인트. 스택트레이스를 노출하지 않고 종료 코드만 돌려준다."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch(args)
    except BudgetAppError as exc:
        # 핸들러 안에서 난 오류는 @handle_errors가 이미 처리한다.
        # 여기 오는 건 디스패치 도중(예: 없는 명령) 난 오류뿐이다.
        return report_error(exc)
    except KeyboardInterrupt:
        print("\n[중단] 사용자가 실행을 취소했습니다.", file=sys.stderr)
        return 130
    except Exception as exc:
        # 예상하지 못한 오류(우리 쪽 버그)도 스택트레이스를 노출하지 않는다.
        # 대신 --verbose 를 주면 개발자가 원인을 볼 수 있게 남긴다.
        code = report_error(
            BudgetAppError(
                f"예상하지 못한 오류가 발생했습니다: {exc}",
                hint="--verbose 로 다시 실행하면 자세한 내용을 볼 수 있습니다.",
            )
        )
        if args.verbose:
            traceback.print_exc()
        return code
