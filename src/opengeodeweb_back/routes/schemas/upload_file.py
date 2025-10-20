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


class UploadFile:
    filename: Optional[str]

    def __init__(self, filename: Optional[str]) -> None:
        self.filename = filename

    @staticmethod
    def from_dict(obj: Any) -> 'UploadFile':
        assert isinstance(obj, dict)
        filename = from_union([from_str, from_none], obj.get("filename"))
        return UploadFile(filename)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.filename is not None:
            result["filename"] = from_union([from_str, from_none], self.filename)
        return result


def upload_file_from_dict(s: Any) -> UploadFile:
    return UploadFile.from_dict(s)


def upload_file_to_dict(x: UploadFile) -> Any:
    return to_class(UploadFile, x)
