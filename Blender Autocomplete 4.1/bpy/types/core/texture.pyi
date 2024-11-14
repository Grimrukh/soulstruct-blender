import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID
from .color_ramp import ColorRamp
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Texture(ID, bpy_struct):
    """Texture data-block used by materials, lights, worlds and brushes"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    color_ramp: ColorRamp
    """ 

    :type: ColorRamp
    """

    contrast: float
    """ Adjust the contrast of the texture

    :type: float
    """

    factor_blue: float
    """ 

    :type: float
    """

    factor_green: float
    """ 

    :type: float
    """

    factor_red: float
    """ 

    :type: float
    """

    intensity: float
    """ Adjust the brightness of the texture

    :type: float
    """

    node_tree: NodeTree
    """ Node tree for node-based textures

    :type: NodeTree
    """

    saturation: float
    """ Adjust the saturation of colors in the texture

    :type: float
    """

    type: str
    """ 

    :type: str
    """

    use_clamp: bool
    """ Set negative texture RGB and intensity values to zero, for some uses like displacement this option can be disabled to get the full range

    :type: bool
    """

    use_color_ramp: bool
    """ Map the texture intensity to the color ramp. Note that the alpha value is used for image textures, enable "Calculate Alpha" for images without an alpha channel

    :type: bool
    """

    use_nodes: bool
    """ Make this a node-based texture

    :type: bool
    """

    use_preview_alpha: bool
    """ Show Alpha in Preview Render

    :type: bool
    """

    users_material: typing.Any
    """ Materials that use this texture(readonly)"""

    users_object_modifier: typing.Any
    """ Object modifiers that use this texture(readonly)"""

    def evaluate(
        self, value: collections.abc.Sequence[float] | mathutils.Vector | None
    ) -> mathutils.Vector:
        """Evaluate the texture at the a given coordinate and returns the result

        :param value: The coordinates (x,y,z) of the texture, in case of a 3D texture, the z value is the slice of the texture that is evaluated. For 2D textures such as images, the z value is ignored
        :type value: collections.abc.Sequence[float] | mathutils.Vector | None
        :return: The result of the texture where (x,y,z,w) are (red, green, blue, intensity). For grayscale textures, often intensity only will be used
        :rtype: mathutils.Vector
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
