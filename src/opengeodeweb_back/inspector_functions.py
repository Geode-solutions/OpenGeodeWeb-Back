class Result:
    def __init__(self, title: str = None, children: list = [], value: bool = False):
        self.title = title
        self.value = value
        self.children = children
        self.list_invalidities = None


def json_return(Result_list: list):
    json_result = []
    for result in Result_list:
        json_temp = {
            "title": result.title,
            "value": result.value,
            "children": (
                result.children if result.is_leaf else json_return(result.children)
            ),
        }
        json_result.append(json_temp)
    return json_result
