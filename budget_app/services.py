"""서비스 계층: 유스케이스 조합.

저장소는 "파일을 어떻게 읽고 쓰는가"만 알고, CLI는 "어떻게 묻고 보여주는가"만
안다. 그 사이에서 "무엇이 규칙인가"를 담는 게 이 계층이다.
예: 카테고리는 중복될 수 없고, 파일이 비어 있으면 기본값을 넣어준다.

CLI를 거치지 않고 이 함수들만 호출해도 앱의 규칙을 그대로 검증할 수 있다.
"""

from __future__ import annotations

from .errors import DuplicateCategoryError
from .repositories import CategoryStore
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
