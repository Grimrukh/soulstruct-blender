import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskModifier(Modifier, bpy_struct):
    """Mask modifier to hide parts of the mesh"""

    armature: Object
    """ Armature to use as source of bones to mask

    :type: Object
    """

    invert_vertex_group: bool
    """ Use vertices that are not part of region defined

    :type: bool
    """

    mode: str
    """ 

    :type: str
    """

    threshold: float
    """ Weights over this threshold remain

    :type: float
    """

    use_smooth: bool
    """ Use vertex group weights to cut faces at the weight contour

    :type: bool
    """

    vertex_group: str
    """ Vertex group name

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
