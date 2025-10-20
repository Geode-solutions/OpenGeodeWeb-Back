# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class GeodeObjectsAndOutputExtensions:
    filename: str
    input_geode_object: str

    def __init__(self, filename: str, input_geode_object: str) -> None:
        self.filename = filename
        self.input_geode_object = input_geode_object

    @staticmethod
    def from_dict(obj: Any) -> "GeodeObjectsAndOutputExtensions":
        assert isinstance(obj, dict)
        filename = from_str(obj.get("filename"))
        input_geode_object = from_str(obj.get("input_geode_object"))
        return GeodeObjectsAndOutputExtensions(filename, input_geode_object)

    def to_dict(self) -> dict:
        result: dict = {}
        result["filename"] = from_str(self.filename)
        result["input_geode_object"] = from_str(self.input_geode_object)
        return result


def geode_objects_and_output_extensions_from_dict(
    s: Any,
) -> GeodeObjectsAndOutputExtensions:
    return GeodeObjectsAndOutputExtensions.from_dict(s)


def geode_objects_and_output_extensions_to_dict(
    x: GeodeObjectsAndOutputExtensions,
) -> Any:
    return to_class(GeodeObjectsAndOutputExtensions, x)
