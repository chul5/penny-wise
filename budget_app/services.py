"""서비스 계층: 유스케이스 조합.

저장소는 "파일을 어떻게 읽고 쓰는가"만 알고, CLI는 "어떻게 묻고 보여주는가"만
안다. 그 사이에서 "무엇이 규칙인가"를 담는 게 이 계층이다.
예: 카테고리는 중복될 수 없고, 파일이 비어 있으면 기본값을 넣어준다.

CLI를 거치지 않고 이 함수들만 호출해도 앱의 규칙을 그대로 검증할 수 있다.
"""

from __future__ import annotations

from dataclasses import replace

from .errors import (CategoryInUseError, DuplicateCategoryError, UnknownCategoryError,
                     ValidationError)
from .models import Transaction
from .repositories import CategoryStore, Stores
from .validators import parse_category_name

DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")


def list_categories(store: CategoryStore) -> list[str]:
    """등록된 카테고리 목록. 비어 있으면 기본 카테고리를 만들어 넣고 그것을 준다.

    미션이 "빈 카테고리 파일" 처리로 요구한 두 안 중 (안 A) 자동 생성을 고른
    결과다. 첫 실행에서 add가 바로 되지 않으면 사용 흐름이 끊긴다.

    add와 list가 같은 함수를 쓰므로, 어느 쪽을 먼저 실행해도 기본값이 준비된다.
    """
    names = store.names()
    if names:
        return names
    # 한 줄씩 append하면 중간에 실패했을 때 반만 남는다. 한 번에 쓴다.
    store.replace_all(DEFAULT_CATEGORIES)
    return list(DEFAULT_CATEGORIES)


def add_category(store: CategoryStore, name: str) -> str:
    """카테고리를 추가하고 저장된 이름을 돌려준다. 이미 있으면 오류.

    중복 판정은 대소문자를 무시한다(casefold). food와 FOOD가 함께 등록되면
    summary의 카테고리별 집계가 둘로 쪼개져 사용자가 의도한 결과가 나오지
    않는다. 다만 저장은 입력한 대로 한다 - Netflix를 netflix로 바꿔버리면
    사용자가 정한 이름을 앱이 마음대로 고치는 셈이다.
    """
    clean = parse_category_name(name)
    for existing in list_categories(store):
        if existing.casefold() == clean.casefold():
            raise DuplicateCategoryError(f"이미 있는 카테고리입니다: {existing}")
    store.append(clean)
    return clean


def resolve_category(store: CategoryStore, name: str) -> str:
    """입력한 이름을 등록된 표기로 바꿔 준다. 없으면 오류.

    add와 마찬가지로 대소문자를 무시해 찾되, 돌려주는 건 저장된 표기다.
    사용자가 NETFLIX라고 쳐도 거래에는 등록된 Netflix가 들어가야 한다.
    """
    clean = parse_category_name(name)
    for existing in list_categories(store):
        if existing.casefold() == clean.casefold():
            return existing
    raise UnknownCategoryError(f"등록되지 않은 카테고리입니다: {clean}")


def remove_category(
    stores: Stores, name: str, replace_with: str | None = None
) -> tuple[str, str | None, int]:
    """카테고리를 삭제한다. 반환값은 (삭제된 이름, 대체 카테고리, 옮긴 거래 건수).

    이름을 둘 다 등록된 표기로 돌려주므로, 호출한 쪽이 사용자 입력을 다시
    해석할 필요가 없다.

    사용 중인 카테고리를 그냥 지우면 거래의 category가 등록 목록에 없는 값으로
    남아 데이터가 어긋난다. 그래서 미션 10번대로 삭제를 막거나 대체 카테고리를
    요구한다.

    순서가 중요하다. 거래를 먼저 옮기고 카테고리를 나중에 지운다. 반대로 하면
    중간에 실패했을 때 거래가 이미 없는 카테고리를 가리키게 된다.
    """
    target = resolve_category(stores.categories, name)
    used = sum(1 for t in stores.transactions.stream() if t.category == target)
    substitute: str | None = None

    if used:
        if replace_with is None:
            raise CategoryInUseError(
                f"'{target}' 카테고리를 사용하는 거래가 {used}건 있습니다."
            )
        substitute = resolve_category(stores.categories, replace_with)
        if substitute == target:
            raise ValidationError(
                "대체 카테고리가 삭제할 카테고리와 같습니다.",
                hint=f"--replace-with 에 다른 카테고리를 지정하세요: {target}",
            )
        stores.transactions.replace_all(
            replace(t, category=substitute) if t.category == target else t
            for t in stores.transactions.stream()
        )

    stores.categories.replace_all(n for n in list_categories(stores.categories) if n != target)
    return target, substitute, used


def add_transaction(
    stores: Stores,
    *,
    date: str,
    type: str,
    category: str,
    amount: int,
    memo: str = "",
    tags: tuple[str, ...] = (),
) -> Transaction:
    """거래를 저장하고 저장된 객체를 돌려준다.

    값 검증은 이미 끝난 상태로 받는다(validators가 담당). 이 함수가 더하는
    규칙은 두 가지다. 카테고리를 등록된 표기로 바꾸는 것, 그리고 id를 붙이는 것.

    키워드 전용 인자로 받는 이유는 필드가 여섯 개라 위치 인자로 넘기면
    date와 type을 뒤바꿔도 아무 오류 없이 저장되기 때문이다.
    """
    transaction = Transaction(
        id=stores.transactions.next_id(),
        date=date,
        type=type,
        category=resolve_category(stores.categories, category),
        amount=amount,
        memo=memo,
        tags=tags,
    )
    stores.transactions.append(transaction)
    return transaction
