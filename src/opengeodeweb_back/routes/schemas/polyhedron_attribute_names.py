# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class PolyhedronAttributeNames:
    id: str

    def __init__(self, id: str) -> None:
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> "PolyhedronAttributeNames":
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        return PolyhedronAttributeNames(id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        return result


def polyhedron_attribute_names_from_dict(s: Any) -> PolyhedronAttributeNames:
    return PolyhedronAttributeNames.from_dict(s)


def polyhedron_attribute_names_to_dict(x: PolyhedronAttributeNames) -> Any:
    return to_class(PolyhedronAttributeNames, x)
