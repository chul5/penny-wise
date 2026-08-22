# 1. 개요
학습하면서 궁금한 것들을 정리한 문서

# 2 질문들

## 1 타입힌트
"이 변수/인자/반환값은 이런 타입이다"를 코드에 적어두는 주석 같은 표기입니다. 파이썬은 원래 타입을 안 적어도 되는데, 적을 수 있게 문법을 열어준 것입니다.

- 타입 힌트 없음 — seq가 뭔지, 뭘 돌려주는지 코드를 읽어야 안다
```
def format_id(seq):
    return f"TX-{seq:06d}"
```
- 타입 힌트 있음 — 시그니처만 봐도 계약이 보인다
```
def format_id(seq: int) -> str:
    return f"TX-{seq:06d}"
```
왜 쓰는가 (미션 과제 목표 5번이 요구하는 답)
from_dict를 예로 들면:

def from_dict(cls, raw: Mapping[str, Any]) -> Transaction:
이 한 줄이 없으면 호출하는 쪽에서 "raw에 뭘 넣어야 하지? 리스트를 넣나? 반환값이 Transaction인가 dict인가?"를 알려면 함수 본문을 다 읽어야 합니다. 있으면 시그니처만 보고 씁니다.

가장 실질적인 이득 세 가지:

1. IDE 자동완성 — t. 만 쳐도 t.month, t.amount가 뜹니다. 타입을 모르면 IDE가 뭘 제안할지 알 수 없습니다.
2. 오타/실수를 실행 전에 잡음 — t.amont를 쓰면 실행하지 않아도 에디터가 빨간 줄을 긋습니다.
3. 리팩터링 안전망 — amount를 int에서 Decimal로 바꾸면, 영향받는 모든 지점을 도구가 찾아줍니다.

2단계(저장소)에서 특히 중요해집니다. -> list[Transaction]과 -> Iterator[Transaction]은 겉보기엔 둘 다 for로 돌 수 있지만, 전자는 "메모리에 전부 올렸다", 후자는 "스트리밍이다"라는 완전히 다른 의미입니다. "제너레이터로 처리한다"는 설계 의도를 타입으로 못 박는 것 — 이게 이 과제에서 타입 힌트가 하는 가장 중요한 역할입니다.

## 2. 제너레이터
제너레이터는, 데이터를 한번에 빵하고 불러오는 게 아니라 실시간으로 하나씩 생성하는 특수한 이터레이터다.

- return : 모든 결과를 한꺼번에 담아서 반환하고 함수 종료
- yield : next()로 값을 요구받을 때만 코드를 한 줄씩 실행. 호출되는 순간 스택프레임이 힙메모리 영역에 제너레이터 객체로 저장된다. -> 메모리에선 EOF or break or Error 가 터졌을 때 제거한다.

전체 데이터를 한 번에 메모리에 올리지 않고 필요할 때 한 건씩 사용하는 지연평가를 사용하여 대용량 파일 처리할 때 용이


## 3. with self._path.open(encoding="utf-8") as fp:
fp는 파일포인터인데, 열린 파일에 대한 정보를 담는 객체를 가리킨다.
- 파일디스크립터
- offset 등

fp는 내부적으로 __next()__, __iter()__ 함수가 구현되어 있어서 for line in fp 형태로 순회하면 내부 포인터를 이동시키며 한 줄씩 스트리밍으로 읽어온다.

## 4. Decorator
데코레이터란, AOP(Aspect Oriented Programming) 관점지향 프로그래밍과 같다.
만약, 각 메서드의 병목을 파악하기 위해서, 걸린 시간을 측정하기 위해서 모든 매서드에 시작, 끝 함수를 계산해서 넣으면 매우 끔찍한 일일 것이다. 

데코레이터가 없을 때 코드
```
def process_transaction(tx):
    # [부가 기능 1] 시간 측정 시작
    start = time.time()
    # [부가 기능 2] 인증 체크
    if not is_authenticated():
        raise PermissionError()

    # === [핵심 로직] ===
    db.save(tx)
    # ==================

    # [부가 기능 1] 시간 측정 종료
    print(f"Elapsed: {time.time() - start}")
```

그래서 비지니스로직과 부가기능을 분리하여 사용하고, 부가기능을 감싸서 실행을 지원한다.
위 코드를 다음과 같이 바꿀 수 있다.

```
import functools
import time


# 공통 부가 기능 정의 (스프링의 Aspect / Around Advice 역할)
def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()  # [Before]

        result = func(*args, **kwargs)  # [Target 실행]

        print(
            f"[{func.__name__}] 소요 시간: {time.time() - start:.4f}초"
        )  # [After]
        return result

    return wrapper


# 핵심 비즈니스 로직에 씌우기
@log_execution_time
def process_transaction(tx):
    db.save(tx)  # 순수 비즈니스 로직만 남음
```