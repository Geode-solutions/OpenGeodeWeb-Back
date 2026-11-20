from opengeodeweb_back.schema_types import Filename
from opengeodeweb_microservice.schema_types import DataId
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class ApplyTimeSeries(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: Filename
    id: DataId


@dataclass
class ApplyTimeSeriesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    pass


apply_time_series_route = Route(
    schema=load_schema(Path(__file__)),
    params=ApplyTimeSeries,
    response=ApplyTimeSeriesResponse,
)

__all__ = ["ApplyTimeSeries", "ApplyTimeSeriesResponse", "apply_time_series_route"]
