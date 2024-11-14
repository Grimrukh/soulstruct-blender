import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .object import Object
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxShadow(ShaderFx, bpy_struct):
    """Shadow effect"""

    amplitude: float
    """ Amplitude of Wave

    :type: float
    """

    blur: bpy_prop_array[int]
    """ Number of pixels for blurring shadow (set to 0 to disable)

    :type: bpy_prop_array[int]
    """

    object: Object
    """ Object to determine center of rotation

    :type: Object
    """

    offset: bpy_prop_array[int]
    """ Offset of the shadow

    :type: bpy_prop_array[int]
    """

    orientation: str
    """ Direction of the wave

    :type: str
    """

    period: float
    """ Period of Wave

    :type: float
    """

    phase: float
    """ Phase Shift of Wave

    :type: float
    """

    rotation: float
    """ Rotation around center or object

    :type: float
    """

    samples: int
    """ Number of Blur Samples (zero, disable blur)

    :type: int
    """

    scale: mathutils.Vector
    """ Scale of the shadow

    :type: mathutils.Vector
    """

    shadow_color: bpy_prop_array[float]
    """ Color used for Shadow

    :type: bpy_prop_array[float]
    """

    use_object: bool
    """ Use object as center of rotation

    :type: bool
    """

    use_wave: bool
    """ Use wave effect

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
