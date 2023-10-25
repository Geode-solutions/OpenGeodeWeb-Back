import os
from src.opengeodeweb_back import geode_functions, geode_objects


def test_geode_object_value():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        geode_object_value = geode_functions.geode_object_value(geode_object)
        assert type(geode_object_value) is dict


def test_input_factory():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        geode_object_input = geode_functions.input_factory(geode_object)
        assert type(geode_object_input.list_creators()) is list


def test_input_extensions():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        geode_object_input_extensions = geode_functions.geode_object_input_extensions(
            geode_object
        )

        assert type(geode_object_input_extensions) is list
        for extension in geode_object_input_extensions:
            assert type(extension) is str


def test_output_factory():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        geode_object_output = geode_functions.output_factory(geode_object)
        geode_object_output_list = geode_object_output.list_creators()
        assert type(geode_object_output_list) is list
        for output in geode_object_output_list:
            assert type(output) is str


def test_missing_files():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
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
    for geode_object, value in geode_objects.geode_objects_dict().items():
        is_model = geode_functions.is_model(geode_object)
        assert type(is_model) is bool


def test_is_3D():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        is_3D = geode_functions.is_3D(geode_object)
        assert type(is_3D) is bool


def test_is_viewable():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        is_viewable = geode_functions.is_viewable(geode_object)
        assert type(is_viewable) is bool


def test_geode_object_input_extensions():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
        assert type(input_extensions) is list
        for input_extension in input_extensions:
            assert type(input_extension) is str


def test_geode_object_output_extensions():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        output_extensions = geode_functions.geode_object_output_extensions(geode_object)
        assert type(output_extensions) is list
        for output_extension in output_extensions:
            assert type(output_extension) is str


def test_list_input_extensions():
    keys_array = ["crs", "inspector", None]
    for geode_object, value in geode_objects.geode_objects_dict().items():
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
        for geode_object, value in geode_objects.geode_objects_dict().items():
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


def test_geode_objects_output_extensions():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        geode_objects_and_output_extensions_list = (
            geode_functions.geode_objects_output_extensions(geode_object)
        )
        print(f"{geode_objects_and_output_extensions_list=}")
        assert type(geode_objects_and_output_extensions_list) is list
        for (
            geode_object_and_output_extensions
        ) in geode_objects_and_output_extensions_list:
            assert type(geode_object_and_output_extensions) is dict


def test_versions():
    list_packages = [
        "OpenGeode-core",
        "OpenGeode-IO",
        "OpenGeode-Geosciences",
        "OpenGeode-GeosciencesIO",
    ]
    versions = geode_functions.versions(list_packages)
    assert type(versions) is list
    for version in versions:
        assert type(version) is dict


def test_extension_from_filename():
    extension = geode_functions.extension_from_filename("test.toto")
    assert type(extension) is str
    assert extension.count(".") == 0
