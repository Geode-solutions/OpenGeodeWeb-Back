# Standard library imports
from typing import Literal, get_args, cast

# Third party imports

# Local application imports


GeodeSurfaceMeshType = Literal["PolygonalSurface3D"]
GeodeMeshType = Literal["VertexSet"] | GeodeSurfaceMeshType
GeodeModelType = Literal["BRep"]
GeodeObjectType = GeodeMeshType | GeodeModelType


def _flatten_literal_args(literal: object) -> tuple[str, ...]:
    flattened: list[str] = []
    for arg in get_args(literal):
        if isinstance(arg, str):
            flattened.append(arg)
        else:
            flattened.extend(_flatten_literal_args(arg))
    return tuple(flattened)


GeodeSurfaceMeshType_values = _flatten_literal_args(GeodeSurfaceMeshType)
GeodeMeshType_values = _flatten_literal_args(GeodeMeshType)
GeodeModelType_values = _flatten_literal_args(GeodeModelType)
GeodeObjectType_values = _flatten_literal_args(GeodeObjectType)


def geode_object_type(value: str) -> GeodeObjectType:
    if value not in GeodeObjectType_values:
        raise ValueError(
            f"Invalid GeodeObjectType: {value!r}. Must be one of {allowed}"
        )
    return cast(GeodeObjectType, value)


def geode_mesh_type(value: str) -> GeodeMeshType:
    if value not in GeodeMeshType_values:
        raise ValueError(f"Invalid GeodeMeshType: {value!r}. Must be one of {allowed}")
    return cast(GeodeMeshType, value)


def geode_model_type(value: str) -> GeodeModelType:
    if value not in GeodeModelType_values:
        raise ValueError(f"Invalid GeodeModelType: {value!r}. Must be one of {allowed}")
    return cast(GeodeModelType, value)


ViewerType = Literal["mesh", "model"]
