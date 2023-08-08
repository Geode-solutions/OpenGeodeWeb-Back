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
            "children": result.children
            if result.is_leaf
            else json_return(result.children),
            "is_leaf": result.is_leaf,
            "route": result.route,
            "sentence": result.sentence if result.sentence != None else result.route,
        }
        json_result.append(json_temp)
    return json_result


def AdjacencyTests(object: str):
    AdjacencyTests = [
        Result(
            [],
            f"nb_{object}_with_wrong_adjacency",
            f"Number of {object} with invalid adjacencies",
        )
    ]
    Wrapper_AdjacencyTests = Result(AdjacencyTests, "Adjacency")
    return Wrapper_AdjacencyTests


def ColocationTests():
    ColocationTests = [Result([], "nb_colocated_points", "Number of colocated points")]
    Wrapper_ColocationTests = Result(ColocationTests, "Colocation")
    return Wrapper_ColocationTests


def DegenerationTests():
    DegenerationTests = [
        Result([], "nb_degenerated_edges", "Number of degenerated edges")
    ]
    Wrapper_DegenerationTests = Result(DegenerationTests, "Degeneration")
    return Wrapper_DegenerationTests


def ManifoldTests(objects: list):
    ManifoldTests = []
    for object in objects:
        ManifoldTests.append(
            Result([], f"nb_non_manifold_{object}", f"Number of non manifold {object}")
        )
    Wrapper_ManifoldTests = Result(ManifoldTests, "Manifold")
    return Wrapper_ManifoldTests


def IntersectionTests():
    IntersectionTests = [
        Result([], "intersecting_elements", "Number of intersecting elements")
    ]
    Wrapper_IntersectionTests = Result(IntersectionTests, "Intersection")
    return Wrapper_IntersectionTests


def TopologyTests(object: str):
    unique_vertices_colocation = [
        Result(
            [],
            "unique_vertices_linked_to_different_points",
            "Number of unique vertices linked to different points in space",
        ),
        Result(
            [],
            "colocated_unique_vertices_groups",
            "Number of unique vertices colocated in space",
        ),
    ]

    components_are_linked_to_a_unique_vertex = [
        Result(
            [],
            "nb_corners_not_linked_to_a_unique_vertex",
            "Number of corners not linked to a unique vertex",
        ),
        Result(
            [],
            "nb_lines_meshed_but_not_linked_to_a_unique_vertex",
            "Number of lines not linked to a unique vertex",
        ),
        Result(
            [],
            "nb_surfaces_meshed_but_not_linked_to_a_unique_vertex",
            "Number of surfaces not linked to a unique vertex",
        ),
    ]

    invalid_components_topology_unique_vertices = [
        Result(
            [],
            "unique_vertices_not_linked_to_a_component_vertex",
            "Number of unique vertices not linked to a component mesh vertex",
        ),
        Result(
            [],
            "multiple_corners_unique_vertices",
            "Unique vertices linked to multiple corners",
        ),
        Result(
            [],
            "multiple_internals_corner_vertices",
            "Unique vertices linked to a corner with multiple internal relations",
        ),
        Result(
            [],
            "not_internal_nor_boundary_corner_vertices",
            "Unique vertices linked to a corner which is neither internal nor boundary",
        ),
        Result(
            [],
            "line_corners_without_boundary_status",
            "Unique vertices linked to a line and a corner not boundary of the line",
        ),
        Result(
            [],
            "part_of_not_boundary_nor_internal_line_unique_vertices",
            "Unique vertices part of a line without boundary or internal relations",
        ),
        Result(
            [],
            "part_of_line_with_invalid_internal_topology_unique_vertices",
            "Unique vertices part of a line with invalid internal topology relations",
        ),
        Result(
            [],
            "part_of_invalid_unique_line_unique_vertices",
            "Unique vertices part of a single line with invalid topology",
        ),
        Result(
            [],
            "part_of_lines_but_not_corner_unique_vertices",
            "Unique vertices part of multiple lines with invalid topology",
        ),
        Result(
            [],
            "part_of_line_and_not_on_surface_border_unique_vertices",
            "Unique vertices part of a line and a surface but not on the border of the surface mesh",
        ),
    ]

    if object == "brep":
        brep_components_are_linked_to_a_unique_vertex = (
            components_are_linked_to_a_unique_vertex
        )
        brep_components_are_linked_to_a_unique_vertex.append(
            Result(
                [],
                "nb_blocks_meshed_but_not_linked_to_a_unique_vertex",
                "Number of blocks not linked to a unique vertex",
            )
        )

        brep_invalid_components_topology_unique_vertices = (
            invalid_components_topology_unique_vertices
        )
        brep_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_not_boundary_nor_internal_surface_unique_vertices",
                "Unique vertices part of a surface which has no boundary or internal relations",
            )
        )
        brep_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_surface_with_invalid_internal_topology_unique_vertices",
                "Unique vertices part of a surface with invalid internal topology",
            )
        )
        brep_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_invalid_unique_surface_unique_vertices",
                "Unique vertices part of a unique surface with invalid topology",
            )
        )
        brep_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_invalid_multiple_surfaces_unique_vertices",
                "Unique vertices part of multiple surfaces with invalid topology",
            )
        )
        brep_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_invalid_blocks_unique_vertices",
                "Unique vertices part of blocks with invalid topology",
            )
        )

        TopologyTests = [
            Result(
                brep_components_are_linked_to_a_unique_vertex,
                "Meshed components are linked to a unique vertex",
            ),
            Result(
                brep_invalid_components_topology_unique_vertices,
                "Unique vertices linked to components with invalid topology",
            ),
            Result(
                unique_vertices_colocation, "Unique vertices with colocation issues"
            ),
        ]
    elif object == "section":
        section_invalid_components_topology_unique_vertices = (
            invalid_components_topology_unique_vertices
        )
        section_invalid_components_topology_unique_vertices.append(
            Result(
                [],
                "part_of_invalid_surfaces_unique_vertices",
                "Unique vertices part of surfaces with invalid topology",
            )
        )

        TopologyTests = [
            Result(
                components_are_linked_to_a_unique_vertex,
                "Meshed components are linked to a unique vertex",
            ),
            Result(
                section_invalid_components_topology_unique_vertices,
                "Unique vertices linked to components with invalid topology",
            ),
            Result(
                unique_vertices_colocation, "Unique vertices with colocation issues"
            ),
        ]
    Wrapper_TopologyTests = Result(TopologyTests, "Topology")
    return Wrapper_TopologyTests


def ComponentMeshesTests(object: str):
    component_meshes_adjacency = [
        Result(
            [],
            "surfaces_nb_edges_with_wrong_adjacencies",
            "Model component meshes edge adjacencies",
        )
    ]
    component_meshes_colocation = [
        Result(
            [],
            "components_nb_colocated_points",
            "Model component meshes point colocation",
        )
    ]
    component_meshes_degeneration = [
        Result(
            [],
            "components_nb_degenerated_elements",
            "Model component meshes element degeneration",
        )
    ]
    component_meshes_manifold = [
        Result(
            [],
            "component_meshes_nb_non_manifold_vertices",
            "Model component meshes vertex manifold",
        ),
        Result(
            [],
            "component_meshes_nb_non_manifold_edges",
            "Model component meshes edge manifold",
        ),
    ]
    component_meshes_intersection = [
        Result(
            [],
            "intersecting_surfaces_elements",
            "Pairs of component meshes triangles intersecting",
        )
    ]

    if object == "brep":
        brep_component_meshes_adjacency = component_meshes_adjacency
        brep_component_meshes_adjacency.append(
            Result(
                [],
                "blocks_nb_facets_with_wrong_adjacencies",
                "Model component meshes facet adjacencies",
            )
        )

        brep_component_meshes_manifold = component_meshes_manifold
        brep_component_meshes_manifold.append(
            Result(
                [],
                "component_meshes_nb_non_manifold_facets",
                "Model component meshes facet manifold",
            )
        )

        ComponentMeshesTests = [
            Result(brep_component_meshes_adjacency, "Adjacency"),
            Result(component_meshes_colocation, "Colocation"),
            Result(component_meshes_degeneration, "Degeneration"),
            Result(brep_component_meshes_manifold, "Manifold"),
            Result(component_meshes_intersection, "Intersections"),
        ]

    elif object == "section":
        ComponentMeshesTests = [
            Result(component_meshes_adjacency, "Adjacency"),
            Result(component_meshes_colocation, "Colocation"),
            Result(component_meshes_degeneration, "Degeneration"),
            Result(component_meshes_manifold, "Manifold"),
        ]

    Wrapper_ComponentMeshesTests = Result(ComponentMeshesTests, "Component Meshes")
    return Wrapper_ComponentMeshesTests


def inspectors():
    BRep_Tests = [Result([TopologyTests("brep"), ComponentMeshesTests("brep")], "BRep")]
    CrossSection_Tests = [
        Result(
            [TopologyTests("section"), ComponentMeshesTests("section")], "CrossSection"
        )
    ]
    EdgedCurve2D_Tests = [
        Result([ColocationTests(), DegenerationTests()], "EdgedCurve2D")
    ]
    EdgedCurve3D_Tests = [
        Result([ColocationTests(), DegenerationTests()], "EdgedCurve3D")
    ]
    Graph_Tests = [Result([], "Graph", value=True)]
    HybridSolid3D_Tests = [
        Result(
            [
                AdjacencyTests("facets"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "facets", "vertices"]),
            ],
            "HybridSolid3D",
        )
    ]
    PointSet2D_Tests = [Result([ColocationTests()], "PointSet2D", value=True)]
    PointSet3D_Tests = [Result([ColocationTests()], "PointSet3D", value=True)]
    PolygonalSurface2D_Tests = [
        Result(
            [
                AdjacencyTests("edges"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "vertices"]),
            ],
            "PolygonalSurface2D",
        )
    ]
    PolygonalSurface3D_Tests = [
        Result(
            [
                AdjacencyTests("edges"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "vertices"]),
            ],
            "PolygonalSurface3D",
        )
    ]
    PolyhedralSolid3D_Tests = [
        Result(
            [
                AdjacencyTests("facets"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "facets", "vertices"]),
            ],
            "PolyhedralSolid3D",
        )
    ]
    RegularGrid2D_Tests = [Result([], "RegularGrid2D", value=True)]
    RegularGrid3D_Tests = [Result([], "RegularGrid3D", value=True)]
    Section_Tests = [
        Result([TopologyTests("section"), ComponentMeshesTests("section")], "Section")
    ]
    StructuralModel_Tests = [
        Result([TopologyTests("brep"), ComponentMeshesTests("brep")], "StructuralModel")
    ]
    TetrahedralSolid3D_Tests = [
        Result(
            [
                AdjacencyTests("facets"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "facets", "vertices"]),
            ],
            "TetrahedralSolid3D",
        )
    ]
    TriangulatedSurface2D_Tests = [
        Result(
            [
                AdjacencyTests("edges"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "vertices"]),
                IntersectionTests(),
            ],
            "TriangulatedSurface2D",
        )
    ]
    TriangulatedSurface3D_Tests = [
        Result(
            [
                AdjacencyTests("edges"),
                ColocationTests(),
                DegenerationTests(),
                ManifoldTests(["edges", "vertices"]),
                IntersectionTests(),
            ],
            "TriangulatedSurface3D",
        )
    ]
    VertexSet_Tests = [Result([], "VertexSet", value=True)]

    return {
        "BRep": {"tests_names": BRep_Tests},
        "CrossSection": {
            "tests_names": CrossSection_Tests,
        },
        "EdgedCurve2D": {
            "tests_names": EdgedCurve2D_Tests,
        },
        "EdgedCurve3D": {
            "tests_names": EdgedCurve3D_Tests,
        },
        "Graph": {"tests_names": Graph_Tests},
        "HybridSolid3D": {
            "tests_names": HybridSolid3D_Tests,
        },
        "PointSet2D": {
            "tests_names": PointSet2D_Tests,
        },
        "PointSet3D": {
            "tests_names": PointSet3D_Tests,
        },
        "PolygonalSurface2D": {
            "tests_names": PolygonalSurface2D_Tests,
        },
        "PolygonalSurface3D": {
            "tests_names": PolygonalSurface3D_Tests,
        },
        "PolyhedralSolid3D": {
            "tests_names": PolyhedralSolid3D_Tests,
        },
        "RegularGrid2D": {"tests_names": RegularGrid2D_Tests},
        "RegularGrid3D": {"tests_names": RegularGrid3D_Tests},
        "Section": {
            "tests_names": Section_Tests,
        },
        "StructuralModel": {
            "tests_names": StructuralModel_Tests,
        },
        "TetrahedralSolid3D": {
            "tests_names": TetrahedralSolid3D_Tests,
        },
        "TriangulatedSurface2D": {
            "tests_names": TriangulatedSurface2D_Tests,
        },
        "TriangulatedSurface3D": {
            "tests_names": TriangulatedSurface3D_Tests,
        },
        "VertexSet": {"tests_names": VertexSet_Tests},
    }
