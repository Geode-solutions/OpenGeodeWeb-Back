# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class TextureCoordinates:
    id: str

    def __init__(self, id: str) -> None:
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> "TextureCoordinates":
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        return TextureCoordinates(id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        return result


def texture_coordinates_from_dict(s: Any) -> TextureCoordinates:
    return TextureCoordinates.from_dict(s)


def texture_coordinates_to_dict(x: TextureCoordinates) -> Any:
    return to_class(TextureCoordinates, x)
