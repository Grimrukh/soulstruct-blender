import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SkinModifier(Modifier, bpy_struct):
    """Generate Skin"""

    branch_smoothing: float
    """ Smooth complex geometry around branches

    :type: float
    """

    use_smooth_shade: bool
    """ Output faces with smooth shading rather than flat shaded

    :type: bool
    """

    use_x_symmetry: bool
    """ Avoid making unsymmetrical quads across the X axis

    :type: bool
    """

    use_y_symmetry: bool
    """ Avoid making unsymmetrical quads across the Y axis

    :type: bool
    """

    use_z_symmetry: bool
    """ Avoid making unsymmetrical quads across the Z axis

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
