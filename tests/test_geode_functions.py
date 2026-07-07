# Standard library imports
import os
import uuid

# Third party imports
from opengeodeweb_microservice.database.data_types import GeodeObjectType_values

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.geode_objects import geode_objects

data_folder = os.path.join(os.path.dirname(__file__), "data")


def test_geode_objects() -> None:
    for geode_object_type in GeodeObjectType_values:
        assert geode_object_type in geode_objects


def test_input_output() -> None:
    for generic_geode_object in geode_objects.values():
        print(f"\n{generic_geode_object.geode_object_type()=}")
        for input_extension in generic_geode_object.input_extensions():
            print(f"\t{input_extension=}")
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            if generic_geode_object.is_loadable(file_absolute_path).value() == 0.0:
                continue
            geode_object = generic_geode_object.load(file_absolute_path)
            data_name = geode_object.identifier.name() or os.path.basename(
                file_absolute_path
            )
            if geode_object.is_viewable():
                viewable_file_path = geode_object.save_viewable(
                    os.path.join(os.path.abspath(f"./output"), data_name)
                )
                os.remove(viewable_file_path)
            if geode_object.is_viewable():
                light_viewable_file_path = geode_object.save_light_viewable(
                    os.path.join(os.path.abspath(f"./output"), data_name)
                )
                os.remove(light_viewable_file_path)
            geode_objects_output_extensions = (
                geode_functions.geode_object_output_extensions(geode_object)
            )
            assert type(geode_objects_output_extensions) is dict
            for (
                output_geode_object_type,
                output_geode_extensions,
            ) in geode_objects_output_extensions.items():
                print(f"\t\t{output_geode_object_type=}")
                for (
                    output_extension,
                    output_is_saveable,
                ) in output_geode_extensions.items():
                    print(f"\t\t\t{output_extension=}")
                    uu_id = str(uuid.uuid4()).replace("-", "")
                    filename = f"{uu_id}.{output_extension}"
                    if output_is_saveable:
                        saved_files = geode_objects[output_geode_object_type].save(
                            geode_object,
                            os.path.join(os.path.abspath(f"./output"), filename),
                        )
                        assert type(saved_files) is list
                        for saved_file in saved_files:
                            os.remove(saved_file)


def test_validate() -> None:
    # Test on BRep (uses is_brep_valid)
    brep_path = os.path.join(data_folder, "cube.og_brep")
    brep_object = geode_objects["BRep"].load(brep_path)
    brep_validity = brep_object.validate()
    assert type(brep_validity.nb_issues()) is int

    # Test on PointSet2D (uses is_pointset_valid2D)
    pts_path = os.path.join(data_folder, "test.og_pts2d")
    pts_object = geode_objects["PointSet2D"].load(pts_path)
    pts_validity = pts_object.validate()
    assert type(pts_validity.nb_issues()) is int

    # Test on CrossSection (uses is_section_valid)
    section_path = os.path.join(data_folder, "test.og_xsctn")
    section_object = geode_objects["CrossSection"].load(section_path)
    section_validity = section_object.validate()
    assert type(section_validity.nb_issues()) is int
