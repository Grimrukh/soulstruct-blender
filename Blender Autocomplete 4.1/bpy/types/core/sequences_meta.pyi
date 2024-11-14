import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .mask import Mask
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .movie_clip import MovieClip
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequencesMeta(bpy_prop_collection[Sequence], bpy_struct):
    """Collection of Sequences"""

    def new_clip(
        self,
        name: str | typing.Any,
        clip: MovieClip,
        channel: int | None,
        frame_start: int | None,
    ) -> Sequence:
        """Add a new movie clip sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param clip: Movie clip to add
        :type clip: MovieClip
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def new_mask(
        self,
        name: str | typing.Any,
        mask: Mask,
        channel: int | None,
        frame_start: int | None,
    ) -> Sequence:
        """Add a new mask sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param mask: Mask to add
        :type mask: Mask
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def new_scene(
        self,
        name: str | typing.Any,
        scene: Scene,
        channel: int | None,
        frame_start: int | None,
    ) -> Sequence:
        """Add a new scene sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param scene: Scene to add
        :type scene: Scene
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def new_image(
        self,
        name: str | typing.Any,
        filepath: str | typing.Any,
        channel: int | None,
        frame_start: int | None,
        fit_method: str | None = "ORIGINAL",
    ) -> Sequence:
        """Add a new image sequence

                :param name: Name for the new sequence
                :type name: str | typing.Any
                :param filepath: Filepath to image
                :type filepath: str | typing.Any
                :param channel: Channel, The channel for the new sequence
                :type channel: int | None
                :param frame_start: The start frame for the new sequence
                :type frame_start: int | None
                :param fit_method: Image Fit Method

        FIT
        Scale to Fit -- Scale image so fits in preview.

        FILL
        Scale to Fill -- Scale image so it fills preview completely.

        STRETCH
        Stretch to Fill -- Stretch image so it fills preview.

        ORIGINAL
        Use Original Size -- Don't scale the image.
                :type fit_method: str | None
                :return: New Sequence
                :rtype: Sequence
        """
        ...

    def new_movie(
        self,
        name: str | typing.Any,
        filepath: str | typing.Any,
        channel: int | None,
        frame_start: int | None,
        fit_method: str | None = "ORIGINAL",
    ) -> Sequence:
        """Add a new movie sequence

                :param name: Name for the new sequence
                :type name: str | typing.Any
                :param filepath: Filepath to movie
                :type filepath: str | typing.Any
                :param channel: Channel, The channel for the new sequence
                :type channel: int | None
                :param frame_start: The start frame for the new sequence
                :type frame_start: int | None
                :param fit_method: Image Fit Method

        FIT
        Scale to Fit -- Scale image so fits in preview.

        FILL
        Scale to Fill -- Scale image so it fills preview completely.

        STRETCH
        Stretch to Fill -- Stretch image so it fills preview.

        ORIGINAL
        Use Original Size -- Don't scale the image.
                :type fit_method: str | None
                :return: New Sequence
                :rtype: Sequence
        """
        ...

    def new_sound(
        self,
        name: str | typing.Any,
        filepath: str | typing.Any,
        channel: int | None,
        frame_start: int | None,
    ) -> Sequence:
        """Add a new sound sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param filepath: Filepath to movie
        :type filepath: str | typing.Any
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def new_meta(
        self, name: str | typing.Any, channel: int | None, frame_start: int | None
    ) -> Sequence:
        """Add a new meta sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def new_effect(
        self,
        name: str | typing.Any,
        type: str | None,
        channel: int | None,
        frame_start: int | None,
        frame_end: typing.Any | None = 0,
        seq1: Sequence | None = None,
        seq2: Sequence | None = None,
        seq3: Sequence | None = None,
    ) -> Sequence:
        """Add a new effect sequence

        :param name: Name for the new sequence
        :type name: str | typing.Any
        :param type: Type, type for the new sequence
        :type type: str | None
        :param channel: Channel, The channel for the new sequence
        :type channel: int | None
        :param frame_start: The start frame for the new sequence
        :type frame_start: int | None
        :param frame_end: The end frame for the new sequence
        :type frame_end: typing.Any | None
        :param seq1: Sequence 1 for effect
        :type seq1: Sequence | None
        :param seq2: Sequence 2 for effect
        :type seq2: Sequence | None
        :param seq3: Sequence 3 for effect
        :type seq3: Sequence | None
        :return: New Sequence
        :rtype: Sequence
        """
        ...

    def remove(self, sequence: Sequence):
        """Remove a Sequence

        :param sequence: Sequence to remove
        :type sequence: Sequence
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
