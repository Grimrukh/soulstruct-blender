import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DataTransferModifier(Modifier, bpy_struct):
    """Modifier transferring some data from a source mesh"""

    data_types_edges: set[str]
    """ Which edge data layers to transfer

    :type: set[str]
    """

    data_types_loops: set[str]
    """ Which face corner data layers to transfer

    :type: set[str]
    """

    data_types_polys: set[str]
    """ Which face data layers to transfer

    :type: set[str]
    """

    data_types_verts: set[str]
    """ Which vertex data layers to transfer

    :type: set[str]
    """

    edge_mapping: str
    """ Method used to map source edges to destination ones

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    islands_precision: float
    """ Factor controlling precision of islands handling (typically, 0.1 should be enough, higher values can make things really slow)

    :type: float
    """

    layers_uv_select_dst: str
    """ How to match source and destination layers

    :type: str
    """

    layers_uv_select_src: str
    """ Which layers to transfer, in case of multi-layers types

    :type: str
    """

    layers_vcol_loop_select_dst: str
    """ How to match source and destination layers

    :type: str
    """

    layers_vcol_loop_select_src: str
    """ Which layers to transfer, in case of multi-layers types

    :type: str
    """

    layers_vcol_vert_select_dst: str
    """ How to match source and destination layers

    :type: str
    """

    layers_vcol_vert_select_src: str
    """ Which layers to transfer, in case of multi-layers types

    :type: str
    """

    layers_vgroup_select_dst: str
    """ How to match source and destination layers

    :type: str
    """

    layers_vgroup_select_src: str
    """ Which layers to transfer, in case of multi-layers types

    :type: str
    """

    loop_mapping: str
    """ Method used to map source faces' corners to destination ones

    :type: str
    """

    max_distance: float
    """ Maximum allowed distance between source and destination element, for non-topology mappings

    :type: float
    """

    mix_factor: float
    """ Factor to use when applying data to destination (exact behavior depends on mix mode, multiplied with weights from vertex group when defined)

    :type: float
    """

    mix_mode: str
    """ How to affect destination elements with source values

    :type: str
    """

    object: Object
    """ Object to transfer data from

    :type: Object
    """

    poly_mapping: str
    """ Method used to map source faces to destination ones

    :type: str
    """

    ray_radius: float
    """ 'Width' of rays (especially useful when raycasting against vertices or edges)

    :type: float
    """

    use_edge_data: bool
    """ Enable edge data transfer

    :type: bool
    """

    use_loop_data: bool
    """ Enable face corner data transfer

    :type: bool
    """

    use_max_distance: bool
    """ Source elements must be closer than given distance from destination one

    :type: bool
    """

    use_object_transform: bool
    """ Evaluate source and destination meshes in global space

    :type: bool
    """

    use_poly_data: bool
    """ Enable face data transfer

    :type: bool
    """

    use_vert_data: bool
    """ Enable vertex data transfer

    :type: bool
    """

    vert_mapping: str
    """ Method used to map source vertices to destination ones

    :type: str
    """

    vertex_group: str
    """ Vertex group name for selecting the affected areas

    :type: str
    """

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
