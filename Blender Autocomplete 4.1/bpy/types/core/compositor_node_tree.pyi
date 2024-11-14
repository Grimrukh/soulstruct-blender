import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeTree(NodeTree, ID, bpy_struct):
    """Node tree consisting of linked nodes used for compositing"""

    chunk_size: str
    """ Max size of a tile (smaller values gives better distribution of multiple threads, but more overhead)

    :type: str
    """

    edit_quality: str
    """ Quality when editing

    :type: str
    """

    execution_mode: str
    """ Set how compositing is executed

    :type: str
    """

    precision: str
    """ The precision of compositor intermediate result

    :type: str
    """

    render_quality: str
    """ Quality when rendering

    :type: str
    """

    use_groupnode_buffer: bool
    """ Enable buffering of group nodes

    :type: bool
    """

    use_opencl: bool
    """ Enable GPU calculations

    :type: bool
    """

    use_two_pass: bool
    """ Use two pass execution during editing: first calculate fast nodes, second pass calculate all nodes

    :type: bool
    """

    use_viewer_border: bool
    """ Use boundaries for viewer nodes and composite backdrop

    :type: bool
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
