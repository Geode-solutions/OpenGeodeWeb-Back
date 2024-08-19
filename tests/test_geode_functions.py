import os
import uuid
from src.opengeodeweb_back import geode_functions, geode_objects


data_folder = os.path.join(os.path.dirname(__file__), "data")


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
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            missing_files = geode_functions.missing_files(
                geode_object, file_absolute_path
            )
            has_missing_files = missing_files.has_missing_files()
            assert type(has_missing_files) is bool
            mandatory_files = missing_files.mandatory_files
            assert type(mandatory_files) is list
            additional_files = missing_files.additional_files
            assert type(additional_files) is list


def test_is_loadable():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
        for input_extension in input_extensions:
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            is_loadable = geode_functions.is_loadable(geode_object, file_absolute_path)
            assert type(is_loadable) is bool


def test_load():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        print(f"\n{geode_object=}")
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
        for input_extension in input_extensions:
            print(f"\t{input_extension=}")
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            missing_files = geode_functions.missing_files(
                geode_object, file_absolute_path
            )
            has_missing_files = missing_files.has_missing_files()
            if has_missing_files:
                mandatory_files = missing_files.mandatory_files
                print(f"\t\t{mandatory_files=}")
                additional_files = missing_files.additional_files
                print(f"\t\t{additional_files=}")
            if geode_functions.is_loadable(geode_object, file_absolute_path):
                data = geode_functions.load(geode_object, file_absolute_path)
                if "save_viewable" in value:
                    uu_id = str(uuid.uuid4()).replace("-", "")
                    viewable_file_path = geode_functions.save_viewable(
                        geode_object,
                        data,
                        os.path.abspath(f"./output"),
                        uu_id,
                    )
                    os.remove(viewable_file_path)
                geode_objects_and_output_extensions = (
                    geode_functions.geode_objects_output_extensions(geode_object, data)
                )
                assert type(geode_objects_and_output_extensions) is dict
                for (
                    output_geode_object,
                    output_geode_object_value,
                ) in geode_objects_and_output_extensions.items():
                    print(f"\t\t{output_geode_object=}")
                    for (
                        output_extension,
                        output_extension_value,
                    ) in output_geode_object_value.items():
                        print(f"\t\t\t{output_extension=}")
                        uu_id = str(uuid.uuid4()).replace("-", "")
                        filename = f"{uu_id}.{output_extension}"
                        if geode_functions.is_saveable(
                            output_geode_object, data, filename
                        ):
                            saved_files = geode_functions.save(
                                output_geode_object,
                                data,
                                os.path.abspath(f"./output"),
                                filename,
                            )
                            assert type(saved_files) is list
                            for saved_file in saved_files:
                                os.remove(saved_file)


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
        print(f"\n{geode_object=}")
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
        for input_extension in input_extensions:
            print(f"\t{input_extension=}")
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            missing_files = geode_functions.missing_files(
                geode_object, file_absolute_path
            )
            has_missing_files = missing_files.has_missing_files()
            if has_missing_files:
                mandatory_files = missing_files.mandatory_files
                print(f"\t\t{mandatory_files=}")
                additional_files = missing_files.additional_files
                print(f"\t\t{additional_files=}")
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            if geode_functions.is_loadable(geode_object, file_absolute_path):
                data = geode_functions.load(geode_object, file_absolute_path)
                geode_objets_and_output_extensions = (
                    geode_functions.geode_objects_output_extensions(geode_object, data)
                )
                assert type(geode_objets_and_output_extensions) is dict
                for (
                    output_geode_object,
                    output_geode_object_value,
                ) in geode_objets_and_output_extensions.items():
                    for (
                        output_extension,
                        output_extension_value,
                    ) in output_geode_object_value.items():
                        assert type(output_extension) is str
                        assert type(output_extension_value["is_saveable"]) is bool


def test_get_inspector_children():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        if "inspector" in value:
            print(f"\n{geode_object=}", flush=True)
            input_extensions = geode_functions.geode_object_input_extensions(
                geode_object
            )
            for input_extension in input_extensions:
                print(f"\t{input_extension=}", flush=True)
                file_absolute_path = os.path.join(
                    data_folder, f"test.{input_extension}"
                )
                missing_files = geode_functions.missing_files(
                    geode_object, file_absolute_path
                )
                has_missing_files = missing_files.has_missing_files()
                if has_missing_files:
                    mandatory_files = missing_files.mandatory_files
                    print(f"\t\t{mandatory_files=}", flush=True)
                    additional_files = missing_files.additional_files
                    print(f"\t\t{additional_files=}", flush=True)
                file_absolute_path = os.path.join(
                    data_folder, f"test.{input_extension}"
                )
                if geode_functions.is_loadable(geode_object, file_absolute_path):
                    data = geode_functions.load(geode_object, file_absolute_path)
                    class_inspector = geode_functions.inspect(geode_object, data)
                    assert "InspectionResult" in class_inspector.__class__.__name__
                    inspection_result = geode_functions.get_inspector_children(
                        class_inspector
                    )

                    print(f"\t\t{inspection_result=}", flush=True)
                    assert type(inspection_result) is dict


def test_filter_geode_objects():
    filters_list = ["", "crs", "inspector", None]

    for filter in filters_list:
        geode_objects_filtered_list = geode_functions.filter_geode_objects(filter)
        assert type(geode_objects_filtered_list) is list
        for geode_object in geode_objects_filtered_list:
            assert type(geode_object) is str


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
                file_absolute_path = os.path.join(
                    data_folder, f"test.{input_extension}"
                )
                return_dict = geode_functions.list_geode_objects(
                    file_absolute_path, key
                )
                assert type(return_dict) is dict

                if key != None:
                    assert len(return_dict.keys()) > 0
                    for invalid_geode_object in invalid_geode_objects:
                        assert invalid_geode_object not in return_dict.keys()
                else:
                    assert len(return_dict.keys()) >= 1
                    for input_geode_object, input_extension_dict in return_dict.items():
                        assert type(input_extension_dict) is dict
                        for (
                            input_extension,
                            input_extension_value,
                        ) in input_extension_dict.items():
                            assert type(input_extension_value) is bool


def test_geode_objects_output_extensions():
    for geode_object, value in geode_objects.geode_objects_dict().items():
        input_extensions = geode_functions.geode_object_input_extensions(geode_object)
        for input_extension in input_extensions:
            file_absolute_path = os.path.join(data_folder, f"test.{input_extension}")
            if geode_functions.is_loadable(geode_object, file_absolute_path):
                data = geode_functions.load(geode_object, file_absolute_path)
                geode_objects_and_output_extensions = (
                    geode_functions.geode_objects_output_extensions(geode_object, data)
                )
                assert type(geode_objects_and_output_extensions) is dict
                for (
                    output_geode_object,
                    output_geode_object_value,
                ) in geode_objects_and_output_extensions.items():
                    for (
                        output_extension,
                        output_extension_value,
                    ) in output_geode_object_value.items():
                        assert type(output_extension_value["is_saveable"]) is bool
