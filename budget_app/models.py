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
