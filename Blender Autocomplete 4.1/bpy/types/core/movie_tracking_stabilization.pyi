import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_track import MovieTrackingTrack

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingStabilization(bpy_struct):
    """2D stabilization based on tracking markers"""

    active_rotation_track_index: int | None
    """ Index of active track in rotation stabilization tracks list

    :type: int | None
    """

    active_track_index: int | None
    """ Index of active track in translation stabilization tracks list

    :type: int | None
    """

    anchor_frame: int
    """ Reference point to anchor stabilization (other frames will be adjusted relative to this frame's position)

    :type: int
    """

    filter_type: str
    """ Interpolation to use for sub-pixel shifts and rotations due to stabilization

    :type: str
    """

    influence_location: float
    """ Influence of stabilization algorithm on footage location

    :type: float
    """

    influence_rotation: float
    """ Influence of stabilization algorithm on footage rotation

    :type: float
    """

    influence_scale: float
    """ Influence of stabilization algorithm on footage scale

    :type: float
    """

    rotation_tracks: bpy_prop_collection[MovieTrackingTrack]
    """ Collection of tracks used for 2D stabilization (translation)

    :type: bpy_prop_collection[MovieTrackingTrack]
    """

    scale_max: float
    """ Limit the amount of automatic scaling

    :type: float
    """

    show_tracks_expanded: bool
    """ Show UI list of tracks participating in stabilization

    :type: bool
    """

    target_position: mathutils.Vector
    """ Known relative offset of original shot, will be subtracted (e.g. for panning shot, can be animated)

    :type: mathutils.Vector
    """

    target_rotation: float
    """ Rotation present on original shot, will be compensated (e.g. for deliberate tilting)

    :type: float
    """

    target_scale: float
    """ Explicitly scale resulting frame to compensate zoom of original shot

    :type: float
    """

    tracks: bpy_prop_collection[MovieTrackingTrack]
    """ Collection of tracks used for 2D stabilization (translation)

    :type: bpy_prop_collection[MovieTrackingTrack]
    """

    use_2d_stabilization: bool
    """ Use 2D stabilization for footage

    :type: bool
    """

    use_autoscale: bool
    """ Automatically scale footage to cover unfilled areas when stabilizing

    :type: bool
    """

    use_stabilize_rotation: bool
    """ Stabilize detected rotation around center of frame

    :type: bool
    """

    use_stabilize_scale: bool
    """ Compensate any scale changes relative to center of rotation

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
