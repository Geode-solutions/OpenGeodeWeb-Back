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

# Type casting helpers for OpenGeode C++ bindings
# OpenGeode functions return 'Any' due to missing type stubs,


def cast_str(value: object) -> str:
    """
    Args:
        value: Return value from OpenGeode binding (typed as Any)
    Returns:
        The value cast to str for type checking purposes
    """
    return cast(str, value)


def cast_list_str(value: object) -> list[str]:
    """
    Args:
        value: Return value from OpenGeode binding (typed as Any)
    Returns:
        The value cast to list[str] for type checking purposes
    """
    return cast(list[str], value)


def cast_int(value: object) -> int:
    """
    Args:
        value: Return value from OpenGeode binding (typed as Any)
    Returns:
        The value cast to int for type checking purposes
    """
    return cast(int, value)


def cast_bool(value: object) -> bool:
    """
    Args:
        value: Return value from OpenGeode binding (typed as Any)
    Returns:
        The value cast to bool for type checking purposes
    """
    return cast(bool, value)
