import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ExplodeModifier(Modifier, bpy_struct):
    """Explosion effect modifier based on a particle system"""

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    particle_uv: str
    """ UV map to change with particle age

    :type: str
    """

    protect: float
    """ Clean vertex group edges

    :type: float
    """

    show_alive: bool
    """ Show mesh when particles are alive

    :type: bool
    """

    show_dead: bool
    """ Show mesh when particles are dead

    :type: bool
    """

    show_unborn: bool
    """ Show mesh when particles are unborn

    :type: bool
    """

    use_edge_cut: bool
    """ Cut face edges for nicer shrapnel

    :type: bool
    """

    use_size: bool
    """ Use particle size for the shrapnel

    :type: bool
    """

    vertex_group: str
    """ 

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
