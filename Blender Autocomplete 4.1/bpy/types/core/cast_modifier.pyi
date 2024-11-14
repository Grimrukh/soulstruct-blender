import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CastModifier(Modifier, bpy_struct):
    """Modifier to cast to other shapes"""

    cast_type: str
    """ Target object shape

    :type: str
    """

    factor: float
    """ 

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    object: Object
    """ Control object: if available, its location determines the center of the effect

    :type: Object
    """

    radius: float
    """ Only deform vertices within this distance from the center of the effect (leave as 0 for infinite.)

    :type: float
    """

    size: float
    """ Size of projection shape (leave as 0 for auto)

    :type: float
    """

    use_radius_as_size: bool
    """ Use radius as size of projection shape (0 = auto)

    :type: bool
    """

    use_transform: bool
    """ Use object transform to control projection shape

    :type: bool
    """

    use_x: bool
    """ 

    :type: bool
    """

    use_y: bool
    """ 

    :type: bool
    """

    use_z: bool
    """ 

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
