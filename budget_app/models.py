"""데이터 모델.

모든 모델은 frozen dataclass다. 거래를 불변으로 다루면 update가
"부분 수정"이 아니라 "새 객체로 교체"가 되므로, 중간에 실패해도
반쯤 수정된 상태가 남지 않는다.

to_dict/from_dict는 저장 포맷(JSONL)과 객체 사이의 유일한 경계다.
저장 계층은 이 두 함수만 알면 되고, 서비스 계층은 dict를 볼 일이 없다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import ValidationError

TRANSACTION_TYPES: tuple[str, ...] = ("income", "expense")
ID_PREFIX = "TX-"
ID_WIDTH = 6


def format_id(seq: int) -> str:
    """1 -> 'TX-000001'"""
    return f"{ID_PREFIX}{seq:0{ID_WIDTH}d}"


def parse_id(value: str) -> int | None:
    """'TX-000001' -> 1. 형식이 다르면 None (손상된 줄을 건너뛰기 위함)."""
    if not value.startswith(ID_PREFIX):
        return None
    try:
        return int(value[len(ID_PREFIX):])
    except ValueError:
        return None


@dataclass(frozen=True)
class Transaction:
    """거래 한 건. tags는 불변성을 위해 tuple로 보관한다."""

    id: str
    date: str  # YYYY-MM-DD (문자열 정렬 == 날짜 정렬이라 그대로 비교에 쓴다)
    type: str  # income | expense
    category: str
    amount: int  # 양수 정수(원 단위). float 누적 오차를 피하려 int로 고정
    memo: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def month(self) -> str:
        """'2024-01-15' -> '2024-01'"""
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
        """저장된 한 줄을 객체로 복원. 필수 필드가 없으면 ValidationError."""
        missing = [k for k in ("id", "date", "type", "category", "amount") if k not in raw]
        if missing:
            raise ValidationError(f"필수 필드가 없습니다: {', '.join(missing)}")
        tags = raw.get("tags") or ()
        if isinstance(tags, str):  # CSV 등 외부 유입 대비
            tags = tuple(t.strip() for t in tags.split(",") if t.strip())
        return cls(
            id=str(raw["id"]),
            date=str(raw["date"]),
            type=str(raw["type"]),
            category=str(raw["category"]),
            amount=int(raw["amount"]),
            memo=str(raw.get("memo") or ""),
            tags=tuple(str(t) for t in tags),
        )


@dataclass(frozen=True)
class Category:
    """카테고리. 지금은 이름만 갖지만 별도 파일/모델로 분리해 두면
    나중에 색상·상위 카테고리 등을 붙일 때 저장 스키마만 확장하면 된다."""

    name: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Category:
        if "name" not in raw:
            raise ValidationError("카테고리 파일에 name 필드가 없습니다.")
        return cls(name=str(raw["name"]))


@dataclass(frozen=True)
class Budget:
    """월 예산. month는 'YYYY-MM'."""

    month: str
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Budget:
        missing = [k for k in ("month", "amount") if k not in raw]
        if missing:
            raise ValidationError(f"예산 파일에 필드가 없습니다: {', '.join(missing)}")
        return cls(month=str(raw["month"]), amount=int(raw["amount"]))
