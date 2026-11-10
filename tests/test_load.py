# Standard library imports
from pathlib import Path

# Third party imports
import pytest

# Local application imports
from opengeodeweb_back.geode_objects import geode_objects
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep
from opengeodeweb_back.geode_objects.geode_triangulated_surface3d import (
    GeodeTriangulatedSurface3D,
)

data_folder = Path(__file__).parent / "data"


def test_load_returns_list_for_native_file() -> None:
    objects = GeodeBRep.load(str(data_folder / "test.og_brep"))
    assert isinstance(objects, list)
    assert len(objects) == 1
    assert isinstance(objects[0], GeodeBRep)


def test_load_one_returns_object_for_native_file() -> None:
    geode_object = GeodeBRep.load_one(str(data_folder / "test.og_brep"))
    assert isinstance(geode_object, GeodeBRep)


def test_load_returns_every_object_of_the_file() -> None:
    objects = geode_objects["TriangulatedSurface3D"].load(str(data_folder / "two_surfaces.ts"))
    assert len(objects) == 2
    assert all(isinstance(obj, GeodeTriangulatedSurface3D) for obj in objects)


def test_load_one_raises_when_file_holds_several_objects() -> None:
    filename = str(data_folder / "two_surfaces.ts")
    with pytest.raises(ValueError, match=r"two_surfaces\.ts.*2"):
        GeodeTriangulatedSurface3D.load_one(filename)
