import os
from src.opengeodeweb_back import geode_functions, geode_objects


def test_get_geode_object_input():
    for geode_object, value in geode_objects.objects_list().items():
        geode_object_input = geode_functions.get_geode_object_input(geode_object)
        assert type(geode_object_input) is list


def test_get_geode_object_output():
    for geode_object, value in geode_objects.objects_list().items():
        geode_object_input = geode_functions.get_geode_object_output(geode_object)
        assert type(geode_object_input) is list


def test_is_model():
    for geode_object, value in geode_objects.objects_list().items():
        is_model = geode_functions.is_model(geode_object)
        print(geode_object)
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


def test_get_geode_object_input_extensions():
    for geode_object, value in geode_objects.objects_list().items():
        output_extensions = geode_functions.get_geode_object_output_extensions(
            geode_object
        )
        assert type(output_extensions) is list
        for extension in output_extensions:
            assert type(extension) is str


def test_load():
    for geode_object, value in geode_objects.objects_list().items():
        input_extensions = geode_functions.get_geode_object_input_extensions(
            geode_object
        )

        output_extensions = geode_functions.get_geode_object_output_extensions(
            geode_object
        )
        for input_extension in input_extensions:
            data = geode_functions.load(
                geode_object,
                os.path.join(
                    os.path.abspath("./tests/data"), f"test.{input_extension}"
                ),
            )

            for output_extension in output_extensions:
                file_path = os.path.abspath(f"./output/test.{output_extension}")

                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"{file_path} deleted.")
                geode_functions.save(
                    geode_object,
                    data,
                    os.path.abspath("./output"),
                    f"test.{output_extension}",
                )
