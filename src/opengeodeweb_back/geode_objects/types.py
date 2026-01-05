# Standard library imports
from typing import Literal, get_args, cast

# Third party imports

# Local application imports

GeodePointMeshType = Literal[
    "PointSet2D",
    "PointSet3D",
]
GeodeEdgeMeshType = Literal[
    "EdgedCurve2D",
    "EdgedCurve3D",
]
GeodePolygonMeshType = Literal[
    "RasterImage2D",
    "PolygonalSurface2D",
    "PolygonalSurface3D",
    "TriangulatedSurface2D",
    "TriangulatedSurface3D",
    "RegularGrid2D",
    "LightRegularGrid2D",
]
GeodePolyhedronMeshType = Literal[
    "RasterImage3D",
    "PolyhedralSolid3D",
    "TetrahedralSolid3D",
    "HybridSolid3D",
    "RegularGrid3D",
    "LightRegularGrid3D",
]
GeodeMeshType = (
    Literal[
        "VertexSet",
        "Graph",
    ]
    | GeodePointMeshType
    | GeodeEdgeMeshType
    | GeodePolygonMeshType
    | GeodePolyhedronMeshType
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


GeodeObjectType_values = _flatten_literal_args(GeodeObjectType)


def geode_object_type(value: str) -> GeodeObjectType:
    if value not in GeodeObjectType_values:
        raise ValueError(
            f"Invalid GeodeObjectType: {value!r}. Must be one of {GeodeObjectType_values}"
        )
    return cast(GeodeObjectType, value)


ViewerType = Literal["mesh", "model"]
