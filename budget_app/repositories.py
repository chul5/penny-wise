"""저장소 계층: JSONL 파일 I/O.

읽기는 항상 제너레이터다. JSONL은 "1줄 = 1레코드"라서 파일을 끝까지
읽지 않고 필요한 만큼만 꺼내 쓸 수 있다. 앞에서부터든(read_jsonl),
뒤에서부터든(read_jsonl_reversed) 마찬가지다.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from .errors import DataFileError, ValidationError
from .models import Budget, Category, Transaction, format_id, parse_id

CHUNK_SIZE = 64 * 1024


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


def parse_line(line: str, path: Path, where: str) -> dict[str, Any] | None:
    """JSON 한 줄을 파싱한다. 깨졌으면 경고하고 None을 준다.

    한 줄 때문에 전체 조회가 실패하면 사용자가 나머지 데이터를 되살릴
    방법이 없다. 그래서 예외를 올리지 않고 건너뛴다.
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        warn(f"{path.name} {where}이 JSON 형식이 아닙니다 - 건너뜁니다")
        return None


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """파일을 앞에서부터 한 줄씩 읽어 dict로 yield 한다.

    return이 아니라 yield라서, 호출 즉시 읽는 게 아니라 소비자가 하나씩
    꺼낼 때마다 다음 줄을 읽는다. 없는 파일은 빈 스트림으로 취급한다.
    """
    if not path.exists():
        return
    try:
        with path.open(encoding="utf-8") as fp:
            for lineno, line in enumerate(fp, start=1):
                line = line.strip()
                if not line:  # 끝의 빈 줄이나 손으로 넣은 공백 줄
                    continue
                record = parse_line(line, path, f"{lineno}번째 줄")
                if record is not None:
                    yield record
    except OSError as exc:
        raise DataFileError(f"저장 파일을 읽을 수 없습니다: {path}") from exc


def read_jsonl_reversed(path: Path, chunk_size: int = CHUNK_SIZE) -> Iterator[dict[str, Any]]:
    """파일을 뒤에서부터 한 줄씩 읽어 dict로 yield 한다.

    "최신순 출력"을 위해 필요하다. 전체를 읽어 정렬하면 파일이 커질수록
    메모리를 그만큼 먹는데, append-only 파일은 뒤가 곧 최근이므로
    끝에서부터 읽으면 --limit 만큼만 읽고 멈출 수 있다.

    seek으로 끝에서 chunk_size 바이트씩 거꾸로 읽는다. 청크 경계가 줄
    중간을 자를 수 있으므로, 각 청크의 첫 조각은 다음(더 앞쪽) 청크와
    이어붙일 때까지 들고 있는다.

    바이트 단위로 b"\\n"에서 자르는 게 안전한 이유: UTF-8은 멀티바이트
    문자 안에 0x0A(개행)가 절대 나타나지 않게 설계되어 있다.
    """
    if not path.exists():
        return
    try:
        with path.open("rb") as fp:
            pos = fp.seek(0, os.SEEK_END)
            head = b""  # 아직 완성되지 않은 맨 앞 조각
            while pos > 0:
                size = min(chunk_size, pos)
                pos -= size
                fp.seek(pos)
                lines = (fp.read(size) + head).split(b"\n")
                head = lines.pop(0)  # 앞쪽 청크와 이어질 수 있으니 보류
                for line in reversed(lines):
                    text = line.decode("utf-8").strip()
                    if not text:
                        continue
                    record = parse_line(text, path, "한 줄")
                    if record is not None:
                        yield record
            text = head.decode("utf-8").strip()  # 파일의 첫 줄
            if text:
                record = parse_line(text, path, "1번째 줄")
                if record is not None:
                    yield record
    except OSError as exc:
        raise DataFileError(f"저장 파일을 읽을 수 없습니다: {path}") from exc


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """레코드 한 줄을 파일 끝에 덧붙인다.

    JSONL이 append에 강한 게 이 포맷을 고른 이유다. 기존 내용을 다시 쓰지
    않으므로 파일이 커져도 추가 비용이 일정하고, 쓰다 죽어도 앞부분은 온전하다.
    """
    ensure_file(path)
    try:
        # 마지막 줄에 개행이 없으면(손으로 편집한 경우) 두 레코드가 한 줄로
        # 붙어버린다. 그러면 두 건이 모두 깨지므로 개행을 먼저 보충한다.
        #
        # 마지막 1바이트만 확인한다. read_bytes()로 전체를 읽으면 import처럼
        # 여러 건을 연달아 append할 때 매번 파일을 통째로 읽어 O(N^2)이 된다.
        needs_newline = False
        if path.stat().st_size > 0:
            with path.open("rb") as probe:
                probe.seek(-1, os.SEEK_END)
                needs_newline = probe.read(1) != b"\n"
        with path.open("a", encoding="utf-8") as fp:
            if needs_newline:
                fp.write("\n")
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise DataFileError(f"저장 파일에 쓸 수 없습니다: {path}") from exc


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """전체를 임시 파일에 쓰고 원자적으로 교체한다. 반환값은 쓴 건수.

    파일 기반 저장에는 롤백해 줄 DB 엔진이 없다. 원본을 직접 고치다가
    중간에 죽으면 파일이 반쯤 망가진 상태로 남는다. 그래서 새 파일을 완성한
    뒤 os.replace로 한 번에 갈아끼운다 - 성공하면 새 파일, 실패하면 원본
    그대로이고 중간 상태가 없다.

    임시 파일은 반드시 같은 폴더에 만든다. os.replace의 원자성은 같은
    파일시스템 안에서만 보장된다.
    """
    ensure_file(path)
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, prefix=path.name, suffix=".tmp",
            delete=False, encoding="utf-8",
        ) as fp:
            tmp = Path(fp.name)
            count = 0
            for record in records:
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
            fp.flush()
            os.fsync(fp.fileno())  # 디스크에 내려간 뒤 교체해야 의미가 있다
        os.replace(tmp, path)
        return count
    except OSError as exc:
        raise DataFileError(f"저장 파일을 다시 쓸 수 없습니다: {path}") from exc
    finally:
        # 교체가 성공했으면 tmp는 이미 사라졌다. 실패했을 때만 남아서 지워진다.
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def load_models(raws: Iterable[dict[str, Any]], loader: Any, path: Path) -> Iterator[Any]:
    """dict 스트림을 모델 스트림으로 바꾼다. 필드가 빠진 건은 건너뛴다.

    반환 타입이 느슨한 대신, 호출하는 메서드 쪽에서 Iterator[Category]처럼
    정확한 타입을 선언한다. 사용하는 쪽 계약이 정확하면 그걸로 충분하다.
    """
    for raw in raws:
        try:
            yield loader(raw)
        except ValidationError as exc:
            warn(f"{path.name}: {exc.message} - 건너뜁니다")


class TransactionRepository:
    """transactions.jsonl 담당."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream(self) -> Iterator[Transaction]:
        """저장된 거래를 파일에 기록된 순서대로 흘려보낸다."""
        return load_models(read_jsonl(self.path), Transaction.from_dict, self.path)

    def stream_reversed(self) -> Iterator[Transaction]:
        """저장된 거래를 기록의 역순(= 최근 입력순)으로 흘려보낸다."""
        return load_models(read_jsonl_reversed(self.path), Transaction.from_dict, self.path)

    def next_id(self) -> str:
        """다음에 쓸 거래 id를 만든다.

        항상 append하므로 파일 맨 뒤 레코드가 가장 큰 번호를 갖는다. 덕분에
        전체를 훑지 않고 뒤에서 한 건만 읽으면 된다.

        주의: 가장 최근 거래를 지우면 그 번호가 다시 쓰인다. 남아 있는
        거래끼리는 여전히 유일하므로 그대로 둔다. 번호를 절대 재사용하지
        않으려면 카운터를 따로 저장해야 하는데, 그 복잡도를 살 만한 이득이 없다.
        """
        for transaction in self.stream_reversed():
            seq = parse_id(transaction.id)
            if seq is not None:
                return format_id(seq + 1)
        return format_id(1)

    def append(self, transaction: Transaction) -> None:
        """거래 한 건을 파일 끝에 저장한다."""
        append_jsonl(self.path, transaction.to_dict())

    def replace_all(self, transactions: Iterable[Transaction]) -> int:
        """파일 내용을 주어진 거래들로 통째로 교체한다. 반환값은 저장된 건수.

        update/delete/카테고리 치환이 모두 이 메서드를 재사용한다.
        stream()으로 읽으면서 동시에 넘겨도 안전하다 - 쓰기는 임시 파일에
        일어나고, 원본은 교체 직전까지 손대지 않는다.
        """
        return write_jsonl(self.path, (t.to_dict() for t in transactions))


class CategoryStore:
    """categories.jsonl 담당.

    거래와 달리 카테고리는 수가 적고 add 할 때마다 중복 확인이 필요해서
    names()로 한 번에 읽는 쪽이 자연스럽다. 스트리밍이 목적이 아니라
    "등록된 목록"이 목적인 데이터다.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream(self) -> Iterator[Category]:
        """저장된 카테고리를 등록 순서대로 흘려보낸다."""
        return load_models(read_jsonl(self.path), Category.from_dict, self.path)

    def names(self) -> list[str]:
        """등록된 카테고리 이름 목록. 중복은 등록 순서를 지키며 제거한다."""
        return list(dict.fromkeys(category.name for category in self.stream()))

    def append(self, name: str) -> None:
        """카테고리 하나를 파일 끝에 저장한다. 중복 검사는 서비스 계층 몫이다."""
        append_jsonl(self.path, Category(name).to_dict())

    def replace_all(self, names: Iterable[str]) -> int:
        """카테고리 목록을 통째로 교체한다. 반환값은 저장된 건수."""
        return write_jsonl(self.path, (Category(name).to_dict() for name in names))


class BudgetStore:
    """budgets.jsonl 담당. 한 달에 한 줄이다."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def stream(self) -> Iterator[Budget]:
        """저장된 월 예산을 월 순서대로 흘려보낸다."""
        return load_models(read_jsonl(self.path), Budget.from_dict, self.path)

    def get(self, month: str) -> Budget | None:
        """해당 월 예산. 설정된 적이 없으면 None.

        summary가 "예산이 있으면 사용률을 보여준다"로 동작하므로,
        없는 상태를 예외가 아니라 None으로 표현한다.
        """
        for budget in self.stream():
            if budget.month == month:
                return budget
        return None

    def set(self, month: str, amount: int) -> None:
        """해당 월 예산을 저장한다. 이미 있으면 교체한다.

        append하면 같은 달이 두 줄로 남아 어느 쪽이 맞는지 알 수 없게 된다.
        그래서 전체를 다시 쓴다. 월 예산은 한 달에 한 줄뿐이라 다시 쓰는
        비용이 문제되지 않는다. 파일은 월 순으로 정렬해 둔다.
        """
        others = [b for b in self.stream() if b.month != month]
        self.replace_all(sorted(others + [Budget(month, amount)], key=lambda b: b.month))

    def replace_all(self, budgets: Iterable[Budget]) -> int:
        """예산 목록을 통째로 교체한다. 반환값은 저장된 건수."""
        return write_jsonl(self.path, (budget.to_dict() for budget in budgets))


@dataclass(frozen=True, slots=True)
class Stores:
    """저장소 세 개를 한 묶음으로 들고 다닌다.

    핸들러마다 필요한 저장소가 달라서 인자를 따로 받으면 시그니처가 제각각이
    된다. 한 묶음으로 넘기면 모든 핸들러가 (args, stores) 형태로 통일된다.
    """

    transactions: TransactionRepository
    categories: CategoryStore
    budgets: BudgetStore


def open_stores(data_dir: str | Path) -> Stores:
    """저장 폴더 경로에서 저장소 세 개를 만든다.

    파일은 여기서 만들지 않는다. 쓸 때 append/write가 알아서 생성하고,
    읽을 때 없는 파일은 빈 스트림으로 취급하기 때문이다. 조회만 했는데
    파일이 생기는 건 사용자가 기대하지 않는 동작이다.
    """
    if not str(data_dir).strip():
        # 빈 경로는 Path("")가 되어 현재 폴더에 파일을 흘린다. 조용히 엉뚱한
        # 곳에 저장하는 것보다 바로 알려주는 게 낫다.
        raise DataFileError(
            "--data-dir 경로가 비어 있습니다.", hint="예: --data-dir ./data"
        )
    base = Path(data_dir)
    return Stores(
        transactions=TransactionRepository(base / "transactions.jsonl"),
        categories=CategoryStore(base / "categories.jsonl"),
        budgets=BudgetStore(base / "budgets.jsonl"),
    )
