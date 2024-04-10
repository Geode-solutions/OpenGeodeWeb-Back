class Result:
    def __init__(self, children: list, route: str, sentence: str = None, value=None):
        self.children = children
        self.is_leaf = len(children) == 0
        self.route = route
        self.value = value
        self.sentence = sentence
        self.list_invalidities = None


def json_return(Result_list: list):
    json_result = []
    for result in Result_list:
        json_temp = {
            "value": result.value,
            "children": (
                result.children if result.is_leaf else json_return(result.children)
            ),
            "is_leaf": result.is_leaf,
            "route": result.route,
            "sentence": result.sentence if result.sentence != None else result.route,
        }
        json_result.append(json_temp)
    return json_result
