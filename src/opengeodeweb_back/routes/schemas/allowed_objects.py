# type: ignore
from typing import Optional, Any, TypeVar, Type, cast


T = TypeVar("T")


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


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class AllowedObjects:
    filename: str
    supported_feature: Optional[str]

    def __init__(self, filename: str, supported_feature: Optional[str]) -> None:
        self.filename = filename
        self.supported_feature = supported_feature

    @staticmethod
    def from_dict(obj: Any) -> 'AllowedObjects':
        assert isinstance(obj, dict)
        filename = from_str(obj.get("filename"))
        supported_feature = from_union([from_none, from_str], obj.get("supported_feature"))
        return AllowedObjects(filename, supported_feature)

    def to_dict(self) -> dict:
        result: dict = {}
        result["filename"] = from_str(self.filename)
        result["supported_feature"] = from_union([from_none, from_str], self.supported_feature)
        return result


def allowed_objects_from_dict(s: Any) -> AllowedObjects:
    return AllowedObjects.from_dict(s)


def allowed_objects_to_dict(x: AllowedObjects) -> Any:
    return to_class(AllowedObjects, x)
