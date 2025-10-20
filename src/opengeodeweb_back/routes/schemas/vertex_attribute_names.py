# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class VertexAttributeNames:
    id: str

    def __init__(self, id: str) -> None:
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> 'VertexAttributeNames':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        return VertexAttributeNames(id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        return result


def vertex_attribute_names_from_dict(s: Any) -> VertexAttributeNames:
    return VertexAttributeNames.from_dict(s)


def vertex_attribute_names_to_dict(x: VertexAttributeNames) -> Any:
    return to_class(VertexAttributeNames, x)
