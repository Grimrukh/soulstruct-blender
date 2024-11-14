import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .particle_system import ParticleSystem
from .color_ramp import ColorRamp

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DynamicPaintBrushSettings(bpy_struct):
    """Brush settings"""

    invert_proximity: bool
    """ Proximity falloff is applied inside the volume

    :type: bool
    """

    paint_alpha: float
    """ Paint alpha

    :type: float
    """

    paint_color: mathutils.Color
    """ Color of the paint

    :type: mathutils.Color
    """

    paint_distance: float
    """ Maximum distance from brush to mesh surface to affect paint

    :type: float
    """

    paint_ramp: ColorRamp
    """ Color ramp used to define proximity falloff

    :type: ColorRamp
    """

    paint_source: str
    """ 

    :type: str
    """

    paint_wetness: float
    """ Paint wetness, visible in wetmap (some effects only affect wet paint)

    :type: float
    """

    particle_system: ParticleSystem
    """ The particle system to paint with

    :type: ParticleSystem
    """

    proximity_falloff: str
    """ Proximity falloff type

    :type: str
    """

    ray_direction: str
    """ Ray direction to use for projection (if brush object is located in that direction it's painted)

    :type: str
    """

    smooth_radius: float
    """ Smooth falloff added after solid radius

    :type: float
    """

    smudge_strength: float
    """ Smudge effect strength

    :type: float
    """

    solid_radius: float
    """ Radius that will be painted solid

    :type: float
    """

    use_absolute_alpha: bool
    """ Only increase alpha value if paint alpha is higher than existing

    :type: bool
    """

    use_negative_volume: bool
    """ Negate influence inside the volume

    :type: bool
    """

    use_paint_erase: bool
    """ Erase / remove paint instead of adding it

    :type: bool
    """

    use_particle_radius: bool
    """ Use radius from particle settings

    :type: bool
    """

    use_proximity_project: bool
    """ Brush is projected to canvas from defined direction within brush proximity

    :type: bool
    """

    use_proximity_ramp_alpha: bool
    """ Only read color ramp alpha

    :type: bool
    """

    use_smudge: bool
    """ Make this brush to smudge existing paint as it moves

    :type: bool
    """

    use_velocity_alpha: bool
    """ Multiply brush influence by velocity color ramp alpha

    :type: bool
    """

    use_velocity_color: bool
    """ Replace brush color by velocity color ramp

    :type: bool
    """

    use_velocity_depth: bool
    """ Multiply brush intersection depth (displace, waves) by velocity ramp alpha

    :type: bool
    """

    velocity_max: float
    """ Velocity considered as maximum influence (Blender units per frame)

    :type: float
    """

    velocity_ramp: ColorRamp
    """ Color ramp used to define brush velocity effect

    :type: ColorRamp
    """

    wave_clamp: float
    """ Maximum level of surface intersection used to influence waves (use 0.0 to disable)

    :type: float
    """

    wave_factor: float
    """ Multiplier for wave influence of this brush

    :type: float
    """

    wave_type: str
    """ 

    :type: str
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
