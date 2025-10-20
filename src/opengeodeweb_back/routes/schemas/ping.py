# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Ping:
    pass

    def __init__(self, ) -> None:
        pass

    @staticmethod
    def from_dict(obj: Any) -> 'Ping':
        assert isinstance(obj, dict)
        return Ping()

    def to_dict(self) -> dict:
        result: dict = {}
        return result


def ping_from_dict(s: Any) -> Ping:
    return Ping.from_dict(s)


def ping_to_dict(x: Ping) -> Any:
    return to_class(Ping, x)
