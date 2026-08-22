"""저장소 계층: JSONL 파일 I/O.

읽기는 항상 제너레이터다. JSONL은 "1줄 = 1레코드"라서 파일을 끝까지
읽지 않고 앞에서부터 필요한 만큼만 꺼내 쓸 수 있다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

from .errors import DataFileError, ValidationError
from .models import Transaction


def warn(message: str) -> None:
    """건너뛴 데이터를 알린다. 한 줄이 깨져도 조회 전체는 계속된다."""
    print(f"[경고] {message}", file=sys.stderr)


def ensure_file(path: Path) -> None:
    """파일이 없으면 상위 폴더까지 만들고 빈 파일을 생성한다."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    except OSError as exc:
        raise DataFileError(f"저장 파일을 만들 수 없습니다: {path}") from exc


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """파일을 한 줄씩 읽어 dict로 yield 한다.

    return이 아니라 yield라서, 호출 즉시 읽는 게 아니라 소비자가 하나씩
    꺼낼 때마다 다음 줄을 읽는다. 없는 파일은 빈 스트림으로 취급한다.
    깨진 줄은 경고만 남기고 건너뛴다 - 한 줄 때문에 전체 조회가 실패하면
    사용자가 데이터를 되살릴 방법이 없다.
    """
    if not path.exists():
        return
    try:
        with path.open(encoding="utf-8") as fp:
            for lineno, line in enumerate(fp, start=1):
                line = line.strip()
                if not line:  # 끝의 빈 줄이나 손으로 넣은 공백 줄
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    warn(f"{path.name} {lineno}번째 줄이 JSON 형식이 아닙니다 - 건너뜁니다")
    except OSError as exc:
        raise DataFileError(f"저장 파일을 읽을 수 없습니다: {path}") from exc


class TransactionRepository:
    """transactions.jsonl 담당."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream(self) -> Iterator[Transaction]:
        """저장된 거래를 파일에 기록된 순서대로 흘려보낸다."""
        for raw in read_jsonl(self.path):
            try:
                yield Transaction.from_dict(raw)
            except ValidationError as exc:
                warn(f"{self.path.name}: {exc.message} - 건너뜁니다")
