# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Kill:
    pass

    def __init__(
        self,
    ) -> None:
        pass

    @staticmethod
    def from_dict(obj: Any) -> "Kill":
        assert isinstance(obj, dict)
        return Kill()

    def to_dict(self) -> dict:
        result: dict = {}
        return result


def kill_from_dict(s: Any) -> Kill:
    return Kill.from_dict(s)


def kill_to_dict(x: Kill) -> Any:
    return to_class(Kill, x)
