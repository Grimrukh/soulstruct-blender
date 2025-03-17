from __future__ import annotations

__all__ = [
    "BlenderMCG",
    "BlenderMCGNode",
    "BlenderMCGEdge",
]

import typing as tp

import bpy
from io_soulstruct.exceptions import *
from io_soulstruct.navmesh.nvm.types import BlenderNVM
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.navmesh import MCG, MCGNode
from soulstruct.base.maps.navmesh import MCGEdge
from soulstruct.utilities.text import natural_keys
from .properties import *


class BlenderMCG(BaseBlenderSoulstructObject[MCG, MCGProps]):

    TYPE = SoulstructType.MCG
    BL_OBJ_TYPE = ObjectType.EMPTY
    SOULSTRUCT_CLASS = MCG

    __slots__ = [
        "node_parent",
        "edge_parent",
    ]

    node_parent: bpy.types.Object
    edge_parent: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        super().__init__(obj)

        # MCG parent should have two Empty children: a 'Nodes' sub-parent and an 'Edges' sub-parent.
        # We look for these by name, ignoring Blender dupe suffix.
        if len(obj.children) != 2:
            raise SoulstructTypeError(
                f"MCG object '{obj.name}' must have exactly two children: '{{name}} Nodes' and '{{name}} Edges'."
            )
        for child in obj.children:
            name = remove_dupe_suffix(child.name)
            if name.lower().endswith("nodes"):
                self.node_parent = child
            elif name.lower().endswith("edges"):
                self.edge_parent = child
        if not hasattr(self, "node_parent"):
            raise SoulstructTypeError(f"Could not find Nodes parent object as a child of MCG object '{obj.name}'.")
        if not hasattr(self, "edge_parent"):
            raise SoulstructTypeError(f"Could not find Edges parent object as a child of MCG object '{obj.name}'.")

    @property
    def unknowns(self):
        return [self.type_properties.unknown_0, self.type_properties.unknown_1, self.type_properties.unknown_2]

    @unknowns.setter
    def unknowns(self, value: list[int]):
        if len(value) != 3:
            raise ValueError("`BlenderMCG.unknowns` must be a list of three integers.")
        self.type_properties.unknown_0 = value[0]
        self.type_properties.unknown_1 = value[1]
        self.type_properties.unknown_2 = value[2]

    def get_nodes(self) -> list[BlenderMCGNode]:
        return [BlenderMCGNode(node) for node in sorted(self.node_parent.children, key=lambda c: natural_keys(c.name))]

    def get_edges(self) -> list[BlenderMCGEdge]:
        return [BlenderMCGEdge(edge) for edge in sorted(self.edge_parent.children, key=lambda c: natural_keys(c.name))]

    def get_node_index(self, node_obj: bpy.types.Object) -> int:
        """Get index of given node (raw object) in this MCG's nodes. Will raise a ValueError if absent."""
        return [bl_node.obj for bl_node in self.get_nodes()].index(node_obj)

    # NOTE: No edge index method ever needed.

    @classmethod
    def new(
        cls,
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Creates Nodes and Edges child-parents."""
        match cls.BL_OBJ_TYPE:
            case ObjectType.EMPTY:
                if data is not None:
                    raise SoulstructTypeError(f"Cannot create an EMPTY object with data.")
                obj = bpy.data.objects.new(name, None)
            case ObjectType.MESH:
                # Permitted to be initialized as Empty.
                if data is not None and not isinstance(data, bpy.types.Mesh):
                    raise SoulstructTypeError(f"Data for MESH object must be a Mesh, not {type(data).__name__}.")
                obj = bpy.data.objects.new(name, data)
            case _:
                raise SoulstructTypeError(f"Unsupported Soulstruct BL_OBJ_TYPE '{cls.BL_OBJ_TYPE}'.")
        obj.soulstruct_type = cls.TYPE
        (collection or bpy.context.scene.collection).objects.link(obj)

        node_parent = bpy.data.objects.new(f"{name} Nodes", None)
        collection.objects.link(node_parent)
        node_parent.parent = obj

        edge_parent = bpy.data.objects.new(f"{name} Edges", None)
        collection.objects.link(edge_parent)
        edge_parent.parent = obj

        return cls(obj)

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MCG,
        name: str,
        collection: bpy.types.Collection = None,
        navmesh_part_names: list[str] = None,
    ) -> BlenderMCG:
        if not navmesh_part_names:
            raise ValueError("`navmesh_part_names` must be provided.")

        mcg = soulstruct_obj
        if mcg.edges and mcg.edges[0].navmesh_index is None:
            raise NavGraphImportError("Imported MCG must not have its MSB navmeshes dereferenced.")
        collection = collection or context.scene.collection
        operator.info(f"Importing MCG '{name}'.")

        highest_navmesh_index = max(edge.navmesh_index for edge in mcg.edges)
        if highest_navmesh_index >= len(navmesh_part_names):
            raise NavGraphImportError(
                f"Highest MCG edge navmesh part index ({highest_navmesh_index}) exceeds number of navmesh part "
                f"names provided ({len(navmesh_part_names)}."
            )
        # NOTE: navmesh count can exceed highest edge index, as some navmeshes may have no edges in them.

        operator.to_object_mode()
        operator.deselect_all()

        bl_mcg = cls.new(name, data=None, collection=collection)  # type: BlenderMCG

        # Actual MCG binary file stores navmesh node triangle indices for every edge, which is extremely redundant, as
        # every node touches exactly two navmeshes and its connected edges in each of those two navmeshes always use
        # consistent triangles (in a valid MCG file). So we store them on the NODES in Blender and write them back to
        # edges on export. (This is strictly a Blender thing - the Soulstruct `MCGEdge` classes still hold their node
        # triangle indices - but does use a Soulstruct `MCG` method to verify the triangles used on a node-by-node basis
        # rather than by edge.)
        # NOTE: If a node uses inconsistent triangles in different edges in the same navmesh, the first indices will be
        # used and a warning logged. If a node seemingly has edges in more than two navmeshes, import will fail, as the
        # MCG file is not valid (for DS1 at least).
        node_triangle_indices = mcg.get_navmesh_triangles_by_node(allow_clashes=True)

        node_objs = []

        for i, (node, triangle_indices) in enumerate(zip(mcg.nodes, node_triangle_indices)):
            node: MCGNode
            bl_node = BlenderMCGNode.new_from_soulstruct_obj(
                operator,
                context,
                node,
                name=f"{name} Node {i}",
                collection=None,  # default
                navmesh_part_names=navmesh_part_names,
                triangle_indices=triangle_indices,
            )
            bl_node.parent = bl_mcg.node_parent
            # Connected node/edge indices not kept; inferred from edges.
            node_objs.append(bl_node)

        for i, edge in enumerate(mcg.edges):
            node_a_index = mcg.nodes.index(edge.node_a)
            node_b_index = mcg.nodes.index(edge.node_b)
            if node_a_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid node A index: {node_a_index}")
            if node_b_index >= len(mcg.nodes):
                raise ValueError(f"Edge {i} has invalid node B index: {node_b_index}")
            try:
                navmesh_name = navmesh_part_names[edge.navmesh_index]
            except IndexError:
                raise ValueError(f"Edge {i} has invalid navmesh index {edge.navmesh_index}.")

            # NOTE: Suffix is for inspection convenience only. The true navmesh part name/index is stored in properties.
            # Also note that we don't include the edge index in the name (unlike nodes) because it is unused elsewhere.
            # The start and end node indices are enough to uniquely identify an edge.
            edge_name = f"{name} Edge ({node_a_index} -> {node_b_index}) <{navmesh_name}>"

            bl_edge = BlenderMCGEdge.new_from_soulstruct_obj(
                operator,
                context,
                edge,
                name=edge_name,
                collection=None,  # default
                navmesh_name=navmesh_name,
                node_a=node_objs[node_a_index].obj,
                node_b=node_objs[node_b_index].obj,
            )
            bl_edge.parent = bl_mcg.edge_parent

        # Automatically set node and edge parents for drawing.
        context.scene.mcg_draw_settings.mcg_parent = bl_mcg.obj

        # Invoke 'scene.refresh_mcg_names' operator.
        operator.set_active_obj(bl_mcg.obj)
        getattr(bpy.ops.scene, "refresh_mcg_names")()

        return bl_mcg

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        navmesh_part_indices: dict[str, int] = None,
    ) -> MCG:
        """Create MCG from Blender nodes and edges.

        `bl_nodes` and `bl_edges` are assumed to be correctly ordered for MCG indexing. This should generally match the
        order they appear in Blender.

        Requires a dictionary mapping navmesh part names to indices (from MSB) for export, and a `map_id` for edges.
        """
        if not navmesh_part_indices:
            raise ValueError("`navmesh_part_indices` must be provided to export `MCG`.")

        map_stem = self.game_name
        match = MAP_STEM_RE.match(map_stem)
        if not match:
            raise NavGraphExportError(f"Could not extract map stem from MCG name '{self.name}'.")
        map_id = (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
        )

        # Iterate over all nodes to build a dictionary of Nodes that ignores 'dead end' navmesh suffixes.
        node_dict = {}  # type: dict[str, int]
        node_prefix = f"{map_stem} Node "  # map-specific node prefix (multiple MCGs can exist with the same node names)
        bl_nodes = self.get_nodes()  # natural keys sorting

        for i, bl_node in enumerate(bl_nodes):
            if bl_node.name.startswith(node_prefix):
                node_name = _get_node_name_stem(bl_node.obj)
                node_dict[node_name] = i
            else:
                raise NavGraphExportError(f"Node '{bl_node.name}' does not start with '{node_prefix}'.")

        # List of all created nodes in the order they will be written in the file.
        nodes = []  # type: list[MCGNode]

        # Maps navmesh names to their nodes, so we can detect dead ends (single-node navmeshes).
        navmesh_nodes = {navmesh_name: [] for navmesh_name in navmesh_part_indices.keys()}

        # List of dicts that map EXACTLY two navmesh names to triangles for edges to write (as Soulstruct stores the
        # triangle indices on the nodes rather than the edges).
        node_navmesh_triangles = []  # type: list[dict[str, list[int]]]
        for bl_node in bl_nodes:
            node_navmesh_info = {}
            node = bl_node.to_soulstruct_obj(
                operator,
                context,
                navmesh_nodes=navmesh_nodes,
                node_navmesh_info=node_navmesh_info,  # 'out' parameter
            )
            nodes.append(node)
            node_navmesh_triangles.append(node_navmesh_info)

        # Check for dead ends.
        for navmesh_name, nodes_with_navmesh in navmesh_nodes.items():
            if len(nodes_with_navmesh) == 1:
                # NOTE: We don't check if/what triangles were set here, as the user may want to shuffle around navmeshes
                # and change which ones are dead ends without removing the indices.
                node = nodes_with_navmesh[0]
                if node.dead_end_navmesh_index != -1:
                    # Already set from another navmesh!
                    raise NavGraphExportError(
                        f"Node '{node.name}' is apparently connected to multiple dead-end navmeshes, which is not "
                        f"allowed. You must fix your navmesh graph in Blender first."
                    )
                node.dead_end_navmesh_index = navmesh_part_indices[navmesh_name]

        operator.info(f"Exported {len(nodes)} MCG nodes.")

        edges = []
        for i, bl_edge in enumerate(self.get_edges()):  # natural keys sorting
            edge = bl_edge.to_soulstruct_obj(
                operator,
                context,
                navmesh_part_indices=navmesh_part_indices,
                node_navmesh_triangles=node_navmesh_triangles,
                node_indices=node_dict,
                nodes=nodes,
                map_id=map_id,
            )
            edges.append(edge)

        operator.info(f"Exported {len(edges)} MCG edges.")

        mcg = MCG(nodes=nodes, edges=edges, unknowns=(0, 0, 0))

        return mcg


class BlenderMCGNode(BaseBlenderSoulstructObject[MCGNode, MCGNodeProps]):

    TYPE = SoulstructType.MCG_NODE
    BL_OBJ_TYPE = ObjectType.EMPTY
    SOULSTRUCT_CLASS = MCGNode

    __slots__ = []

    @property
    def unknown_offset(self) -> int:
        return self.type_properties.unknown_offset

    @unknown_offset.setter
    def unknown_offset(self, value: int):
        self.type_properties.unknown_offset = value

    @property
    def navmesh_a(self) -> bpy.types.MeshObject | None:
        return self.type_properties.navmesh_a

    @navmesh_a.setter
    def navmesh_a(self, value: bpy.types.MeshObject | None):
        self.type_properties.navmesh_a = value

    @property
    def navmesh_a_triangles(self) -> list[int]:
        return [t.index for t in self.type_properties.navmesh_a_triangles]

    @navmesh_a_triangles.setter
    def navmesh_a_triangles(self, indices: list[int]):
        self.type_properties.navmesh_a_triangles.clear()
        for index in indices:
            self.type_properties.navmesh_a_triangles.add().index = index

    @property
    def navmesh_b(self) -> bpy.types.MeshObject | None:
        return self.type_properties.navmesh_b

    @navmesh_b.setter
    def navmesh_b(self, value: bpy.types.MeshObject | None):
        self.type_properties.navmesh_b = value

    @property
    def navmesh_b_triangles(self) -> list[int]:
        return [t.index for t in self.type_properties.navmesh_b_triangles]

    @navmesh_b_triangles.setter
    def navmesh_b_triangles(self, indices: list[int]):
        self.type_properties.navmesh_b_triangles.clear()
        for index in indices:
            self.type_properties.navmesh_b_triangles.add().index = index

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MCGNode,
        name: str,
        collection: bpy.types.Collection = None,
        navmesh_part_names: list[str] = None,
        triangle_indices: dict[str, None | tuple[int, list[int]]] = None,
    ) -> BlenderMCGNode:
        if not navmesh_part_names:
            raise ValueError("`navmesh_part_names` must be provided.")
        if not triangle_indices:
            raise ValueError("`triangle_indices` must be provided.")

        node = soulstruct_obj

        bl_node = cls.new(name, data=None, collection=collection)  # type: BlenderMCGNode
        bl_node.obj.empty_display_type = "SPHERE"
        bl_node.obj.location = GAME_TO_BL_VECTOR(soulstruct_obj.translate)

        # Since MCG nodes in Blender reference the two navmeshes they connect, dead-end navmeshes can be
        # auto-detected from single-node navmeshes and don't need to be stored in Blender. However, we do check the
        # dead-end index here.
        if node.dead_end_navmesh_index >= len(navmesh_part_names):
            operator.warning(
                f"'{bl_node.name}' has invalid dead-end navmesh index: {node.dead_end_navmesh_index}. Ignoring."
            )

        # Stored here, but unlikely to ever matter, and cannot be reconstructed. Still exported if available.
        bl_node.unknown_offset = node.unknown_offset

        # Triangle indices are stored on the node, not the edge, for convenience, as they should be the same.
        for nav in ["a", "b"]:
            if triangle_indices[nav]:
                navmesh_index, navmesh_triangles = triangle_indices[nav]
                try:
                    navmesh_name = navmesh_part_names[navmesh_index]
                except IndexError:
                    raise NavGraphImportError(
                        f"'{bl_node.name}' has invalid navmesh {nav.upper()} index: {navmesh_index}"
                    )
                # TODO: Only search in appropriate MSB collection.
                navmesh_part = find_obj(navmesh_name, soulstruct_type=SoulstructType.MSB_PART)
                if navmesh_part is None:
                    # Not acceptable. Parts must be imported before MCG.
                    raise NavGraphMissingNavmeshError(
                        f"'{bl_node.name}' navmesh {nav.upper()} references missing MSB Navmesh object: {navmesh_name}"
                    )

                setattr(bl_node, f"navmesh_{nav}", navmesh_part)
                setattr(bl_node, f"navmesh_{nav}_triangles", navmesh_triangles)

        return bl_node

    def get_navmesh_triangles(self, navmesh: bpy.types.Object) -> list[int] | None:
        if self.navmesh_a == navmesh:
            return self.navmesh_a_triangles
        elif self.navmesh_b == navmesh:
            return self.navmesh_b_triangles
        return None  # node does not connect to this navmesh

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        navmesh_nodes: dict[str, list[MCGNode]] = None,
        node_navmesh_info: dict[str, list[int]] = None,
    ) -> MCGNode:
        node = MCGNode(
            translate=BL_TO_GAME_VECTOR3(self.location),
            unknown_offset=self.type_properties.unknown_offset,
            dead_end_navmesh_index=-1,  # may be set below
        )

        if node_navmesh_info is None:
            node_navmesh_info = {}

        # Get navmesh A (must ALWAYS be present).
        if self.navmesh_a is None:
            raise NavGraphExportError(f"Node '{self.name}' does not have Navmesh A set.")
        navmesh_a_name = self.navmesh_a.name  # type: str
        navmesh_a_triangles = self.navmesh_a_triangles
        node_navmesh_info[navmesh_a_name] = navmesh_a_triangles
        if navmesh_nodes is not None:
            try:
                navmesh_a_nodes = navmesh_nodes[navmesh_a_name]
            except KeyError:
                raise KeyError(f"Navmesh A '{navmesh_a_name}' not found in `navmesh_nodes`.")
            navmesh_a_nodes.append(node)

        if self.navmesh_b is None:
            raise NavGraphExportError(f"Node '{self.name}' does not have Navmesh B set.")
        navmesh_b_name = self.navmesh_b.name  # type: str
        navmesh_b_triangles = self.navmesh_b_triangles
        node_navmesh_info[navmesh_b_name] = navmesh_b_triangles
        if navmesh_nodes is not None:
            try:
                navmesh_b_nodes = navmesh_nodes[navmesh_b_name]
            except KeyError:
                raise KeyError(f"Navmesh B '{navmesh_b_name}' not found in `navmesh_nodes`.")
            navmesh_b_nodes.append(node)

        if not navmesh_a_triangles and not navmesh_b_triangles:
            raise NavGraphExportError(
                f"Node '{self.name}' does not have any triangles set for Navmesh A or B. One of them is "
                f"permitted to be missing, if that navmesh is a dead end, but not both."
            )

        return node


class BlenderMCGEdge(BaseBlenderSoulstructObject[MCGEdge, MCGEdgeProps]):

    TYPE = SoulstructType.MCG_EDGE
    BL_OBJ_TYPE = ObjectType.EMPTY
    SOULSTRUCT_CLASS = MCGEdge

    __slots__ = []

    @property
    def node_a(self) -> bpy.types.Object | None:
        return self.type_properties.node_a

    @node_a.setter
    def node_a(self, value: bpy.types.Object | None):
        self.type_properties.node_a = value

    @property
    def node_b(self) -> bpy.types.Object | None:
        return self.type_properties.node_b

    @node_b.setter
    def node_b(self, value: bpy.types.Object | None):
        self.type_properties.node_b = value

    @property
    def navmesh_part(self) -> bpy.types.MeshObject | None:
        return self.type_properties.navmesh_part

    @navmesh_part.setter
    def navmesh_part(self, value: bpy.types.MeshObject | None):
        self.type_properties.navmesh_part = value

    @property
    def cost(self) -> float:
        return self.type_properties.cost

    @cost.setter
    def cost(self, value: float):
        self.type_properties.cost = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MCGEdge,
        name: str,
        collection: bpy.types.Collection = None,
        navmesh_name="",
        node_a: bpy.types.Object = None,
        node_b: bpy.types.Object = None,
    ) -> BlenderMCGEdge:
        bl_edge = cls.new(name, data=None, collection=collection)  # type: BlenderMCGEdge
        bl_edge.obj.empty_display_type = "PLAIN_AXES"
        bl_edge.obj.location = (node_a.location + node_b.location) / 2.0
        # Point empty arrow in direction of edge.
        bl_edge.obj.rotation_euler = (node_b.location - node_a.location).to_track_quat('Z', 'Y').to_euler()

        # TODO: Only search in appropriate MSB collection.
        navmesh_part = find_obj(navmesh_name, soulstruct_type=SoulstructType.MSB_PART)
        if navmesh_part is None:
            # Not acceptable. Parts must be imported before MCG.
            raise NavGraphMissingNavmeshError(f"'{bl_edge.name}' references missing MSB Navmesh object: {navmesh_name}")

        bl_edge.cost = soulstruct_obj.cost
        bl_edge.navmesh_part = navmesh_part
        bl_edge.node_a = node_a
        bl_edge.node_b = node_b
        return bl_edge

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        navmesh_part_indices: dict[str, int] = None,
        node_navmesh_triangles: list[dict[str, list[int]]] = None,
        node_indices: dict[str, int] = None,
        nodes: list[MCGNode] = None,
        map_id: tuple[int, int, int, int] = None,
    ) -> MCGEdge:
        """Lots of existing node/triangle data from full `MCG` export required here.

        Args:
            operator: Calling `LoggingOperator` for error/warning messages.
            context: Operator's Blender context.
            navmesh_part_indices: Mapping of navmesh part names to their indices in the MSB.
            node_navmesh_triangles: List of dictionaries mapping node indices to navmesh part names to triangle indices.
            node_indices: Mapping of node names to their indices in the MCG.
                NOTE: '<DEAD END>' suffix (or any suffix after '<') has already been stripped from these keys.
            nodes: List of all nodes in the MCG.
            map_id: Tuple of four integers representing the map ID of the MCG.
        """
        if not navmesh_part_indices:
            raise ValueError("`navmesh_part_indices` must be provided to export `MCGEdge`.")
        if not node_navmesh_triangles:
            raise ValueError("`node_navmesh_triangles` must be provided to export `MCGEdge`.")
        if not node_indices:
            raise ValueError("`node_indices` must be provided to export `MCGEdge`.")
        if not nodes:
            raise ValueError("`nodes` must be provided to export `MCGEdge`.")
        if not map_id:
            raise ValueError("`map_id` must be provided to export `MCGEdge`.")

        edge = MCGEdge(map_id=map_id, cost=self.cost)
        if not self.navmesh_part:
            raise NavGraphExportError(f"Edge '{self.name}' does not have a Navmesh Part set.")
        navmesh_part_name = BlenderNVM(self.navmesh_part).game_name
        try:
            navmesh_index = navmesh_part_indices[navmesh_part_name]
        except KeyError:
            raise NavGraphExportError(
                f"Cannot get MSB index of MCG edge's referenced MSB Navmesh part: {navmesh_part_name}"
            )
        edge.navmesh_index = navmesh_index

        if not self.node_a:
            raise NavGraphExportError(f"Edge '{self.name}' does not have a Node A set.")
        if not self.node_b:
            raise NavGraphExportError(f"Edge '{self.name}' does not have a Node B set.")

        # Strip down node names to match dictionary keys.
        node_a_name = _get_node_name_stem(self.node_a)
        node_b_name = _get_node_name_stem(self.node_b)

        try:
            node_a_index = node_indices[node_a_name]
        except KeyError:
            print(node_indices)
            raise NavGraphExportError(
                f"Cannot get node index of '{self.name}' start node: '{node_a_name}' (originally '{self.node_a.name}')."
            )
        try:
            node_b_index = node_indices[node_b_name]
        except KeyError:
            print(node_indices)
            raise NavGraphExportError(
                f"Cannot get node index of '{self.name}' end node: '{node_b_name}' (originally '{self.node_b.name}')."
            )

        node_a = nodes[node_a_index]
        node_b = nodes[node_b_index]
        edge.node_a = node_a
        edge.node_b = node_b
        node_a.connected_nodes.append(node_b)
        node_a.connected_edges.append(edge)
        node_b.connected_nodes.append(node_a)
        node_b.connected_edges.append(edge)

        for nav, index in [("a", node_a_index), ("b", node_b_index)]:
            try:
                nav_triangles = node_navmesh_triangles[index][navmesh_part_name]
                setattr(edge, f"node_{nav}_triangles", nav_triangles)
            except KeyError:
                bl_node = self.node_a if nav == "a" else self.node_b
                raise NavGraphExportError(
                    f"Node {bl_node.name} does not specify its triangles in MSB Navmesh part {navmesh_part_name} "
                    f"(edge {self.name}). You must fix your navmeshes and navmesh graph in Blender first."
                )

        return edge


def _get_node_name_stem(node_obj: bpy.types.Object) -> str:
    """Strip '<DEAD END>' and any other '<' suffix from tight node name (and anything from first period)."""
    return node_obj.name.split(".")[0].split("<")[0].strip()
