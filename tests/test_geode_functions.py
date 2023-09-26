from .src import geode_functions


def test_is_model():
    response = geode_functions.is_model("BRep")
    assert response == True
