"""저장소 계층: JSONL 파일 I/O.

읽기는 항상 제너레이터다. JSONL은 "1줄 = 1레코드"라서 파일을 끝까지
읽지 않고 앞에서부터 필요한 만큼만 꺼내 쓸 수 있다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .errors import DataFileError
from .models import Transaction


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
    """
    if not path.exists():
        return
    try:
        with path.open(encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if line:  # 끝의 빈 줄이나 손으로 넣은 공백 줄은 건너뛴다
                    yield json.loads(line)
    except OSError as exc:
        raise DataFileError(f"저장 파일을 읽을 수 없습니다: {path}") from exc


class TransactionRepository:
    """transactions.jsonl 담당."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream(self) -> Iterator[Transaction]:
        """저장된 거래를 파일에 기록된 순서대로 흘려보낸다."""
        return (Transaction.from_dict(raw) for raw in read_jsonl(self.path))
