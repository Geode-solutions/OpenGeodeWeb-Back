import opengeode as og
import geode_viewables as viewables

from ..geode_objects import GeodeObject


class GeodeBRep(GeodeObject):
    brep: og.BRep

    def __init__(self, brep: og.BRep | None = None) -> None:
        super().__init__(geode_type="BRep", object_type="model")
        self.brep = brep if brep is not None else og.BRep()

    def builder(self) -> og.BRepBuilder:
        return og.BRepBuilder(self.brep)

    @classmethod
    def load(self, filename: str) -> GeodeBRep:
        return GeodeBRep(og.load_brep(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFilesBRep:
        return og.brep_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_brep_loadable(filename)

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.brep_object_priority(filename)
    
    def is_saveable(self, filename: str) -> bool:
        return og.is_brep_saveable(self.brep, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_brep(self.brep, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_brep(self.brep, filename_without_extension)

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_brep(self.brep, filename_without_extension)
