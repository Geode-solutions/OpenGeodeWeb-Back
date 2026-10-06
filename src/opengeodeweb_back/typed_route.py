from __future__ import annotations

# Standard library imports
import functools
from typing import TYPE_CHECKING, Any

import fastjsonschema  # type: ignore[import-untyped]

# Third party imports
import flask

# Local application imports
from opengeodeweb_back import utils_functions

if TYPE_CHECKING:
    from collections.abc import Callable

    from opengeodeweb_microservice.schemas import ParamsT, ResponseT, Route

TYPED_ROUTE_MARKER = "__typed_route__"


def _drop_none(value: Any) -> Any:
    # Optional response fields are generated as `field: X | None = None`:
    # omit them instead of sending null
    if isinstance(value, dict):
        return {key: _drop_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value


def _register(
    blueprint: flask.Blueprint,
    route: Route[Any, Any],
    handler: Callable[..., Any],
    view: Callable[[], flask.Response],
) -> Callable[[], flask.Response]:
    view = functools.wraps(handler)(view)
    setattr(view, TYPED_ROUTE_MARKER, True)
    blueprint.route(route.schema["route"], methods=route.schema["methods"])(view)
    return view


def parse_params(route: Route[ParamsT, Any]) -> ParamsT:
    """Validate the JSON body of the current request against its route schema.

    Return the typed params built from it.
    """
    json_data = utils_functions.validate_request(flask.request, route.schema)
    return route.params.from_dict(json_data)


def typed_route(
    blueprint: flask.Blueprint, route: Route[ParamsT, ResponseT]
) -> Callable[[Callable[[ParamsT], ResponseT]], Callable[[], flask.Response]]:
    """Register a JSON route whose handler takes and returns typed objects.

    The handler takes its typed params and returns its typed success response.
    Errors must be raised (flask.abort or any exception), they are turned into an
    ErrorResponse by the app error handlers.
    """
    validate_response = fastjsonschema.compile(route.schema["response"])

    def decorator(
        handler: Callable[[ParamsT], ResponseT],
    ) -> Callable[[], flask.Response]:
        def view() -> flask.Response:
            result = handler(parse_params(route))
            if not isinstance(result, route.response):
                raise TypeError(
                    f"{handler.__name__} returned {type(result).__name__}, "
                    f"expected {route.response.__name__}"
                )
            payload = _drop_none(result.to_dict())
            if flask.current_app.debug or flask.current_app.testing:
                validate_response(payload)
            return flask.make_response(payload, 200)

        return _register(blueprint, route, handler, view)

    return decorator


def raw_route(
    blueprint: flask.Blueprint, route: Route[Any, Any]
) -> Callable[[Callable[[], flask.Response]], Callable[[], flask.Response]]:
    """Register a route that cannot go through typed_route.

    Used for a non JSON request body (file upload) or a file response.
    The handler builds its own flask.Response: call parse_params for a JSON body,
    and build a JSON body from the route's generated response class.
    """

    def decorator(
        handler: Callable[[], flask.Response],
    ) -> Callable[[], flask.Response]:
        def view() -> flask.Response:
            return handler()

        return _register(blueprint, route, handler, view)

    return decorator
