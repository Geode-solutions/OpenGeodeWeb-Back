# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class InspectFile:
    filename: str
    input_geode_object: str

    def __init__(self, filename: str, input_geode_object: str) -> None:
        self.filename = filename
        self.input_geode_object = input_geode_object

    @staticmethod
    def from_dict(obj: Any) -> 'InspectFile':
        assert isinstance(obj, dict)
        filename = from_str(obj.get("filename"))
        input_geode_object = from_str(obj.get("input_geode_object"))
        return InspectFile(filename, input_geode_object)

    def to_dict(self) -> dict:
        result: dict = {}
        result["filename"] = from_str(self.filename)
        result["input_geode_object"] = from_str(self.input_geode_object)
        return result


def inspect_file_from_dict(s: Any) -> InspectFile:
    return InspectFile.from_dict(s)


def inspect_file_to_dict(x: InspectFile) -> Any:
    return to_class(InspectFile, x)
