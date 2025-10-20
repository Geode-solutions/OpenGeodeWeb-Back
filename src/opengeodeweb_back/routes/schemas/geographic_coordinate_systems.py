# type: ignore
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class GeographicCoordinateSystems:
    input_geode_object: str

    def __init__(self, input_geode_object: str) -> None:
        self.input_geode_object = input_geode_object

    @staticmethod
    def from_dict(obj: Any) -> 'GeographicCoordinateSystems':
        assert isinstance(obj, dict)
        input_geode_object = from_str(obj.get("input_geode_object"))
        return GeographicCoordinateSystems(input_geode_object)

    def to_dict(self) -> dict:
        result: dict = {}
        result["input_geode_object"] = from_str(self.input_geode_object)
        return result


def geographic_coordinate_systems_from_dict(s: Any) -> GeographicCoordinateSystems:
    return GeographicCoordinateSystems.from_dict(s)


def geographic_coordinate_systems_to_dict(x: GeographicCoordinateSystems) -> Any:
    return to_class(GeographicCoordinateSystems, x)
