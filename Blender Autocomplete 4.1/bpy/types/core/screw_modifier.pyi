import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ScrewModifier(Modifier, bpy_struct):
    """Revolve edges"""

    angle: float
    """ Angle of revolution

    :type: float
    """

    axis: str
    """ Screw axis

    :type: str
    """

    iterations: int
    """ Number of times to apply the screw operation

    :type: int
    """

    merge_threshold: float
    """ Limit below which to merge vertices

    :type: float
    """

    object: Object
    """ Object to define the screw axis

    :type: Object
    """

    render_steps: int
    """ Number of steps in the revolution

    :type: int
    """

    screw_offset: float
    """ Offset the revolution along its axis

    :type: float
    """

    steps: int
    """ Number of steps in the revolution

    :type: int
    """

    use_merge_vertices: bool
    """ Merge adjacent vertices (screw offset must be zero)

    :type: bool
    """

    use_normal_calculate: bool
    """ Calculate the order of edges (needed for meshes, but not curves)

    :type: bool
    """

    use_normal_flip: bool
    """ Flip normals of lathed faces

    :type: bool
    """

    use_object_screw_offset: bool
    """ Use the distance between the objects to make a screw

    :type: bool
    """

    use_smooth_shade: bool
    """ Output faces with smooth shading rather than flat shaded

    :type: bool
    """

    use_stretch_u: bool
    """ Stretch the U coordinates between 0 and 1 when UVs are present

    :type: bool
    """

    use_stretch_v: bool
    """ Stretch the V coordinates between 0 and 1 when UVs are present

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
