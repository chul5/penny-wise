"""공통 관심사 데코레이터 (미션 12번).

명령 핸들러가 하는 일은 "요청을 처리한다" 하나여야 한다. 오류를 어떤 문구로
보여줄지, 종료 코드를 뭘로 할지는 모든 핸들러에 똑같이 걸리는 관심사이므로
데코레이터로 분리한다. 그 결과 핸들러 본문에는 try/except가 하나도 없다.
"""

from __future__ import annotations

import functools
import sys
from typing import Callable, ParamSpec

from .errors import BudgetAppError

P = ParamSpec("P")


def print_error(exc: BudgetAppError) -> None:
    """오류를 [오류]/[힌트] 두 줄로 stderr에 출력한다.

    이 문구를 만드는 곳은 여기 한 군데뿐이다. 핸들러에서 난 오류든, 디스패치
    도중 난 오류든, 재입력 루프에서 난 검증 오류든 같은 모양으로 보여야 한다.
    """
    print(f"[오류] {exc.message}", file=sys.stderr)
    if exc.hint:
        print(f"[힌트] {exc.hint}", file=sys.stderr)


def report_error(exc: BudgetAppError) -> int:
    """오류를 출력하고 그 예외가 정한 종료 코드를 돌려준다."""
    print_error(exc)
    return exc.exit_code


def handle_errors(func: Callable[P, int]) -> Callable[P, int]:
    """도메인 예외를 사용자용 메시지와 종료 코드로 바꾼다.

    스택트레이스는 절대 노출하지 않는다(미션 13번). 각 예외가 hint와
    exit_code를 스스로 들고 있으므로 여기서 분기할 게 없다.

    ParamSpec 덕분에 감싼 뒤에도 원래 함수의 인자 타입이 유지된다.
    Callable[..., int]로 뭉개면 (args, stores) 시그니처 검사가 사라진다.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except BudgetAppError as exc:
            return report_error(exc)
        except KeyboardInterrupt:
            print("\n[중단] 사용자가 실행을 취소했습니다.", file=sys.stderr)
            return 130

    return wrapper
