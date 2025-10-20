# type: ignore
from typing import Any, Optional, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Point:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'Point':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return Point(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        return result


class CreateAoi:
    id: Optional[str]
    name: str
    """Name of the AOI"""

    points: List[Point]
    z: float

    def __init__(self, id: Optional[str], name: str, points: List[Point], z: float) -> None:
        self.id = id
        self.name = name
        self.points = points
        self.z = z

    @staticmethod
    def from_dict(obj: Any) -> 'CreateAoi':
        assert isinstance(obj, dict)
        id = from_union([from_str, from_none], obj.get("id"))
        name = from_str(obj.get("name"))
        points = from_list(Point.from_dict, obj.get("points"))
        z = from_float(obj.get("z"))
        return CreateAoi(id, name, points, z)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = from_union([from_str, from_none], self.id)
        result["name"] = from_str(self.name)
        result["points"] = from_list(lambda x: to_class(Point, x), self.points)
        result["z"] = to_float(self.z)
        return result


def create_aoi_from_dict(s: Any) -> CreateAoi:
    return CreateAoi.from_dict(s)


def create_aoi_to_dict(x: CreateAoi) -> Any:
    return to_class(CreateAoi, x)
