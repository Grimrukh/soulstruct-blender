import typing
import collections.abc
import mathutils
import numpy as np
from .mesh_polygons import MeshPolygons
from .mesh_normal_value import MeshNormalValue
from .loop_colors import LoopColors
from .anim_data import AnimData
from .mesh_skin_vertex_layer import MeshSkinVertexLayer
from .mesh_uv_loop_layer import MeshUVLoopLayer
from .struct import Struct
from .attribute_group import AttributeGroup
from .bpy_prop_collection import bpy_prop_collection
from .key import Key
from .bpy_prop_array import bpy_prop_array
from .read_only_integer import ReadOnlyInteger
from .mesh_loop_triangles import MeshLoopTriangles
from .mesh_vertices import MeshVertices
from .uv_loop_layers import UVLoopLayers
from .bpy_struct import bpy_struct
from .id import ID
from .mesh_edges import MeshEdges
from .mesh_loops import MeshLoops
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Mesh(ID, bpy_struct):
    """Mesh data-block defining geometric surfaces"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    attributes: AttributeGroup
    """ Geometry attributes

    :type: AttributeGroup
    """

    auto_texspace: bool
    """ Adjust active object's texture space automatically when transforming object

    :type: bool
    """

    color_attributes: AttributeGroup
    """ Geometry color attributes

    :type: AttributeGroup
    """

    corner_normals: bpy_prop_collection[MeshNormalValue]
    """ The "slit" normal direction of each face corner, influenced by vertex normals, sharp faces, sharp edges, and custom normals. May be empty

    :type: bpy_prop_collection[MeshNormalValue]
    """

    cycles: typing.Any
    """ Cycles mesh settings

    :type: typing.Any
    """

    edges: MeshEdges
    """ Edges of the mesh

    :type: MeshEdges
    """

    has_custom_normals: bool
    """ True if there are custom split normals data in this mesh

    :type: bool
    """

    is_editmode: bool
    """ True when used in editmode

    :type: bool
    """

    loop_triangle_polygons: bpy_prop_collection[ReadOnlyInteger]
    """ The face index for each loop triangle

    :type: bpy_prop_collection[ReadOnlyInteger]
    """

    loop_triangles: MeshLoopTriangles
    """ Tessellation of mesh polygons into triangles

    :type: MeshLoopTriangles
    """

    loops: MeshLoops
    """ Loops of the mesh (face corners)

    :type: MeshLoops
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    normals_domain: str
    """ The attribute domain that gives enough information to represent the mesh's normals

    :type: str
    """

    polygon_normals: bpy_prop_collection[MeshNormalValue]
    """ The normal direction of each face, defined by the winding order and position of its vertices

    :type: bpy_prop_collection[MeshNormalValue]
    """

    polygons: MeshPolygons
    """ Polygons of the mesh

    :type: MeshPolygons
    """

    remesh_mode: str
    """ 

    :type: str
    """

    remesh_voxel_adaptivity: float
    """ Reduces the final face count by simplifying geometry where detail is not needed, generating triangles. A value greater than 0 disables Fix Poles

    :type: float
    """

    remesh_voxel_size: float
    """ Size of the voxel in object space used for volume evaluation. Lower values preserve finer details

    :type: float
    """

    shape_keys: Key
    """ 

    :type: Key
    """

    skin_vertices: bpy_prop_collection[MeshSkinVertexLayer]
    """ All skin vertices

    :type: bpy_prop_collection[MeshSkinVertexLayer]
    """

    texco_mesh: Mesh
    """ Derive texture coordinates from another mesh

    :type: Mesh
    """

    texspace_location: mathutils.Vector
    """ Texture space location

    :type: mathutils.Vector
    """

    texspace_size: mathutils.Vector
    """ Texture space size

    :type: mathutils.Vector
    """

    texture_mesh: Mesh
    """ Use another mesh for texture indices (vertex indices must be aligned)

    :type: Mesh
    """

    total_edge_sel: int
    """ Selected edge count in editmode

    :type: int
    """

    total_face_sel: int
    """ Selected face count in editmode

    :type: int
    """

    total_vert_sel: int
    """ Selected vertex count in editmode

    :type: int
    """

    use_auto_texspace: bool
    """ Adjust active object's texture space automatically when transforming object

    :type: bool
    """

    use_mirror_topology: bool
    """ Use topology based mirroring (for when both sides of mesh have matching, unique topology)

    :type: bool
    """

    use_mirror_vertex_groups: bool
    """ Mirror the left/right vertex groups when painting. The symmetry axis is determined by the symmetry settings

    :type: bool
    """

    use_mirror_x: bool
    """ Enable symmetry in the X axis

    :type: bool
    """

    use_mirror_y: bool
    """ Enable symmetry in the Y axis

    :type: bool
    """

    use_mirror_z: bool
    """ Enable symmetry in the Z axis

    :type: bool
    """

    use_paint_bone_selection: bool
    """ Bone selection during painting

    :type: bool
    """

    use_paint_mask: bool
    """ Face selection masking for painting

    :type: bool
    """

    use_paint_mask_vertex: bool
    """ Vertex selection masking for painting

    :type: bool
    """

    use_remesh_fix_poles: bool
    """ Produces fewer poles and a better topology flow

    :type: bool
    """

    use_remesh_preserve_attributes: bool
    """ Transfer all attributes to the new mesh

    :type: bool
    """

    use_remesh_preserve_volume: bool
    """ Projects the mesh to preserve the volume and details of the original mesh

    :type: bool
    """

    uv_layer_clone: MeshUVLoopLayer
    """ UV loop layer to be used as cloning source

    :type: MeshUVLoopLayer
    """

    uv_layer_clone_index: int
    """ Clone UV loop layer index

    :type: int
    """

    uv_layer_stencil: MeshUVLoopLayer
    """ UV loop layer to mask the painted area

    :type: MeshUVLoopLayer
    """

    uv_layer_stencil_index: int
    """ Mask UV loop layer index

    :type: int
    """

    uv_layers: UVLoopLayers
    """ All UV loop layers

    :type: UVLoopLayers
    """

    vertex_colors: LoopColors
    """ Legacy vertex color layers. Deprecated, use color attributes instead

    :type: LoopColors
    """

    vertex_normals: bpy_prop_collection[MeshNormalValue]
    """ The normal direction of each vertex, defined as the average of the surrounding face normals

    :type: bpy_prop_collection[MeshNormalValue]
    """

    vertices: MeshVertices
    """ Vertices of the mesh

    :type: MeshVertices
    """

    edge_creases: typing.Any
    """ Edge crease values for subdivision surface, corresponding to the "crease_edge" attribute.(readonly)"""

    edge_keys: typing.Any
    """ (readonly)"""

    vertex_creases: typing.Any
    """ Vertex crease values for subdivision surface, corresponding to the "crease_vert" attribute.(readonly)"""

    vertex_paint_mask: typing.Any
    """ Mask values for sculpting and painting, corresponding to the ".sculpt_mask" attribute.(readonly)"""

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        shape_keys: bool | typing.Any | None = False,
    ):
        """Transform mesh vertices by a matrix (Warning: inverts normals if matrix is negative)

        :param matrix: Matrix
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param shape_keys: Transform Shape Keys
        :type shape_keys: bool | typing.Any | None
        """
        ...

    def flip_normals(self):
        """Invert winding of all polygons (clears tessellation, does not handle custom normals)"""
        ...

    def set_sharp_from_angle(self, angle: typing.Any | None = 3.14159):
        """Reset and fill the "sharp_edge" attribute based on the angle of faces neighboring manifold edges

        :param angle: Angle, Angle between faces beyond which edges are marked sharp
        :type angle: typing.Any | None
        """
        ...

    def split_faces(self):
        """Split faces based on the edge angle"""
        ...

    def calc_tangents(self, uvmap: str | typing.Any = ""):
        """Compute tangents and bitangent signs, to be used together with the split normals to get a complete tangent space for normal mapping (split normals are also computed if not yet present)

        :param uvmap: Name of the UV map to use for tangent space computation
        :type uvmap: str | typing.Any
        """
        ...

    def free_tangents(self):
        """Free tangents"""
        ...

    def calc_loop_triangles(self):
        """Calculate loop triangle tessellation (supports editmode too)"""
        ...

    def calc_smooth_groups(self, use_bitflags: bool | typing.Any | None = False):
        """Calculate smooth groups from sharp edges

                :param use_bitflags: Produce bitflags groups instead of simple numeric values
                :type use_bitflags: bool | typing.Any | None
                :return: poly_groups, Smooth Groups, int array of 1 items in [-inf, inf]

        groups, Total number of groups, int in [0, inf]
        """
        ...

    def normals_split_custom_set(
        self,
        normals: typing.Union[
            list[list[float]],
            tuple[tuple[float], tuple[float], tuple[float]],
            np.ndarray,
            None,
        ],
    ):
        """Define custom split normals of this mesh (use zero-vectors to keep auto ones)

        :param normals: Normals
        :type normals: list[list[float]] | tuple[tuple[float], tuple[float], tuple[float]] | None
        """
        ...

    def normals_split_custom_set_from_vertices(
        self,
        normals: list[list[float]]
        | tuple[tuple[float], tuple[float], tuple[float]]
        | None,
    ):
        """Define custom split normals of this mesh, from vertices' normals (use zero-vectors to keep auto ones)

        :param normals: Normals
        :type normals: list[list[float]] | tuple[tuple[float], tuple[float], tuple[float]] | None
        """
        ...

    def update(
        self,
        calc_edges: bool | typing.Any | None = False,
        calc_edges_loose: bool | typing.Any | None = False,
    ):
        """update

        :param calc_edges: Calculate Edges, Force recalculation of edges
        :type calc_edges: bool | typing.Any | None
        :param calc_edges_loose: Calculate Loose Edges, Calculate the loose state of each edge
        :type calc_edges_loose: bool | typing.Any | None
        """
        ...

    def update_gpu_tag(self):
        """update_gpu_tag"""
        ...

    def unit_test_compare(
        self, mesh: Mesh | None = None, threshold: typing.Any | None = 7.1526e-06
    ) -> str | typing.Any:
        """unit_test_compare

        :param mesh: Mesh to compare to
        :type mesh: Mesh | None
        :param threshold: Threshold, Comparison tolerance threshold
        :type threshold: typing.Any | None
        :return: Return value, String description of result of comparison
        :rtype: str | typing.Any
        """
        ...

    def clear_geometry(self):
        """Remove all geometry from the mesh. Note that this does not free shape keys or materials"""
        ...

    def validate(
        self,
        verbose: bool | typing.Any | None = False,
        clean_customdata: bool | typing.Any | None = True,
    ) -> bool:
        """Validate geometry, return True when the mesh has had invalid geometry corrected/removed

        :param verbose: Verbose, Output information about the errors found
        :type verbose: bool | typing.Any | None
        :param clean_customdata: Clean Custom Data, Remove temp/cached custom-data layers, like e.g. normals...
        :type clean_customdata: bool | typing.Any | None
        :return: Result
        :rtype: bool
        """
        ...

    def validate_material_indices(self) -> bool:
        """Validate material indices of polygons, return True when the mesh has had invalid indices corrected (to default 0)

        :return: Result
        :rtype: bool
        """
        ...

    def count_selected_items(self) -> bpy_prop_array[int]:
        """Return the number of selected items (vert, edge, face)

        :return: Result
        :rtype: bpy_prop_array[int]
        """
        ...

    def edge_creases_ensure(self): ...
    def edge_creases_remove(self): ...
    def from_pydata(
        self,
        vertices: list | np.ndarray | None,
        edges: list | np.ndarray | None,
        faces: list | np.ndarray | None,
        shade_flat=True,
    ):
        """Make a mesh from a list of vertices/edges/faces
        Until we have a nicer way to make geometry, use this.

                :param vertices: float triplets each representing (X, Y, Z)
        eg: [(0.0, 1.0, 0.5), ...].
                :type vertices: list | None
                :param edges: int pairs, each pair contains two indices to the
        vertices argument. eg: [(1, 2), ...]

        When an empty iterable is passed in, the edges are inferred from the polygons.
                :type edges: list | None
                :param faces: iterator of faces, each faces contains three or more indices to
        the vertices argument. eg: [(5, 6, 8, 9), (1, 2, 3), ...]
                :type faces: list | None
                :param shade_flat:
        """
        ...

    def shade_flat(self):
        """Render and display faces uniform, using face normals,
        setting the "sharp_face" attribute true for every face

        """
        ...

    def shade_smooth(self):
        """Render and display faces smooth, using interpolated vertex normals,
        removing the "sharp_face" attribute

        """
        ...

    def vertex_creases_ensure(self): ...
    def vertex_creases_remove(self): ...
    def vertex_paint_mask_ensure(self): ...
    def vertex_paint_mask_remove(self): ...
    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...
