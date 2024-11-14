import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BuildGpencilModifier(GpencilModifier, bpy_struct):
    """Animate strokes appearing and disappearing"""

    concurrent_time_alignment: str
    """ How should strokes start to appear/disappear

    :type: str
    """

    fade_factor: float
    """ Defines how much of the stroke is fading in/out

    :type: float
    """

    fade_opacity_strength: float
    """ How much strength fading applies on top of stroke opacity

    :type: float
    """

    fade_thickness_strength: float
    """ How much strength fading applies on top of stroke thickness

    :type: float
    """

    frame_end: float
    """ End Frame (when Restrict Frame Range is enabled)

    :type: float
    """

    frame_start: float
    """ Start Frame (when Restrict Frame Range is enabled)

    :type: float
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    length: float
    """ Maximum number of frames that the build effect can run for (unless another GP keyframe occurs before this time has elapsed)

    :type: float
    """

    mode: str
    """ How strokes are being built

    :type: str
    """

    object: Object
    """ Object used as build starting position

    :type: Object
    """

    percentage_factor: float
    """ Defines how much of the stroke is visible

    :type: float
    """

    speed_factor: float
    """ Multiply recorded drawing speed by a factor

    :type: float
    """

    speed_maxgap: float
    """ The maximum gap between strokes in seconds

    :type: float
    """

    start_delay: float
    """ Number of frames after each GP keyframe before the modifier has any effect

    :type: float
    """

    target_vertex_group: str
    """ Output Vertex group

    :type: str
    """

    time_mode: str
    """ Use drawing speed, a number of frames, or a manual factor to build strokes

    :type: str
    """

    transition: str
    """ How are strokes animated (i.e. are they appearing or disappearing)

    :type: str
    """

    use_fading: bool
    """ Fade out strokes instead of directly cutting off

    :type: bool
    """

    use_percentage: bool
    """ Use a percentage factor to determine the visible points

    :type: bool
    """

    use_restrict_frame_range: bool
    """ Only modify strokes during the specified frame range

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
