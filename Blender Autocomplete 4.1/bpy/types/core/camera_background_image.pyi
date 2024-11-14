import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .image import Image
from .movie_clip_user import MovieClipUser
from .movie_clip import MovieClip
from .image_user import ImageUser

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CameraBackgroundImage(bpy_struct):
    """Image and settings for display in the 3D View background"""

    alpha: float
    """ Image opacity to blend the image against the background color

    :type: float
    """

    clip: MovieClip
    """ Movie clip displayed and edited in this space

    :type: MovieClip
    """

    clip_user: MovieClipUser
    """ Parameters defining which frame of the movie clip is displayed

    :type: MovieClipUser
    """

    display_depth: str
    """ Display under or over everything

    :type: str
    """

    frame_method: str
    """ How the image fits in the camera frame

    :type: str
    """

    image: Image
    """ Image displayed and edited in this space

    :type: Image
    """

    image_user: ImageUser
    """ Parameters defining which layer, pass and frame of the image is displayed

    :type: ImageUser
    """

    is_override_data: bool
    """ In a local override camera, whether this background image comes from the linked reference camera, or is local to the override

    :type: bool
    """

    offset: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    rotation: float
    """ Rotation for the background image (ortho view only)

    :type: float
    """

    scale: float
    """ Scale the background image

    :type: float
    """

    show_background_image: bool
    """ Show this image as background

    :type: bool
    """

    show_expanded: bool
    """ Show the details in the user interface

    :type: bool
    """

    show_on_foreground: bool
    """ Show this image in front of objects in viewport

    :type: bool
    """

    source: str
    """ Data source used for background

    :type: str
    """

    use_camera_clip: bool
    """ Use movie clip from active scene camera

    :type: bool
    """

    use_flip_x: bool
    """ Flip the background image horizontally

    :type: bool
    """

    use_flip_y: bool
    """ Flip the background image vertically

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
