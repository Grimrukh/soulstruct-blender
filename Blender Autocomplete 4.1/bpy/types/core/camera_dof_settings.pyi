import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CameraDOFSettings(bpy_struct):
    """Depth of Field settings"""

    aperture_blades: int
    """ Number of blades in aperture for polygonal bokeh (at least 3)

    :type: int
    """

    aperture_fstop: float
    """ F-Stop ratio (lower numbers give more defocus, higher numbers give a sharper image)

    :type: float
    """

    aperture_ratio: float
    """ Distortion to simulate anamorphic lens bokeh

    :type: float
    """

    aperture_rotation: float
    """ Rotation of blades in aperture

    :type: float
    """

    focus_distance: float
    """ Distance to the focus point for depth of field

    :type: float
    """

    focus_object: Object
    """ Use this object to define the depth of field focal point

    :type: Object
    """

    focus_subtarget: str
    """ Use this armature bone to define the depth of field focal point

    :type: str
    """

    use_dof: bool
    """ Use Depth of Field

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
