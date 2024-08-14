from src.opengeodeweb_back import utils_functions


def test_versions():
    list_packages = [
        "OpenGeode-core",
        "OpenGeode-IO",
        "OpenGeode-Geosciences",
        "OpenGeode-GeosciencesIO",
    ]
    versions = utils_functions.versions(list_packages)
    assert type(versions) is list
    for version in versions:
        assert type(version) is dict


def test_extension_from_filename():
    extension = utils_functions.extension_from_filename("test.toto")
    assert type(extension) is str
    assert extension.count(".") == 0


def test_handle_exception(client):
    route = "/error"
    response = client.post(route)
    assert response.status_code == 500
    data = response.get_json()
    assert type(data) is dict
    assert type(data["description"]) is str
    assert type(data["name"]) is str
    assert type(data["code"]) is int