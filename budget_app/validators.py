"""입력값 검증.

여기 있는 함수는 모두 순수 함수다. 문자열을 받아 검증된 값을 돌려주거나
ValidationError를 던진다. input()을 부르지 않으므로 대화형이든 옵션
방식이든 CSV import든 같은 함수를 그대로 쓴다.

각 예외는 hint를 함께 들고 나간다. 사용자가 보는 출력이
    [오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
    [힌트] 예: 2024-01-15
이 되도록 문구를 여기서 정한다.
"""

from __future__ import annotations

from datetime import datetime

from .errors import ValidationError
from .models import TRANSACTION_TYPES


def parse_date(value: str) -> str:
    """'YYYY-MM-DD'로 정규화해 돌려준다.

    strptime은 달력까지 검사하므로 2024-02-30이나 2024-13-40이 걸러진다.
    strftime으로 다시 만들어 돌려주기 때문에 '2024-1-5'처럼 자릿수를 덜
    맞춘 입력도 '2024-01-05'로 통일된다.
    """
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", hint="예: 2024-01-15"
        ) from None


def parse_month(value: str) -> str:
    """'YYYY-MM'으로 정규화해 돌려준다."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise ValidationError(
            "월 형식이 올바르지 않습니다 (YYYY-MM).", hint="예: 2024-01"
        ) from None


def parse_type(value: str) -> str:
    """income 또는 expense. 대소문자는 가리지 않는다."""
    text = value.strip().lower()
    if text not in TRANSACTION_TYPES:
        raise ValidationError(
            f"타입은 {' 또는 '.join(TRANSACTION_TYPES)} 중 하나여야 합니다.",
            hint=f"입력값: {value.strip()}",
        )
    return text


def parse_amount(value: str) -> int:
    """양수 정수만 허용한다. '15,000'처럼 천단위 쉼표가 있어도 받는다."""
    text = value.strip().replace(",", "")
    try:
        amount = int(text)
    except ValueError:
        raise ValidationError(
            "금액은 숫자로 입력해야 합니다.", hint="예: 15000"
        ) from None
    if amount <= 0:
        raise ValidationError(
            "금액은 0보다 큰 정수여야 합니다.", hint=f"입력값: {amount}"
        )
    return amount


def parse_tags(value: str) -> tuple[str, ...]:
    """쉼표로 구분된 태그. 빈 입력은 빈 튜플이고, 중복은 순서를 지키며 제거한다."""
    return tuple(dict.fromkeys(tag.strip() for tag in value.split(",") if tag.strip()))
