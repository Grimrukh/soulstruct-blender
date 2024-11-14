import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .sequence_timeline_channel import SequenceTimelineChannel
from .sequences_top_level import SequencesTopLevel

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceEditor(bpy_struct):
    """Sequence editing data for a Scene data-block"""

    active_strip: Sequence | None
    """ Sequencer's active strip

    :type: Sequence | None
    """

    channels: bpy_prop_collection[SequenceTimelineChannel]
    """ 

    :type: bpy_prop_collection[SequenceTimelineChannel]
    """

    meta_stack: bpy_prop_collection[Sequence]
    """ Meta strip stack, last is currently edited meta strip

    :type: bpy_prop_collection[Sequence]
    """

    overlay_frame: int
    """ Number of frames to offset

    :type: int
    """

    proxy_dir: str
    """ 

    :type: str
    """

    proxy_storage: str
    """ How to store proxies for this project

    :type: str
    """

    selected_retiming_keys: bool
    """ 

    :type: bool
    """

    sequences: SequencesTopLevel
    """ Top-level strips only

    :type: SequencesTopLevel
    """

    sequences_all: bpy_prop_collection[Sequence]
    """ All strips, recursively including those inside metastrips

    :type: bpy_prop_collection[Sequence]
    """

    show_cache: bool
    """ Visualize cached images on the timeline

    :type: bool
    """

    show_cache_composite: bool
    """ Visualize cached composite images

    :type: bool
    """

    show_cache_final_out: bool
    """ Visualize cached complete frames

    :type: bool
    """

    show_cache_preprocessed: bool
    """ Visualize cached pre-processed images

    :type: bool
    """

    show_cache_raw: bool
    """ Visualize cached raw images

    :type: bool
    """

    show_overlay_frame: bool
    """ Partial overlay on top of the sequencer with a frame offset

    :type: bool
    """

    use_cache_composite: bool
    """ Cache intermediate composited images, for faster tweaking of stacked strips at the cost of memory usage

    :type: bool
    """

    use_cache_final: bool
    """ Cache final image for each frame

    :type: bool
    """

    use_cache_preprocessed: bool
    """ Cache preprocessed images, for faster tweaking of effects at the cost of memory usage

    :type: bool
    """

    use_cache_raw: bool
    """ Cache raw images read from disk, for faster tweaking of strip parameters at the cost of memory usage

    :type: bool
    """

    use_overlay_frame_lock: bool
    """ 

    :type: bool
    """

    use_prefetch: bool
    """ Render frames ahead of current frame in the background for faster playback

    :type: bool
    """

    def display_stack(self, meta_sequence: Sequence | None):
        """Display sequences stack

        :param meta_sequence: Meta Sequence, Meta to display its stack
        :type meta_sequence: Sequence | None
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
