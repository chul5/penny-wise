"""데이터 모델.

거래는 frozen dataclass다. update가 "부분 수정"이 아니라 "새 객체로 교체"가
되므로 중간에 실패해도 반쯤 수정된 상태가 남지 않는다.
to_dict/from_dict는 저장 포맷(JSONL)과 객체 사이의 유일한 경계다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import ValidationError

TRANSACTION_TYPES = ("income", "expense")
ID_PREFIX = "TX-"


def format_id(seq: int) -> str:
    """1 -> 'TX-000001'"""
    return f"{ID_PREFIX}{seq:06d}"


def parse_id(value: str) -> int | None:
    """'TX-000001' -> 1. 형식이 다르면 None."""
    if not value.startswith(ID_PREFIX):
        return None
    try:
        return int(value[len(ID_PREFIX):])
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class Transaction:
    id: str
    date: str  # YYYY-MM-DD (문자열 정렬 == 날짜 정렬)
    type: str  # income | expense
    category: str
    amount: int  # 양수 정수(원). float 누적 오차를 피한다
    memo: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def month(self) -> str:
        return self.date[:7]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "memo": self.memo,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Transaction:
        tags = raw.get("tags") or ()
        if isinstance(tags, str):  # CSV 유입 대비
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        try:
            return cls(
                id=str(raw["id"]),
                date=str(raw["date"]),
                type=str(raw["type"]),
                category=str(raw["category"]),
                amount=int(raw["amount"]),
                memo=str(raw.get("memo") or ""),
                tags=tuple(str(t) for t in tags),
            )
        except KeyError as exc:
            raise ValidationError(f"필수 필드가 없습니다: {exc.args[0]}") from exc


@dataclass(frozen=True, slots=True)
class Category:
    name: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Category:
        try:
            return cls(name=str(raw["name"]))
        except KeyError as exc:
            raise ValidationError(f"카테고리 파일에 필드가 없습니다: {exc.args[0]}") from exc


@dataclass(frozen=True, slots=True)
class Budget:
    month: str  # YYYY-MM
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Budget:
        try:
            return cls(month=str(raw["month"]), amount=int(raw["amount"]))
        except KeyError as exc:
            raise ValidationError(f"예산 파일에 필드가 없습니다: {exc.args[0]}") from exc


@dataclass(frozen=True, slots=True)
class MonthlySummary:
    """한 달 요약. 저장되는 데이터가 아니라 계산 결과다.

    dataclass로 고정해 두면 서비스가 무엇을 돌려주고 CLI가 무엇을 출력할지가
    타입으로 드러난다. dict로 넘기면 키 이름 오타가 실행 시점까지 안 잡힌다.

    계산으로 얻을 수 있는 값(잔액, 사용률)은 필드로 저장하지 않고 property로
    둔다. 같은 사실을 두 군데 저장하면 어긋날 수 있다.
    """

    month: str  # YYYY-MM
    count: int  # 그 달에 해당하는 거래 건수
    total_income: int
    total_expense: int
    top_expenses: tuple[tuple[str, int], ...]  # (카테고리, 합계) 내림차순
    budget: int | None = None  # 설정되지 않았으면 None

    @property
    def balance(self) -> int:
        return self.total_income - self.total_expense

    @property
    def is_empty(self) -> bool:
        """그 달 거래가 한 건도 없는지. 미션 8번의 "데이터 없음" 판단 기준."""
        return self.count == 0

    @property
    def usage_rate(self) -> float | None:
        """예산 대비 지출 비율(%). 예산이 없으면 None."""
        if self.budget is None:
            return None
        return self.total_expense / self.budget * 100

    @property
    def over_budget(self) -> bool:
        return self.budget is not None and self.total_expense > self.budget
