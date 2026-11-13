# Standard library imports
from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
from opengeodeweb_microservice.database.data_types import GeodeObjectType_values

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.geode_objects import geode_objects
from opengeodeweb_back.routes.schemas.allowed_objects import AllowedObject

if TYPE_CHECKING:
    from opengeodeweb_back.geode_objects.geode_object import GeodeObject

data_folder = Path(__file__).parent / "data"
output_folder = Path("./output").resolve()


def test_geode_objects() -> None:
    for geode_object_type in GeodeObjectType_values:
        assert geode_object_type in geode_objects


def test_input_output() -> None:
    for generic_geode_object in geode_objects.values():
        for input_extension in generic_geode_object.input_extensions():
            file_absolute_path = str(data_folder / f"test.{input_extension}")
            if generic_geode_object.is_loadable(file_absolute_path).value() == 0.0:
                continue
            for geode_object in generic_geode_object.load(file_absolute_path):
                check_save_and_output_extensions(geode_object, file_absolute_path)


def check_save_and_output_extensions(geode_object: GeodeObject, file_absolute_path: str) -> None:
    data_name = geode_object.identifier.name() or Path(file_absolute_path).name
    if geode_object.is_viewable():
        viewable_file_path = geode_object.save_viewable(str(output_folder / data_name))
        Path(viewable_file_path).unlink()
    if geode_object.is_viewable():
        light_viewable_file_path = geode_object.save_light_viewable(str(output_folder / data_name))
        Path(light_viewable_file_path).unlink()
    geode_objects_output_extensions = geode_functions.geode_object_output_extensions(geode_object)
    assert type(geode_objects_output_extensions) is dict
    for (
        output_geode_object_type,
        output_geode_extensions,
    ) in geode_objects_output_extensions.items():
        for (
            output_extension,
            output_is_saveable,
        ) in output_geode_extensions.items():
            uu_id = str(uuid.uuid4()).replace("-", "")
            filename = f"{uu_id}.{output_extension}"
            if output_is_saveable:
                saved_files = geode_objects[output_geode_object_type].save(
                    geode_object,
                    str(output_folder / filename),
                )
                assert type(saved_files) is list
                for saved_file in saved_files:
                    Path(saved_file).unlink()


def test_validate() -> None:
    # Test on BRep (uses is_brep_valid)
    brep_path = str(data_folder / "cube.og_brep")
    brep_object = geode_objects["BRep"].load_one(brep_path)
    brep_validity = brep_object.validate()
    assert type(brep_validity.nb_issues()) is int

    # Test on PointSet2D (uses is_pointset_valid2D)
    pts_path = str(data_folder / "test.og_pts2d")
    pts_object = geode_objects["PointSet2D"].load_one(pts_path)
    pts_validity = pts_object.validate()
    assert type(pts_validity.nb_issues()) is int

    # Test on CrossSection (uses is_section_valid)
    section_path = str(data_folder / "test.og_xsctn")
    section_object = geode_objects["CrossSection"].load_one(section_path)
    section_validity = section_object.validate()
    assert type(section_validity.nb_issues()) is int


def _allowed(
    *entries: tuple[str, str, float, int],
) -> dict[str, AllowedObject]:
    return {
        object_type: AllowedObject(
            is_loadable=is_loadable,
            object_priority=priority,
            loadable_family=family,
        )
        for object_type, family, is_loadable, priority in entries
    }


def test_loadable_family() -> None:
    expected = {
        "VertexSet": "VertexSet",
        "PointSet2D": "PointSet",
        "PointSet3D": "PointSet",
        "Graph": "Graph",
        "EdgedCurve2D": "Graph",
        "EdgedCurve3D": "Graph",
        "PolygonalSurface2D": "SurfaceMesh",
        "PolygonalSurface3D": "SurfaceMesh",
        "TriangulatedSurface2D": "SurfaceMesh",
        "TriangulatedSurface3D": "SurfaceMesh",
        "PolyhedralSolid3D": "SolidMesh",
        "TetrahedralSolid3D": "SolidMesh",
        "HybridSolid3D": "SolidMesh",
        "RegularGrid2D": "Grid",
        "RegularGrid3D": "Grid",
        "LightRegularGrid2D": "Grid",
        "LightRegularGrid3D": "Grid",
        "RasterImage2D": "RasterImage",
        "RasterImage3D": "RasterImage",
        "BRep": "BRep",
        "StructuralModel": "BRep",
        "ImplicitStructuralModel": "BRep",
        "Section": "Section",
        "CrossSection": "Section",
        "ImplicitCrossSection": "Section",
        "HorizonStack3D": "HorizonsStack",
    }
    assert set(expected) == set(geode_objects)
    for object_type, geode_object in geode_objects.items():
        assert geode_object.loadable_family() == expected[object_type]


def test_objects_to_load_mixed_vtu() -> None:
    allowed = _allowed(
        ("PolygonalSurface3D", "SurfaceMesh", 0.5, 0),
        ("TriangulatedSurface3D", "SurfaceMesh", 0.5, 1),
        ("PolyhedralSolid3D", "SolidMesh", 0.5, 0),
        ("TetrahedralSolid3D", "SolidMesh", 0.5, 2),
        ("HybridSolid3D", "SolidMesh", 0.5, 1),
    )
    assert geode_functions.objects_to_load(allowed) == [
        "TriangulatedSurface3D",
        "TetrahedralSolid3D",
    ]


def test_objects_to_load_json_curve_and_grid() -> None:
    allowed = _allowed(
        ("EdgedCurve3D", "Graph", 1.0, 1),
        ("RegularGrid3D", "Grid", 0.7, 1),
        ("LightRegularGrid3D", "Grid", 0.7, 3),
    )
    assert geode_functions.objects_to_load(allowed) == ["EdgedCurve3D", "LightRegularGrid3D"]


def test_objects_to_load_loadability_beats_priority() -> None:
    allowed = _allowed(
        ("RegularGrid3D", "Grid", 1.0, 0),
        ("LightRegularGrid3D", "Grid", 0.5, 9),
    )
    assert geode_functions.objects_to_load(allowed) == ["RegularGrid3D"]


def test_objects_to_load_dimensions_are_alternatives() -> None:
    allowed = _allowed(
        ("TriangulatedSurface2D", "SurfaceMesh", 1.0, 1),
        ("TriangulatedSurface3D", "SurfaceMesh", 1.0, 2),
    )
    assert geode_functions.objects_to_load(allowed) == ["TriangulatedSurface3D"]


def test_objects_to_load_single_content() -> None:
    allowed = _allowed(("BRep", "BRep", 1.0, 0))
    assert geode_functions.objects_to_load(allowed) == ["BRep"]


def test_objects_to_load_tie_gives_nothing() -> None:
    allowed = _allowed(
        ("EdgedCurve3D", "Graph", 1.0, 1),
        ("TriangulatedSurface2D", "SurfaceMesh", 1.0, 1),
        ("TriangulatedSurface3D", "SurfaceMesh", 1.0, 1),
    )
    assert geode_functions.objects_to_load(allowed) == []


def test_objects_to_load_nothing_loadable() -> None:
    allowed = _allowed(
        ("TriangulatedSurface3D", "SurfaceMesh", 0.0, 1),
        ("TetrahedralSolid3D", "SolidMesh", 0.0, 2),
    )
    assert geode_functions.objects_to_load(allowed) == []
    assert geode_functions.objects_to_load({}) == []


def test_objects_to_load_ignores_unloadable_family() -> None:
    allowed = _allowed(
        ("TriangulatedSurface3D", "SurfaceMesh", 1.0, 1),
        ("TetrahedralSolid3D", "SolidMesh", 0.0, 2),
    )
    assert geode_functions.objects_to_load(allowed) == ["TriangulatedSurface3D"]
