"""도메인 예외 계층.

모든 예외가 `hint`(해결 힌트)와 `exit_code`를 스스로 들고 다닌다.
덕분에 출력 문구를 만드는 책임이 CLI 데코레이터 한 곳으로 모이고,
스택트레이스 대신 "원인 + 힌트"만 사용자에게 노출할 수 있다.
"""

from __future__ import annotations


class BudgetAppError(Exception):
    """이 앱이 의도적으로 발생시키는 모든 오류의 최상위 타입."""

    exit_code: int = 1
    hint: str = ""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if hint is not None:
            self.hint = hint


class ValidationError(BudgetAppError):
    """날짜 형식, 금액, 타입 등 입력값 자체가 잘못된 경우."""

    hint = "입력 형식을 확인해 주세요."


class NotFoundError(BudgetAppError):
    """지정한 id의 데이터가 존재하지 않는 경우."""

    hint = "list 명령으로 존재하는 id를 확인해 보세요."


class UnknownCategoryError(BudgetAppError):
    """등록되지 않은 카테고리를 사용하려는 경우."""

    hint = "category list로 목록을 확인하거나 category add로 먼저 등록하세요."


class DuplicateCategoryError(BudgetAppError):
    """이미 존재하는 카테고리를 다시 추가하려는 경우."""

    hint = "category list로 현재 목록을 확인하세요."


class CategoryInUseError(BudgetAppError):
    """삭제하려는 카테고리를 사용하는 거래가 남아 있는 경우."""

    hint = "--replace-with <다른카테고리> 로 대체 카테고리를 지정하세요."


class DataFileError(BudgetAppError):
    """저장 파일을 읽거나 쓸 수 없는 경우(권한, 경로, 손상)."""

    exit_code = 2
    hint = "--data-dir 경로와 파일 쓰기 권한을 확인하세요."
