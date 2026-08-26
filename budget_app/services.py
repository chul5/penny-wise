"""서비스 계층: 유스케이스 조합.

저장소는 "파일을 어떻게 읽고 쓰는가"만 알고, CLI는 "어떻게 묻고 보여주는가"만
안다. 그 사이에서 "무엇이 규칙인가"를 담는 게 이 계층이다.
예: 카테고리는 중복될 수 없고, 파일이 비어 있으면 기본값을 넣어준다.

CLI를 거치지 않고 이 함수들만 호출해도 앱의 규칙을 그대로 검증할 수 있다.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import replace
from itertools import islice
from pathlib import Path
from typing import Iterator

from .errors import (CategoryInUseError, DataFileError, DuplicateCategoryError,
                     NotFoundError, UnknownCategoryError, ValidationError)
from .models import Budget, MonthlySummary, Transaction
from .repositories import CategoryStore, Stores
from .validators import (parse_amount, parse_category_name, parse_date, parse_month,
                         parse_tags, parse_type)

DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")

# import/export CSV 고정 스키마 (미션 11번). id는 넣지 않는다 - 가져올 때
# 새로 발급하므로 내보낸 id가 다른 앱/다른 파일에서 의미를 갖지 않는다.
CSV_FIELDS = ("date", "type", "category", "amount", "memo", "tags")


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


def recent_transactions(stores: Stores, limit: int) -> Iterator[Transaction]:
    """최근 입력순으로 limit건. 조건 없는 search와 같다."""
    return search_transactions(stores, limit=limit)


def search_transactions(
    stores: Stores,
    *,
    limit: int | None,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    type: str | None = None,
    q: str | None = None,
    tag: str | None = None,
) -> Iterator[Transaction]:
    """조건에 맞는 거래를 최근 입력순으로 흘려보낸다 (미션 7번).

    조건을 제너레이터 체인으로 겹치지 않고 술어(predicate) 하나로 합쳤다.
    filter가 게으르므로 스트리밍은 그대로 유지되고, 조건 다섯 개를 함수 다섯
    개로 만드는 것보다 짧다.

    검증은 루프 밖에서 한 번만 한다. 날짜를 정규화해 두는 게 특히 중요하다 -
    날짜를 문자열로 비교하므로 '2024-1-5'가 그대로 들어오면 비교가 깨진다.

    리스트가 아니라 Iterator를 돌려주는 이유는 list()를 한 번 끼우면 파일을
    전부 읽게 되어 스트리밍이 깨지기 때문이다.

    limit=None은 "제한 없음"이다. islice(it, None)이 그대로 전부 흘려보내므로
    export가 조건에 맞는 전체를 받을 수 있다.
    """
    if limit is not None and limit <= 0:
        raise ValidationError("--limit 은 1 이상이어야 합니다.", hint=f"입력값: {limit}")

    wanted_month = parse_month(month) if month else None
    start = parse_date(date_from) if date_from else None
    end = parse_date(date_to) if date_to else None
    if start and end and start > end:
        raise ValidationError(
            "--from 이 --to 보다 늦습니다.", hint=f"--from {start} / --to {end}"
        )
    wanted_type = parse_type(type) if type else None
    wanted_category = resolve_category(stores.categories, category) if category else None
    # 메모와 태그는 대소문자를 무시해 찾는다. 한글에는 영향이 없고, 영문
    # 메모를 찾을 때 사용자가 대소문자를 정확히 기억하지 않아도 된다.
    keyword = q.strip().casefold() if q else None
    wanted_tag = tag.strip().casefold() if tag else None

    def matches(transaction: Transaction) -> bool:
        if wanted_month and transaction.month != wanted_month:
            return False
        if start and transaction.date < start:
            return False
        if end and transaction.date > end:
            return False
        if wanted_type and transaction.type != wanted_type:
            return False
        if wanted_category and transaction.category != wanted_category:
            return False
        if keyword and keyword not in transaction.memo.casefold():
            return False
        if wanted_tag and wanted_tag not in (t.casefold() for t in transaction.tags):
            return False
        return True

    return islice(filter(matches, stores.transactions.stream_reversed()), limit)


def delete_transaction(stores: Stores, tx_id: str) -> Transaction:
    """거래 한 건을 삭제하고 삭제된 거래를 돌려준다. 없으면 NotFoundError.

    먼저 찾아보고 없으면 그 자리에서 실패한다. 곧바로 재작성부터 하면 없는
    id를 지우라는 요청에도 파일을 통째로 다시 쓰게 되는데, 얻는 것 없이
    위험만 지는 일이다.

    id 비교는 대소문자를 무시한다. 목록에서 눈으로 읽어 옮겨 적는 값이라
    tx-000012로 쳤다고 "없는 거래"라고 답하는 건 불친절하다.
    """
    target = tx_id.strip()
    if not target:
        raise ValidationError("--id 를 입력해야 합니다.", hint="예: --id TX-000012")

    key = target.casefold()
    removed = next((t for t in stores.transactions.stream() if t.id.casefold() == key), None)
    if removed is None:
        raise NotFoundError(f"id={target} 거래를 찾을 수 없습니다.")

    stores.transactions.replace_all(
        t for t in stores.transactions.stream() if t.id.casefold() != key
    )
    return removed


def update_transaction(
    stores: Stores,
    tx_id: str,
    *,
    date: str | None = None,
    type: str | None = None,
    category: str | None = None,
    amount: str | None = None,
    memo: str | None = None,
    tags: str | None = None,
) -> Transaction:
    """지정한 항목만 바꾸고 수정된 거래를 돌려준다. 없으면 NotFoundError.

    None은 "주지 않았다"는 뜻이고 빈 문자열은 "비워라"는 뜻이다. 그래서
    --memo "" 로 메모를 지울 수 있다.

    값은 add와 똑같은 검증 함수를 통과한다. 옵션 방식이라고 검증이 느슨하면
    대화형으로 넣을 수 없는 값이 옵션으로는 들어가는 구멍이 생긴다.

    frozen dataclass라 부분 수정이 아니라 replace로 새 객체를 만든다.
    중간에 실패해도 반쯤 수정된 거래가 남지 않는다.
    """
    changes: dict[str, object] = {}
    if date is not None:
        changes["date"] = parse_date(date)
    if type is not None:
        changes["type"] = parse_type(type)
    if category is not None:
        changes["category"] = resolve_category(stores.categories, category)
    if amount is not None:
        changes["amount"] = parse_amount(amount)
    if memo is not None:
        changes["memo"] = memo.strip()
    if tags is not None:
        changes["tags"] = parse_tags(tags)

    if not changes:
        raise ValidationError(
            "수정할 항목을 하나 이상 지정해야 합니다.",
            hint="예: update --id TX-000012 --amount 20000",
        )

    target = tx_id.strip()
    if not target:
        raise ValidationError("--id 를 입력해야 합니다.", hint="예: --id TX-000012")

    key = target.casefold()
    current = next((t for t in stores.transactions.stream() if t.id.casefold() == key), None)
    if current is None:
        raise NotFoundError(f"id={target} 거래를 찾을 수 없습니다.")

    updated = replace(current, **changes)
    stores.transactions.replace_all(
        updated if t.id.casefold() == key else t for t in stores.transactions.stream()
    )
    return updated


def set_budget(stores: Stores, month: str, amount: str) -> Budget:
    """월 예산을 저장하고 저장된 값을 돌려준다. 이미 있으면 교체한다 (미션 9번).

    금액은 거래와 같은 규칙을 쓴다. 예산에만 0이나 음수를 허용하면 사용률
    계산에서 0으로 나누게 된다.
    """
    normalized = parse_month(month)
    value = parse_amount(amount)
    stores.budgets.set(normalized, value)
    return Budget(normalized, value)


def get_budget(stores: Stores, month: str) -> Budget | None:
    """해당 월 예산. 설정된 적이 없으면 None.

    월을 정규화해서 넘기므로 '2024-1'로 물어도 '2024-01'을 찾는다.
    """
    return stores.budgets.get(parse_month(month))


def list_budgets(stores: Stores) -> Iterator[Budget]:
    """저장된 모든 월 예산을 월 순서대로. cli가 저장소를 직접 만지지 않게 한다."""
    return stores.budgets.stream()


def summarize_month(stores: Stores, month: str, top: int) -> MonthlySummary:
    """한 달 요약을 계산한다 (미션 8번).

    파일을 한 번만 훑는다. 그 달 전체를 봐야 하므로 읽는 양은 줄일 수 없지만,
    메모리에 쌓이는 건 카테고리 개수만큼이지 거래 건수만큼이 아니다.
    10만 건짜리 파일도 Counter에는 카테고리 몇 개만 남는다.

    월 비교는 date[:7]로 한다. 그래서 저장 시점에 날짜를 정규화해 두는 것이
    중요하다 - '2024-1-5'가 그대로 저장되어 있으면 이 비교에서 빠진다.
    """
    if top <= 0:
        raise ValidationError("--top 은 1 이상이어야 합니다.", hint=f"입력값: {top}")

    normalized = parse_month(month)
    count = 0
    income = 0
    expense = 0
    per_category: Counter[str] = Counter()

    for transaction in stores.transactions.stream():
        if transaction.month != normalized:
            continue
        count += 1
        if transaction.type == "income":
            income += transaction.amount
        else:
            expense += transaction.amount
            per_category[transaction.category] += transaction.amount

    budget = stores.budgets.get(normalized)
    return MonthlySummary(
        month=normalized,
        count=count,
        total_income=income,
        total_expense=expense,
        top_expenses=tuple(per_category.most_common(top)),
        budget=budget.amount if budget else None,
    )


def export_transactions(
    stores: Stores,
    out_path: str,
    *,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    """조건에 맞는 거래를 CSV로 내보내고 건수를 돌려준다 (미션 11번).

    조건을 하나 이상 반드시 받는다. 조건 없이 전체를 뽑는 건 실수일 가능성이
    높아 미션이 명시적으로 금지한다.

    csv.DictWriter로 쓴다. tags를 쉼표로 이어붙이므로 값 안에 구분자가 들어가는데,
    직접 문자열을 조립하면 칸이 어긋난다. csv 모듈이 알아서 큰따옴표로 감싼다.

    한 줄씩 흘려 쓴다. 조건에 맞는 전체를 리스트로 모아두지 않으므로 10만 건을
    내보내도 메모리는 일정하다.
    """
    if not (month or date_from or date_to):
        raise ValidationError(
            "--month 또는 --from/--to 중 하나 이상을 지정해야 합니다.",
            hint="예: export --out out.csv --month 2024-01",
        )

    rows = search_transactions(
        stores, limit=None, month=month, date_from=date_from, date_to=date_to
    )
    count = 0
    try:
        # newline="" 은 csv 모듈 권장값이다. 없으면 플랫폼에 따라 빈 줄이 끼어든다.
        with Path(out_path).open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for transaction in rows:
                writer.writerow(
                    {
                        "date": transaction.date,
                        "type": transaction.type,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "memo": transaction.memo,
                        "tags": ",".join(transaction.tags),
                    }
                )
                count += 1
    except OSError as exc:
        # 기본 hint는 --data-dir 를 가리키므로 여기서는 맞지 않는다. --out 경로 문제다.
        raise DataFileError(
            f"CSV 파일에 쓸 수 없습니다: {out_path}",
            hint="--out 의 상위 폴더가 있는지, 쓰기 권한이 있는지 확인하세요.",
        ) from exc
    return count
