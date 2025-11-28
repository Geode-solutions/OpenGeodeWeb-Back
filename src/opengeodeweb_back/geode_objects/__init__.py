# Standard library imports
from __future__ import annotations

# Third party imports

# Local application imports
from .types import GeodeObjectType
from .geode_object import GeodeObject
from .geode_brep import GeodeBRep
from .geode_vertex_set import GeodeVertexSet
from .geode_graph import GeodeGraph
from .geode_point_set2d import GeodePointSet2D
from .geode_point_set3d import GeodePointSet3D
from .geode_edged_curve2d import GeodeEdgedCurve2D
from .geode_edged_curve3d import GeodeEdgedCurve3D
from .geode_raster_image2d import GeodeRasterImage2D
from .geode_raster_image3d import GeodeRasterImage3D
from .geode_polygonal_surface2d import GeodePolygonalSurface2D
from .geode_polygonal_surface3d import GeodePolygonalSurface3D
from .geode_triangulated_surface2d import GeodeTriangulatedSurface2D
from .geode_triangulated_surface3d import GeodeTriangulatedSurface3D
from .geode_regular_grid2d import GeodeRegularGrid2D
from .geode_polyhedral_solid3d import GeodePolyhedralSolid3D
from .geode_tetrahedral_solid3d import GeodeTetrahedralSolid3D
from .geode_hybrid_solid3d import GeodeHybridSolid3D
from .geode_regular_grid3d import GeodeRegularGrid3D
from .geode_light_regular_grid2d import GeodeLightRegularGrid2D
from .geode_light_regular_grid3d import GeodeLightRegularGrid3D
from .geode_section import GeodeSection
from .geode_structural_model import GeodeStructuralModel
from .geode_cross_section import GeodeCrossSection
from .geode_implicit_structural_model import GeodeImplicitStructuralModel
from .geode_implicit_cross_section import GeodeImplicitCrossSection

geode_objects: dict[GeodeObjectType, type[GeodeObject]] = {
    "VertexSet": GeodeVertexSet,
    "Graph": GeodeGraph,
    "PointSet2D": GeodePointSet2D,
    "PointSet3D": GeodePointSet3D,
    "EdgedCurve2D": GeodeEdgedCurve2D,
    "EdgedCurve3D": GeodeEdgedCurve3D,
    "RasterImage2D": GeodeRasterImage2D,
    "RasterImage3D": GeodeRasterImage3D,
    "PolygonalSurface2D": GeodePolygonalSurface2D,
    "PolygonalSurface3D": GeodePolygonalSurface3D,
    "TriangulatedSurface2D": GeodeTriangulatedSurface2D,
    "TriangulatedSurface3D": GeodeTriangulatedSurface3D,
    "RegularGrid2D": GeodeRegularGrid2D,
    "PolyhedralSolid3D": GeodePolyhedralSolid3D,
    "TetrahedralSolid3D": GeodeTetrahedralSolid3D,
    "HybridSolid3D": GeodeHybridSolid3D,
    "RegularGrid3D": GeodeRegularGrid3D,
    "LightRegularGrid2D": GeodeLightRegularGrid2D,
    "LightRegularGrid3D": GeodeLightRegularGrid3D,
    "BRep": GeodeBRep,
    "Section": GeodeSection,
    "StructuralModel": GeodeStructuralModel,
    "CrossSection": GeodeCrossSection,
    "ImplicitStructuralModel": GeodeImplicitStructuralModel,
    "ImplicitCrossSection": GeodeImplicitCrossSection,
}
