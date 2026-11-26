from opengeodeweb_microservice.schema_types import DataId, GeodeId
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class ModelPhysicalProperties(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: DataId


@dataclass
class Component(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_id: GeodeId
    max_values: List[Optional[float]]
    min_values: List[Optional[float]]
    no_data: bool


@dataclass
class PhysicalProperty(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribute_id: str
    attribute_name: str
    component_type: str
    components: List[Component]
    element_type: str
    name: str
    nb_items: int


@dataclass
class ModelPhysicalPropertiesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    physical_properties: List[PhysicalProperty]


model_physical_properties_route = Route(
    schema=load_schema(Path(__file__)),
    params=ModelPhysicalProperties,
    response=ModelPhysicalPropertiesResponse,
)

__all__ = ["ModelPhysicalProperties", "ModelPhysicalPropertiesResponse", "model_physical_properties_route"]
