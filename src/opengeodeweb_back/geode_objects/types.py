# Standard library imports
from typing import Literal, get_args, cast

# Third party imports

# Local application imports


GeodeSurfaceMeshType = Literal[
    "PolygonalSurface2D",
    "PolygonalSurface3D",
    "TriangulatedSurface2D",
    "TriangulatedSurface3D",
    "RegularGrid2D",
]
GeodeSolidMeshType = Literal[
    "PolyhedralSolid3D",
    "TetrahedralSolid3D",
    "HybridSolid3D",
    "RegularGrid3D",
]
GeodeGridType = Literal[
    "LightRegularGrid2D",
    "LightRegularGrid3D",
]
GeodeMeshType = (
    Literal[
        "VertexSet",
        "Graph",
        "PointSet2D",
        "PointSet3D",
        "EdgedCurve2D",
        "EdgedCurve3D",
        "RasterImage2D",
        "RasterImage3D",
    ]
    | GeodeSurfaceMeshType
    | GeodeSolidMeshType
    | GeodeGridType
)
GeodeModelType = Literal[
    "BRep",
    "Section",
    "StructuralModel",
    "CrossSection",
    "ImplicitStructuralModel",
    "ImplicitCrossSection",
]
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
GeodeSolidMeshType_values = _flatten_literal_args(GeodeSolidMeshType)
GeodeGridType_values = _flatten_literal_args(GeodeGridType)
GeodeMeshType_values = _flatten_literal_args(GeodeMeshType)
GeodeModelType_values = _flatten_literal_args(GeodeModelType)
GeodeObjectType_values = _flatten_literal_args(GeodeObjectType)


def geode_object_type(value: str) -> GeodeObjectType:
    if value not in GeodeObjectType_values:
        raise ValueError(
            f"Invalid GeodeObjectType: {value!r}. Must be one of {GeodeObjectType_values}"
        )
    return cast(GeodeObjectType, value)


def geode_mesh_type(value: str) -> GeodeMeshType:
    if value not in GeodeMeshType_values:
        raise ValueError(
            f"Invalid GeodeMeshType: {value!r}. Must be one of {GeodeMeshType_values}"
        )
    return cast(GeodeMeshType, value)


def geode_surface_mesh_type(value: str) -> GeodeSurfaceMeshType:
    if value not in GeodeSurfaceMeshType_values:
        raise ValueError(
            f"Invalid GeodeSurfaceMeshType: {value!r}. Must be one of {GeodeSurfaceMeshType_values}"
        )
    return cast(GeodeSurfaceMeshType, value)


def geode_solid_mesh_type(value: str) -> GeodeSolidMeshType:
    if value not in GeodeSolidMeshType_values:
        raise ValueError(
            f"Invalid GeodeSolidMeshType: {value!r}. Must be one of {GeodeSolidMeshType_values}"
        )
    return cast(GeodeSolidMeshType, value)


def geode_model_type(value: str) -> GeodeModelType:
    if value not in GeodeModelType_values:
        raise ValueError(
            f"Invalid GeodeModelType: {value!r}. Must be one of {GeodeModelType_values}"
        )
    return cast(GeodeModelType, value)


ViewerType = Literal["mesh", "model"]
