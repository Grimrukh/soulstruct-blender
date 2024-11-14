import typing
import collections.abc
import mathutils
from .struct import Struct
from .movie_tracking_markers import MovieTrackingMarkers
from .bpy_struct import bpy_struct
from .grease_pencil import GreasePencil

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingTrack(bpy_struct):
    """Match-moving track data for tracking"""

    average_error: float
    """ Average error of re-projection

    :type: float
    """

    bundle: mathutils.Vector
    """ Position of bundle reconstructed from this track

    :type: mathutils.Vector
    """

    color: mathutils.Color
    """ Color of the track in the Movie Clip Editor and the 3D viewport after a solve

    :type: mathutils.Color
    """

    correlation_min: float
    """ Minimal value of correlation between matched pattern and reference that is still treated as successful tracking

    :type: float
    """

    frames_limit: int
    """ Every tracking cycle, this number of frames are tracked

    :type: int
    """

    grease_pencil: GreasePencil
    """ Grease pencil data for this track

    :type: GreasePencil
    """

    has_bundle: bool
    """ True if track has a valid bundle

    :type: bool
    """

    hide: bool
    """ Track is hidden

    :type: bool
    """

    lock: bool
    """ Track is locked and all changes to it are disabled

    :type: bool
    """

    margin: int
    """ Distance from image boundary at which marker stops tracking

    :type: int
    """

    markers: MovieTrackingMarkers
    """ Collection of markers in track

    :type: MovieTrackingMarkers
    """

    motion_model: str
    """ Default motion model to use for tracking

    :type: str
    """

    name: str
    """ Unique name of track

    :type: str
    """

    offset: mathutils.Vector
    """ Offset of track from the parenting point

    :type: mathutils.Vector
    """

    pattern_match: str
    """ Track pattern from given frame when tracking marker to next frame

    :type: str
    """

    select: bool
    """ Track is selected

    :type: bool
    """

    select_anchor: bool
    """ Track's anchor point is selected

    :type: bool
    """

    select_pattern: bool
    """ Track's pattern area is selected

    :type: bool
    """

    select_search: bool
    """ Track's search area is selected

    :type: bool
    """

    use_alpha_preview: bool
    """ Apply track's mask on displaying preview

    :type: bool
    """

    use_blue_channel: bool
    """ Use blue channel from footage for tracking

    :type: bool
    """

    use_brute: bool
    """ Use a brute-force translation only pre-track before refinement

    :type: bool
    """

    use_custom_color: bool
    """ Use custom color instead of theme-defined

    :type: bool
    """

    use_grayscale_preview: bool
    """ Display what the tracking algorithm sees in the preview

    :type: bool
    """

    use_green_channel: bool
    """ Use green channel from footage for tracking

    :type: bool
    """

    use_mask: bool
    """ Use a grease pencil data-block as a mask to use only specified areas of pattern when tracking

    :type: bool
    """

    use_normalization: bool
    """ Normalize light intensities while tracking. Slower

    :type: bool
    """

    use_red_channel: bool
    """ Use red channel from footage for tracking

    :type: bool
    """

    weight: float
    """ Influence of this track on a final solution

    :type: float
    """

    weight_stab: float
    """ Influence of this track on 2D stabilization

    :type: float
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
