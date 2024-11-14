import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .f_modifier import FModifier
from .action import Action
from .struct import Struct
from .nla_strip_f_curves import NlaStripFCurves
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NlaStrip(bpy_struct):
    """A container referencing an existing Action"""

    action: Action
    """ Action referenced by this strip

    :type: Action
    """

    action_frame_end: float
    """ Last frame from action to use

    :type: float
    """

    action_frame_start: float
    """ First frame from action to use

    :type: float
    """

    active: bool
    """ NLA Strip is active

    :type: bool
    """

    blend_in: float
    """ Number of frames at start of strip to fade in influence

    :type: float
    """

    blend_out: float
    """ 

    :type: float
    """

    blend_type: str
    """ Method used for combining strip's result with accumulated result

    :type: str
    """

    extrapolation: str
    """ Action to take for gaps past the strip extents

    :type: str
    """

    fcurves: NlaStripFCurves
    """ F-Curves for controlling the strip's influence and timing

    :type: NlaStripFCurves
    """

    frame_end: float
    """ 

    :type: float
    """

    frame_end_raw: float
    """ Same as frame_end, except that any value can be set, including ones that create an invalid state

    :type: float
    """

    frame_end_ui: float
    """ End frame of the NLA strip. Note: changing this value also updates the value of the strip's repeats or its action's end frame. If only the end frame should be changed, see the "frame_end" property instead

    :type: float
    """

    frame_start: float
    """ 

    :type: float
    """

    frame_start_raw: float
    """ Same as frame_start, except that any value can be set, including ones that create an invalid state

    :type: float
    """

    frame_start_ui: float
    """ Start frame of the NLA strip. Note: changing this value also updates the value of the strip's end frame. If only the start frame should be changed, see the "frame_start" property instead

    :type: float
    """

    influence: float
    """ Amount the strip contributes to the current result

    :type: float
    """

    modifiers: bpy_prop_collection[FModifier]
    """ Modifiers affecting all the F-Curves in the referenced Action

    :type: bpy_prop_collection[FModifier]
    """

    mute: bool
    """ Disable NLA Strip evaluation

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    repeat: float
    """ Number of times to repeat the action range

    :type: float
    """

    scale: float
    """ Scaling factor for action

    :type: float
    """

    select: bool
    """ NLA Strip is selected

    :type: bool
    """

    strip_time: float
    """ Frame of referenced Action to evaluate

    :type: float
    """

    strips: bpy_prop_collection[NlaStrip]
    """ NLA Strips that this strip acts as a container for (if it is of type Meta)

    :type: bpy_prop_collection[NlaStrip]
    """

    type: str
    """ Type of NLA Strip

    :type: str
    """

    use_animated_influence: bool
    """ Influence setting is controlled by an F-Curve rather than automatically determined

    :type: bool
    """

    use_animated_time: bool
    """ Strip time is controlled by an F-Curve rather than automatically determined

    :type: bool
    """

    use_animated_time_cyclic: bool
    """ Cycle the animated time within the action start and end

    :type: bool
    """

    use_auto_blend: bool
    """ Number of frames for Blending In/Out is automatically determined from overlapping strips

    :type: bool
    """

    use_reverse: bool
    """ NLA Strip is played back in reverse order (only when timing is automatically determined)

    :type: bool
    """

    use_sync_length: bool
    """ Update range of frames referenced from action after tweaking strip and its keyframes

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
