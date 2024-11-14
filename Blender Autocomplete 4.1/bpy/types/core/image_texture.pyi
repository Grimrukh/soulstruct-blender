import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .texture import Texture
from .image import Image
from .image_user import ImageUser

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ImageTexture(Texture, ID, bpy_struct):
    checker_distance: float
    """ Distance between checker tiles

    :type: float
    """

    crop_max_x: float
    """ Maximum X value to crop the image

    :type: float
    """

    crop_max_y: float
    """ Maximum Y value to crop the image

    :type: float
    """

    crop_min_x: float
    """ Minimum X value to crop the image

    :type: float
    """

    crop_min_y: float
    """ Minimum Y value to crop the image

    :type: float
    """

    extension: str
    """ How the image is extrapolated past its original bounds

    :type: str
    """

    filter_eccentricity: int
    """ Maximum eccentricity (higher gives less blur at distant/oblique angles, but is also slower)

    :type: int
    """

    filter_lightprobes: int
    """ Maximum number of samples (higher gives less blur at distant/oblique angles, but is also slower)

    :type: int
    """

    filter_size: float
    """ Multiply the filter size used by MIP Map and Interpolation

    :type: float
    """

    filter_type: str
    """ Texture filter to use for sampling image

    :type: str
    """

    image: Image
    """ 

    :type: Image
    """

    image_user: ImageUser
    """ Parameters defining which layer, pass and frame of the image is displayed

    :type: ImageUser
    """

    invert_alpha: bool
    """ Invert all the alpha values in the image

    :type: bool
    """

    repeat_x: int
    """ Repetition multiplier in the X direction

    :type: int
    """

    repeat_y: int
    """ Repetition multiplier in the Y direction

    :type: int
    """

    use_alpha: bool
    """ Use the alpha channel information in the image

    :type: bool
    """

    use_calculate_alpha: bool
    """ Calculate an alpha channel based on RGB values in the image

    :type: bool
    """

    use_checker_even: bool
    """ Even checker tiles

    :type: bool
    """

    use_checker_odd: bool
    """ Odd checker tiles

    :type: bool
    """

    use_filter_size_min: bool
    """ Use Filter Size as a minimal filter value in pixels

    :type: bool
    """

    use_flip_axis: bool
    """ Flip the texture's X and Y axis

    :type: bool
    """

    use_interpolation: bool
    """ Interpolate pixels using selected filter

    :type: bool
    """

    use_mipmap: bool
    """ Use auto-generated MIP maps for the image

    :type: bool
    """

    use_mipmap_gauss: bool
    """ Use Gauss filter to sample down MIP maps

    :type: bool
    """

    use_mirror_x: bool
    """ Mirror the image repetition on the X direction

    :type: bool
    """

    use_mirror_y: bool
    """ Mirror the image repetition on the Y direction

    :type: bool
    """

    use_normal_map: bool
    """ Use image RGB values for normal mapping

    :type: bool
    """

    users_material: typing.Any
    """ Materials that use this texture(readonly)"""

    users_object_modifier: typing.Any
    """ Object modifiers that use this texture(readonly)"""

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
