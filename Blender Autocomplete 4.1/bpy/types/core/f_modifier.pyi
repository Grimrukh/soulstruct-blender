import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifier(bpy_struct):
    """Modifier for values of F-Curve"""

    active: bool | None
    """ F-Curve modifier will show settings in the editor

    :type: bool | None
    """

    blend_in: float
    """ Number of frames from start frame for influence to take effect

    :type: float
    """

    blend_out: float
    """ Number of frames from end frame for influence to fade out

    :type: float
    """

    frame_end: float
    """ Frame that modifier's influence ends (if Restrict Frame Range is in use)

    :type: float
    """

    frame_start: float
    """ Frame that modifier's influence starts (if Restrict Frame Range is in use)

    :type: float
    """

    influence: float
    """ Amount of influence F-Curve Modifier will have when not fading in/out

    :type: float
    """

    is_valid: bool
    """ F-Curve Modifier has invalid settings and will not be evaluated

    :type: bool
    """

    mute: bool
    """ Enable F-Curve modifier evaluation

    :type: bool
    """

    name: str
    """ F-Curve Modifier name

    :type: str
    """

    show_expanded: bool
    """ F-Curve Modifier's panel is expanded in UI

    :type: bool
    """

    type: str
    """ F-Curve Modifier Type

    :type: str
    """

    use_influence: bool
    """ F-Curve Modifier's effects will be tempered by a default factor

    :type: bool
    """

    use_restricted_range: bool
    """ F-Curve Modifier is only applied for the specified frame range to help mask off effects in order to chain them

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
