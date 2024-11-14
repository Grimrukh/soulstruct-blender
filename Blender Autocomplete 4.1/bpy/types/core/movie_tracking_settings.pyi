import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingSettings(bpy_struct):
    """Match moving settings"""

    clean_action: str
    """ Cleanup action to execute

    :type: str
    """

    clean_error: float
    """ Effect on tracks which have a larger re-projection error

    :type: float
    """

    clean_frames: int
    """ Effect on tracks which are tracked less than the specified amount of frames

    :type: int
    """

    default_correlation_min: float
    """ Default minimum value of correlation between matched pattern and reference that is still treated as successful tracking

    :type: float
    """

    default_frames_limit: int
    """ Every tracking cycle, this number of frames are tracked

    :type: int
    """

    default_margin: int
    """ Default distance from image boundary at which marker stops tracking

    :type: int
    """

    default_motion_model: str
    """ Default motion model to use for tracking

    :type: str
    """

    default_pattern_match: str
    """ Track pattern from given frame when tracking marker to next frame

    :type: str
    """

    default_pattern_size: int
    """ Size of pattern area for newly created tracks

    :type: int
    """

    default_search_size: int
    """ Size of search area for newly created tracks

    :type: int
    """

    default_weight: float
    """ Influence of newly created track on a final solution

    :type: float
    """

    distance: float
    """ Distance between two bundles used for scene scaling

    :type: float
    """

    object_distance: float
    """ Distance between two bundles used for object scaling

    :type: float
    """

    refine_intrinsics_focal_length: bool
    """ Refine focal length during camera solving

    :type: bool
    """

    refine_intrinsics_principal_point: bool
    """ Refine principal point during camera solving

    :type: bool
    """

    refine_intrinsics_radial_distortion: bool
    """ Refine radial coefficients of distortion model during camera solving

    :type: bool
    """

    refine_intrinsics_tangential_distortion: bool
    """ Refine tangential coefficients of distortion model during camera solving

    :type: bool
    """

    speed: str
    """ Limit speed of tracking to make visual feedback easier (this does not affect the tracking quality)

    :type: str
    """

    use_default_blue_channel: bool
    """ Use blue channel from footage for tracking

    :type: bool
    """

    use_default_brute: bool
    """ Use a brute-force translation-only initialization when tracking

    :type: bool
    """

    use_default_green_channel: bool
    """ Use green channel from footage for tracking

    :type: bool
    """

    use_default_mask: bool
    """ Use a grease pencil data-block as a mask to use only specified areas of pattern when tracking

    :type: bool
    """

    use_default_normalization: bool
    """ Normalize light intensities while tracking (slower)

    :type: bool
    """

    use_default_red_channel: bool
    """ Use red channel from footage for tracking

    :type: bool
    """

    use_keyframe_selection: bool
    """ Automatically select keyframes when solving camera/object motion

    :type: bool
    """

    use_tripod_solver: bool
    """ Use special solver to track a stable camera position, such as a tripod

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
