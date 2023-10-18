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


def test_missing_files():
    for geode_object, value in geode_objects.objects_list().items():
        input_extensions = geode_functions.get_geode_object_input_extensions(
            geode_object
        )
        for input_extension in input_extensions:
            file_absolute_path = os.path.abspath(f"tests/data/test.{input_extension}")
            missing_files = geode_functions.missing_files(
                geode_object, file_absolute_path
            )
            has_missing_files = missing_files.has_missing_files()
            assert type(has_missing_files) is bool
            mandatory_files = missing_files.mandatory_files
            assert type(mandatory_files) is list
            additional_files = missing_files.additional_files
            assert type(additional_files) is list


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
    keys_array = ["crs", "inspector", None]
    for geode_object, value in geode_objects.objects_list().items():
        for keys in keys_array:
            input_extensions = geode_functions.list_input_extensions(keys)
            assert type(input_extensions) is list


def test_list_geode_objects():
    test_list = [
        {
            "key": "crs",
            "invalid_geode_objects": [
                "Graph",
                "RasterImage2D",
                "RasterImage3D",
                "VertexSet",
            ],
        },
        {
            "key": "inspector",
            "invalid_geode_objects": [
                "Graph",
                "RasterImage2D",
                "RasterImage3D",
                "RasterImage2D",
                "RasterImage3D",
                "VertexSet",
            ],
        },
        {
            "key": None,
            "invalid_geode_objects": [],
        },
    ]
    for test in test_list:
        key = test["key"]
        invalid_geode_objects = test["invalid_geode_objects"]

        input_extensions = geode_functions.list_input_extensions(key)
        for geode_object, value in geode_objects.objects_list().items():
            for input_extension in input_extensions:
                geode_objects_list = geode_functions.list_geode_objects(
                    input_extension, key
                )
                assert type(geode_objects_list) is list

                if key != None:
                    assert len(geode_objects_list) > 0
                    for invalid_geode_object in invalid_geode_objects:
                        assert invalid_geode_object not in geode_objects_list
                else:
                    assert len(geode_objects_list) >= 1


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
    assert type(extension) is str
    assert extension.count(".") == 0
