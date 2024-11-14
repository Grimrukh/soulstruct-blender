import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WireframeModifier(Modifier, bpy_struct):
    """Wireframe effect modifier"""

    crease_weight: float
    """ Crease weight (if active)

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    material_offset: int
    """ Offset material index of generated faces

    :type: int
    """

    offset: float
    """ Offset the thickness from the center

    :type: float
    """

    thickness: float
    """ Thickness factor

    :type: float
    """

    thickness_vertex_group: float
    """ Thickness factor to use for zero vertex group influence

    :type: float
    """

    use_boundary: bool
    """ Support face boundaries

    :type: bool
    """

    use_crease: bool
    """ Crease hub edges for improved subdivision surface

    :type: bool
    """

    use_even_offset: bool
    """ Scale the offset to give more even thickness

    :type: bool
    """

    use_relative_offset: bool
    """ Scale the offset by surrounding geometry

    :type: bool
    """

    use_replace: bool
    """ Remove original geometry

    :type: bool
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
