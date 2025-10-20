# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class CreatePoint:
    name: str
    x: float
    y: float
    z: float

    def __init__(self, name: str, x: float, y: float, z: float) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_dict(obj: Any) -> 'CreatePoint':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        z = from_float(obj.get("z"))
        return CreatePoint(name, x, y, z)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        result["z"] = to_float(self.z)
        return result


def create_point_from_dict(s: Any) -> CreatePoint:
    return CreatePoint.from_dict(s)


def create_point_to_dict(x: CreatePoint) -> Any:
    return to_class(CreatePoint, x)
