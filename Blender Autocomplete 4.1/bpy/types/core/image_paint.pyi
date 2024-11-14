import typing
import collections.abc
import mathutils
from .struct import Struct
from .paint import Paint
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .image import Image

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ImagePaint(Paint, bpy_struct):
    """Properties of image and texture painting mode"""

    canvas: Image
    """ Image used as canvas

    :type: Image
    """

    clone_image: Image
    """ Image used as clone source

    :type: Image
    """

    dither: float
    """ Amount of dithering when painting on byte images

    :type: float
    """

    interpolation: str
    """ Texture filtering type

    :type: str
    """

    invert_stencil: bool
    """ Invert the stencil layer

    :type: bool
    """

    missing_materials: bool
    """ The mesh is missing materials

    :type: bool
    """

    missing_stencil: bool
    """ Image Painting does not have a stencil

    :type: bool
    """

    missing_texture: bool
    """ Image Painting does not have a texture to paint on

    :type: bool
    """

    missing_uvs: bool
    """ A UV layer is missing on the mesh

    :type: bool
    """

    mode: str
    """ Mode of operation for projection painting

    :type: str
    """

    normal_angle: int
    """ Paint most on faces pointing towards the view according to this angle

    :type: int
    """

    screen_grab_size: bpy_prop_array[int]
    """ Size to capture the image for re-projecting

    :type: bpy_prop_array[int]
    """

    seam_bleed: int
    """ Extend paint beyond the faces UVs to reduce seams (in pixels, slower)

    :type: int
    """

    stencil_color: mathutils.Color
    """ Stencil color in the viewport

    :type: mathutils.Color
    """

    stencil_image: Image
    """ Image used as stencil

    :type: Image
    """

    use_backface_culling: bool
    """ Ignore faces pointing away from the view (faster)

    :type: bool
    """

    use_clone_layer: bool
    """ Use another UV map as clone source, otherwise use the 3D cursor as the source

    :type: bool
    """

    use_normal_falloff: bool
    """ Paint most on faces pointing towards the view

    :type: bool
    """

    use_occlude: bool
    """ Only paint onto the faces directly under the brush (slower)

    :type: bool
    """

    use_stencil_layer: bool
    """ Set the mask layer from the UV map buttons

    :type: bool
    """

    def detect_data(self) -> bool:
        """Check if required texpaint data exist

        :return:
        :rtype: bool
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
