# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class MeshComponents:
    id: str

    def __init__(self, id: str) -> None:
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> 'MeshComponents':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        return MeshComponents(id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        return result


def mesh_components_from_dict(s: Any) -> MeshComponents:
    return MeshComponents.from_dict(s)


def mesh_components_to_dict(x: MeshComponents) -> Any:
    return to_class(MeshComponents, x)
