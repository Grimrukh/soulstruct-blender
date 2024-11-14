import typing
import collections.abc
import mathutils
from .image_format_settings import ImageFormatSettings
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BakeSettings(bpy_struct):
    """Bake data for a Scene data-block"""

    cage_extrusion: float
    """ Inflate the active object by the specified distance for baking. This helps matching to points nearer to the outside of the selected object meshes

    :type: float
    """

    cage_object: Object
    """ Object to use as cage instead of calculating the cage from the active object with cage extrusion

    :type: Object
    """

    filepath: str
    """ Image filepath to use when saving externally

    :type: str
    """

    height: int
    """ Vertical dimension of the baking map

    :type: int
    """

    image_settings: ImageFormatSettings
    """ 

    :type: ImageFormatSettings
    """

    margin: int
    """ Extends the baked result as a post process filter

    :type: int
    """

    margin_type: str
    """ Algorithm to extend the baked result

    :type: str
    """

    max_ray_distance: float
    """ The maximum ray distance for matching points between the active and selected objects. If zero, there is no limit

    :type: float
    """

    normal_b: str
    """ Axis to bake in blue channel

    :type: str
    """

    normal_g: str
    """ Axis to bake in green channel

    :type: str
    """

    normal_r: str
    """ Axis to bake in red channel

    :type: str
    """

    normal_space: str
    """ Choose normal space for baking

    :type: str
    """

    pass_filter: typing.Any
    """ Passes to include in the active baking pass

    :type: typing.Any
    """

    save_mode: str
    """ Where to save baked image textures

    :type: str
    """

    target: str
    """ Where to output the baked map

    :type: str
    """

    use_automatic_name: bool
    """ Automatically name the output file with the pass type (external only)

    :type: bool
    """

    use_cage: bool
    """ Cast rays to active object from a cage

    :type: bool
    """

    use_clear: bool
    """ Clear Images before baking (internal only)

    :type: bool
    """

    use_pass_color: bool
    """ Color the pass

    :type: bool
    """

    use_pass_diffuse: bool
    """ Add diffuse contribution

    :type: bool
    """

    use_pass_direct: bool
    """ Add direct lighting contribution

    :type: bool
    """

    use_pass_emit: bool
    """ Add emission contribution

    :type: bool
    """

    use_pass_glossy: bool
    """ Add glossy contribution

    :type: bool
    """

    use_pass_indirect: bool
    """ Add indirect lighting contribution

    :type: bool
    """

    use_pass_transmission: bool
    """ Add transmission contribution

    :type: bool
    """

    use_selected_to_active: bool
    """ Bake shading on the surface of selected objects to the active object

    :type: bool
    """

    use_split_materials: bool
    """ Split external images per material (external only)

    :type: bool
    """

    view_from: str
    """ Source of reflection ray directions

    :type: str
    """

    width: int
    """ Horizontal dimension of the baking map

    :type: int
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
