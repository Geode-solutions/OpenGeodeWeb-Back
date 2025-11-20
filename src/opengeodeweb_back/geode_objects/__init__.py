# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, Any, get_args, cast

# Third party imports
import opengeode as og
import opengeode_io as og_io
import opengeode_inspector as og_inspector
import opengeode_geosciences as og_gs
import opengeode_geosciencesio as og_gs_io
import geode_viewables as viewables

# Local application imports
from .types import GeodeObjectType, GeodeMeshType, GeodeModelType
from .geode_object import GeodeObject
from .geode_model import GeodeModel
from .geode_mesh import GeodeMesh
from .geode_brep import GeodeBRep


geode_meshes: dict[GeodeMeshType, type[GeodeMesh]] = {}
geode_models: dict[GeodeModelType, type[GeodeModel]] = {"BRep": GeodeBRep}

GeodeObjectsDict = dict[GeodeObjectType, type[GeodeObject]]
geode_objects: GeodeObjectsDict = {}
geode_objects.update(cast(GeodeObjectsDict, geode_meshes))
geode_objects.update(cast(GeodeObjectsDict, geode_models))


# def geode_objects_dict():
#     return {
#         "BRep": {
#             "crs": {
#                 "assign": og_gs.assign_brep_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_brep_coordinate_reference_system,
#                 "create": og.create_brep_coordinate_system,
#             },
#         },
#         "CrossSection": {
#             "crs": {
#                 "assign": og_gs.assign_section_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_section_coordinate_reference_system,
#                 "create": og.create_section_coordinate_system,
#             },
#         },
#         "EdgedCurve2D": {
#             "crs": {
#                 "assign": og_gs.assign_edged_curve_geographic_coordinate_system_info2D,
#                 "convert": og_gs.convert_edged_curve_coordinate_reference_system2D,
#                 "create": og.create_edged_curve_coordinate_system2D,
#             },
#         },
#         "EdgedCurve3D": {
#             "crs": {
#                 "assign": og_gs.assign_edged_curve_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_edged_curve_coordinate_reference_system3D,
#                 "create": og.create_edged_curve_coordinate_system3D,
#             },
#         },
#         "HybridSolid3D": {
#             "class": og.HybridSolid3D,
#             "input_factory": og.HybridSolidInputFactory3D,
#             "output_factory": og.HybridSolidOutputFactory3D,
#             "additional_files": og.hybrid_solid_additional_files3D,
#             "is_loadable": og.is_hybrid_solid_loadable3D,
#             "object_priority": og.hybrid_solid_object_priority3D,
#             "load": og.load_hybrid_solid3D,
#             "is_saveable": og.is_hybrid_solid_saveable3D,
#             "save": og.save_hybrid_solid3D,
#             "builder": og.HybridSolidBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_solid_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_solid_mesh_coordinate_reference_system3D,
#                 "create": og.create_solid_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polyhedrons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_hybrid_solid3D,
#             "save_light_viewable": g_v.save_light_viewable_hybrid_solid3D,
#             "inspector": og_inspector.inspect_solid3D,
#         },
#         "ImplicitCrossSection": {
#             "crs": {
#                 "assign": og_gs.assign_section_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_section_coordinate_reference_system,
#                 "create": og.create_section_coordinate_system,
#             },
#         },
#         "ImplicitStructuralModel": {
#             "crs": {
#                 "assign": og_gs.assign_brep_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_brep_coordinate_reference_system,
#                 "create": og.create_brep_coordinate_system,
#             },
#         },
#         "LightRegularGrid2D": {
#             "class": og.LightRegularGrid2D,
#             "input_factory": og.LightRegularGridInputFactory2D,
#             "output_factory": og.LightRegularGridOutputFactory2D,
#             "additional_files": og.light_regular_grid_additional_files2D,
#             "is_loadable": og.is_light_regular_grid_loadable2D,
#             "object_priority": og.light_regular_grid_object_priority2D,
#             "load": og.load_light_regular_grid2D,
#             "is_saveable": og.is_light_regular_grid_saveable2D,
#             "save": og.save_light_regular_grid2D,
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": False,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_light_regular_grid2D,
#             "save_light_viewable": g_v.save_light_viewable_light_regular_grid2D,
#         },
#         "LightRegularGrid3D": {
#             "class": og.LightRegularGrid3D,
#             "input_factory": og.LightRegularGridInputFactory3D,
#             "output_factory": og.LightRegularGridOutputFactory3D,
#             "additional_files": og.light_regular_grid_additional_files3D,
#             "is_loadable": og.is_light_regular_grid_loadable3D,
#             "object_priority": og.light_regular_grid_object_priority3D,
#             "load": og.load_light_regular_grid3D,
#             "is_saveable": og.is_light_regular_grid_saveable3D,
#             "save": og.save_light_regular_grid3D,
#             "object_type": mesh,
#             "elements": [points, polyhedrons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_light_regular_grid3D,
#             "save_light_viewable": g_v.save_light_viewable_light_regular_grid3D,
#         },
#         "PointSet2D": {
#             "crs": {
#                 "assign": og_gs.assign_point_set_geographic_coordinate_system_info2D,
#                 "convert": og_gs.convert_point_set_coordinate_reference_system2D,
#                 "create": og.create_point_set_coordinate_system2D,
#             },
#         },
#         "PointSet3D": {
#             "crs": {
#                 "assign": og_gs.assign_point_set_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_point_set_coordinate_reference_system3D,
#                 "create": og.create_point_set_coordinate_system3D,
#             },
#         },
#         "PolygonalSurface2D": {
#             "class": og.PolygonalSurface2D,
#             "input_factory": og.PolygonalSurfaceInputFactory2D,
#             "output_factory": og.PolygonalSurfaceOutputFactory2D,
#             "additional_files": og.polygonal_surface_additional_files2D,
#             "is_loadable": og.is_polygonal_surface_loadable2D,
#             "object_priority": og.polygonal_surface_object_priority2D,
#             "load": og.load_polygonal_surface2D,
#             "is_saveable": og.is_polygonal_surface_saveable2D,
#             "save": og.save_polygonal_surface2D,
#             "builder": og.PolygonalSurfaceBuilder2D.create,
#             "crs": {
#                 "assign": og_gs.assign_surface_mesh_geographic_coordinate_system_info2D,
#                 "convert": og_gs.convert_surface_mesh_coordinate_reference_system2D,
#                 "create": og.create_surface_mesh_coordinate_system2D,
#             },
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": False,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_polygonal_surface2D,
#             "save_light_viewable": g_v.save_light_viewable_polygonal_surface2D,
#             "inspector": og_inspector.inspect_surface2D,
#         },
#         "PolygonalSurface3D": {
#             "class": og.PolygonalSurface3D,
#             "input_factory": og.PolygonalSurfaceInputFactory3D,
#             "output_factory": og.PolygonalSurfaceOutputFactory3D,
#             "additional_files": og.polygonal_surface_additional_files3D,
#             "is_loadable": og.is_polygonal_surface_loadable3D,
#             "object_priority": og.polygonal_surface_object_priority3D,
#             "load": og.load_polygonal_surface3D,
#             "is_saveable": og.is_polygonal_surface_saveable3D,
#             "save": og.save_polygonal_surface3D,
#             "builder": og.PolygonalSurfaceBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_surface_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_surface_mesh_coordinate_reference_system3D,
#                 "create": og.create_surface_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_polygonal_surface3D,
#             "save_light_viewable": g_v.save_light_viewable_polygonal_surface3D,
#             "inspector": og_inspector.inspect_surface3D,
#         },
#         "PolyhedralSolid3D": {
#             "class": og.PolyhedralSolid3D,
#             "input_factory": og.PolyhedralSolidInputFactory3D,
#             "output_factory": og.PolyhedralSolidOutputFactory3D,
#             "additional_files": og.polyhedral_solid_additional_files3D,
#             "is_loadable": og.is_polyhedral_solid_loadable3D,
#             "object_priority": og.polyhedral_solid_object_priority3D,
#             "load": og.load_polyhedral_solid3D,
#             "is_saveable": og.is_polyhedral_solid_saveable3D,
#             "save": og.save_polyhedral_solid3D,
#             "builder": og.PolyhedralSolidBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_solid_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_solid_mesh_coordinate_reference_system3D,
#                 "create": og.create_solid_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polyhedrons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_polyhedral_solid3D,
#             "save_light_viewable": g_v.save_light_viewable_polyhedral_solid3D,
#             "inspector": og_inspector.inspect_solid3D,
#         },
#         "RegularGrid2D": {
#             "class": og.RegularGrid2D,
#             "input_factory": og.RegularGridInputFactory2D,
#             "output_factory": og.RegularGridOutputFactory2D,
#             "additional_files": og.regular_grid_additional_files2D,
#             "is_loadable": og.is_regular_grid_loadable2D,
#             "object_priority": og.regular_grid_object_priority2D,
#             "load": og.load_regular_grid2D,
#             "is_saveable": og.is_regular_grid_saveable2D,
#             "save": og.save_regular_grid2D,
#             "builder": og.RegularGridBuilder2D.create,
#             "crs": {
#                 "assign": og_gs.assign_surface_mesh_geographic_coordinate_system_info2D,
#                 "convert": og_gs.convert_surface_mesh_coordinate_reference_system2D,
#                 "create": og.create_surface_mesh_coordinate_system2D,
#             },
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": False,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_regular_grid2D,
#             "save_light_viewable": g_v.save_light_viewable_regular_grid2D,
#         },
#         "RegularGrid3D": {
#             "class": og.RegularGrid3D,
#             "input_factory": og.RegularGridInputFactory3D,
#             "output_factory": og.RegularGridOutputFactory3D,
#             "additional_files": og.regular_grid_additional_files3D,
#             "is_loadable": og.is_regular_grid_loadable3D,
#             "object_priority": og.regular_grid_object_priority3D,
#             "load": og.load_regular_grid3D,
#             "is_saveable": og.is_regular_grid_saveable3D,
#             "save": og.save_regular_grid3D,
#             "builder": og.RegularGridBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_solid_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_solid_mesh_coordinate_reference_system3D,
#                 "create": og.create_surface_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polyhedrons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_regular_grid3D,
#             "save_light_viewable": g_v.save_light_viewable_regular_grid3D,
#         },
#         "Section": {
#             "crs": {
#                 "assign": og_gs.assign_section_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_section_coordinate_reference_system,
#                 "create": og.create_section_coordinate_system,
#             },
#         },
#         "StructuralModel": {
#             "crs": {
#                 "assign": og_gs.assign_brep_geographic_coordinate_system_info,
#                 "convert": og_gs.convert_brep_coordinate_reference_system,
#                 "create": og.create_brep_coordinate_system,
#             },
#         },
#         "TetrahedralSolid3D": {
#             "class": og.TetrahedralSolid3D,
#             "input_factory": og.TetrahedralSolidInputFactory3D,
#             "output_factory": og.TetrahedralSolidOutputFactory3D,
#             "additional_files": og.tetrahedral_solid_additional_files3D,
#             "is_loadable": og.is_tetrahedral_solid_loadable3D,
#             "object_priority": og.tetrahedral_solid_object_priority3D,
#             "load": og.load_tetrahedral_solid3D,
#             "is_saveable": og.is_tetrahedral_solid_saveable3D,
#             "save": og.save_tetrahedral_solid3D,
#             "builder": og.TetrahedralSolidBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_solid_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_solid_mesh_coordinate_reference_system3D,
#                 "create": og.create_solid_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polyhedrons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_tetrahedral_solid3D,
#             "save_light_viewable": g_v.save_light_viewable_tetrahedral_solid3D,
#             "inspector": og_inspector.inspect_solid3D,
#         },
#         "TriangulatedSurface2D": {
#             "class": og.TriangulatedSurface2D,
#             "input_factory": og.TriangulatedSurfaceInputFactory2D,
#             "output_factory": og.TriangulatedSurfaceOutputFactory2D,
#             "additional_files": og.triangulated_surface_additional_files2D,
#             "is_loadable": og.is_triangulated_surface_loadable2D,
#             "object_priority": og.triangulated_surface_object_priority2D,
#             "load": og.load_triangulated_surface2D,
#             "is_saveable": og.is_triangulated_surface_saveable2D,
#             "save": og.save_triangulated_surface2D,
#             "builder": og.TriangulatedSurfaceBuilder2D.create,
#             "crs": {
#                 "assign": og_gs.assign_surface_mesh_geographic_coordinate_system_info2D,
#                 "convert": og_gs.convert_surface_mesh_coordinate_reference_system2D,
#                 "create": og.create_surface_mesh_coordinate_system2D,
#             },
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": False,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_triangulated_surface2D,
#             "save_light_viewable": g_v.save_light_viewable_triangulated_surface2D,
#             "inspector": og_inspector.inspect_surface2D,
#         },
#         "TriangulatedSurface3D": {
#             "class": og.TriangulatedSurface3D,
#             "input_factory": og.TriangulatedSurfaceInputFactory3D,
#             "output_factory": og.TriangulatedSurfaceOutputFactory3D,
#             "additional_files": og.triangulated_surface_additional_files3D,
#             "is_loadable": og.is_triangulated_surface_loadable3D,
#             "object_priority": og.triangulated_surface_object_priority3D,
#             "load": og.load_triangulated_surface3D,
#             "is_saveable": og.is_triangulated_surface_saveable3D,
#             "save": og.save_triangulated_surface3D,
#             "builder": og.TriangulatedSurfaceBuilder3D.create,
#             "crs": {
#                 "assign": og_gs.assign_surface_mesh_geographic_coordinate_system_info3D,
#                 "convert": og_gs.convert_surface_mesh_coordinate_reference_system3D,
#                 "create": og.create_surface_mesh_coordinate_system3D,
#             },
#             "object_type": mesh,
#             "elements": [points, polygons],
#             "is_3D": True,
#             "is_viewable": True,
#             "save_viewable": g_v.save_viewable_triangulated_surface3D,
#             "save_light_viewable": g_v.save_light_viewable_triangulated_surface3D,
#             "inspector": og_inspector.inspect_surface3D,
#         },
#     }
