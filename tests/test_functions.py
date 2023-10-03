import os
from src.opengeodeweb_back import geode_functions, geode_objects


def test_get_input_factory():
    for geode_object, value in geode_objects.objects_list().items():
        geode_object_input = geode_functions.get_input_factory(geode_object)
        assert type(geode_object_input) is list


def test_get_output_factory():
    for geode_object, value in geode_objects.objects_list().items():
        geode_object_input = geode_functions.get_output_factory(geode_object)
        assert type(geode_object_input) is list


def test_is_model():
    for geode_object, value in geode_objects.objects_list().items():
        is_model = geode_functions.is_model(geode_object)
        assert type(is_model) is bool


def test_is_3D():
    for geode_object, value in geode_objects.objects_list().items():
        is_3D = geode_functions.is_3D(geode_object)
        assert type(is_3D) is bool


def test_is_viewable():
    for geode_object, value in geode_objects.objects_list().items():
        is_viewable = geode_functions.is_viewable(geode_object)
        assert type(is_viewable) is bool


def test_get_geode_object_input_extensions():
    for geode_object, value in geode_objects.objects_list().items():
        input_extensions = geode_functions.get_geode_object_input_extensions(
            geode_object
        )
        assert type(input_extensions) is list
        for extension in input_extensions:
            assert type(extension) is str


def test_get_geode_object_output_extensions():
    for geode_object, value in geode_objects.objects_list().items():
        output_extensions = geode_functions.get_geode_object_output_extensions(
            geode_object
        )
        assert type(output_extensions) is list
        for extension in output_extensions:
            assert type(extension) is str


def test_list_input_extensions():
    keys_array = [["crs"], ["inspector"]]
    for geode_object, value in geode_objects.objects_list().items():
        for keys in keys_array:
            input_extensions = geode_functions.list_input_extensions(keys)
            assert type(input_extensions) is list


def test_list_geode_objects():
    keys_array = [["crs"], ["inspector"]]
    input_extensions = geode_functions.list_input_extensions()
    for geode_object, value in geode_objects.objects_list().items():
        for input_extension in input_extensions:
            for keys in keys_array:
                print(f"{input_extension=}")
                print(f"{keys=}")
                geode_objects_list = geode_functions.list_geode_objects(
                    input_extension, keys
                )
                assert type(geode_objects_list) is list


def test_get_versions():
    list_packages = [
        "OpenGeode-core",
        "OpenGeode-IO",
        "OpenGeode-Geosciences",
        "OpenGeode-GeosciencesIO",
    ]
    versions = geode_functions.get_versions(list_packages)
    assert type(versions) is list
    for version in versions:
        assert type(version) is dict


def test_get_extension_from_filename():
    extension = geode_functions.get_extension_from_filename("test.toto")
    print(extension)
    assert type(extension) is str
    print()
    assert extension.count(".") == 0
