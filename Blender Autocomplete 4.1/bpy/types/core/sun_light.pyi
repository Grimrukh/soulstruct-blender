import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .light import Light

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SunLight(Light, ID, bpy_struct):
    """Constant direction parallel ray Light"""

    angle: float
    """ Angular diameter of the Sun as seen from the Earth

    :type: float
    """

    contact_shadow_bias: float
    """ Bias to avoid self shadowing

    :type: float
    """

    contact_shadow_distance: float
    """ World space distance in which to search for screen space occluder

    :type: float
    """

    contact_shadow_thickness: float
    """ Pixel thickness used to detect occlusion

    :type: float
    """

    energy: float
    """ Sunlight strength in watts per meter squared (W/m²)

    :type: float
    """

    shadow_buffer_bias: float
    """ Bias for reducing self shadowing

    :type: float
    """

    shadow_buffer_clip_start: float
    """ Shadow map clip start, below which objects will not generate shadows

    :type: float
    """

    shadow_cascade_count: int
    """ Number of texture used by the cascaded shadow map

    :type: int
    """

    shadow_cascade_exponent: float
    """ Higher value increase resolution towards the viewpoint

    :type: float
    """

    shadow_cascade_fade: float
    """ How smooth is the transition between each cascade

    :type: float
    """

    shadow_cascade_max_distance: float
    """ End distance of the cascaded shadow map (only in perspective view)

    :type: float
    """

    shadow_color: mathutils.Color
    """ Color of shadows cast by the light

    :type: mathutils.Color
    """

    shadow_soft_size: float
    """ Light size for ray shadow sampling (Raytraced shadows)

    :type: float
    """

    shadow_softness_factor: float
    """ Scale light shape for smaller penumbra

    :type: float
    """

    shadow_trace_distance: float
    """ Maximum distance a shadow map tracing ray can travel

    :type: float
    """

    use_contact_shadow: bool
    """ Use screen space ray-tracing to have correct shadowing near occluder, or for small features that does not appear in shadow maps

    :type: bool
    """

    use_shadow: bool
    """ 

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
