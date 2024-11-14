import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .f_curve_sample import FCurveSample
from .driver import Driver
from .struct import Struct
from .bpy_struct import bpy_struct
from .action_group import ActionGroup
from .f_curve_modifiers import FCurveModifiers
from .f_curve_keyframe_points import FCurveKeyframePoints

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FCurve(bpy_struct):
    """F-Curve defining values of a period of time"""

    array_index: int
    """ Index to the specific property affected by F-Curve if applicable

    :type: int
    """

    auto_smoothing: str
    """ Algorithm used to compute automatic handles

    :type: str
    """

    color: mathutils.Color
    """ Color of the F-Curve in the Graph Editor

    :type: mathutils.Color
    """

    color_mode: str
    """ Method used to determine color of F-Curve in Graph Editor

    :type: str
    """

    data_path: str
    """ RNA Path to property affected by F-Curve

    :type: str
    """

    driver: Driver
    """ Channel Driver (only set for Driver F-Curves)

    :type: Driver
    """

    extrapolation: str
    """ Method used for evaluating value of F-Curve outside first and last keyframes

    :type: str
    """

    group: ActionGroup
    """ Action Group that this F-Curve belongs to

    :type: ActionGroup
    """

    hide: bool
    """ F-Curve and its keyframes are hidden in the Graph Editor graphs

    :type: bool
    """

    is_empty: bool
    """ True if the curve contributes no animation due to lack of keyframes or useful modifiers, and should be deleted

    :type: bool
    """

    is_valid: bool
    """ False when F-Curve could not be evaluated in past, so should be skipped when evaluating

    :type: bool
    """

    keyframe_points: FCurveKeyframePoints
    """ User-editable keyframes

    :type: FCurveKeyframePoints
    """

    lock: bool
    """ F-Curve's settings cannot be edited

    :type: bool
    """

    modifiers: FCurveModifiers
    """ Modifiers affecting the shape of the F-Curve

    :type: FCurveModifiers
    """

    mute: bool
    """ Disable F-Curve evaluation

    :type: bool
    """

    sampled_points: bpy_prop_collection[FCurveSample]
    """ Sampled animation data

    :type: bpy_prop_collection[FCurveSample]
    """

    select: bool
    """ F-Curve is selected for editing

    :type: bool
    """

    def evaluate(self, frame: float | None) -> float:
        """Evaluate F-Curve

        :param frame: Frame, Evaluate F-Curve at given frame
        :type frame: float | None
        :return: Value, Value of F-Curve specific frame
        :rtype: float
        """
        ...

    def update(self):
        """Ensure keyframes are sorted in chronological order and handles are set correctly"""
        ...

    def range(self) -> mathutils.Vector:
        """Get the time extents for F-Curve

        :return: Range, Min/Max values
        :rtype: mathutils.Vector
        """
        ...

    def update_autoflags(self, data: typing.Any):
        """Update FCurve flags set automatically from affected property (currently, integer/discrete flags set when the property is not a float)

        :param data: Data, Data containing the property controlled by given FCurve
        :type data: typing.Any
        """
        ...

    def convert_to_samples(self, start: int | None, end: int | None):
        """Convert current FCurve from keyframes to sample points, if necessary

        :param start: Start Frame
        :type start: int | None
        :param end: End Frame
        :type end: int | None
        """
        ...

    def convert_to_keyframes(self, start: int | None, end: int | None):
        """Convert current FCurve from sample points to keyframes (linear interpolation), if necessary

        :param start: Start Frame
        :type start: int | None
        :param end: End Frame
        :type end: int | None
        """
        ...

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
