import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FieldSettings(bpy_struct):
    """Field settings for an object in physics simulation"""

    apply_to_location: bool
    """ Affect particle's location

    :type: bool
    """

    apply_to_rotation: bool
    """ Affect particle's dynamic rotation

    :type: bool
    """

    distance_max: float
    """ Maximum distance for the field to work

    :type: float
    """

    distance_min: float
    """ Minimum distance for the field's falloff

    :type: float
    """

    falloff_power: float
    """ How quickly strength falls off with distance from the force field

    :type: float
    """

    falloff_type: str
    """ 

    :type: str
    """

    flow: float
    """ Convert effector force into air flow velocity

    :type: float
    """

    guide_clump_amount: float
    """ Amount of clumping

    :type: float
    """

    guide_clump_shape: float
    """ Shape of clumping

    :type: float
    """

    guide_free: float
    """ Guide-free time from particle life's end

    :type: float
    """

    guide_kink_amplitude: float
    """ The amplitude of the offset

    :type: float
    """

    guide_kink_axis: str
    """ Which axis to use for offset

    :type: str
    """

    guide_kink_frequency: float
    """ The frequency of the offset (1/total length)

    :type: float
    """

    guide_kink_shape: float
    """ Adjust the offset to the beginning/end

    :type: float
    """

    guide_kink_type: str
    """ Type of periodic offset on the curve

    :type: str
    """

    guide_minimum: float
    """ The distance from which particles are affected fully

    :type: float
    """

    harmonic_damping: float
    """ Damping of the harmonic force

    :type: float
    """

    inflow: float
    """ Inwards component of the vortex force

    :type: float
    """

    linear_drag: float
    """ Drag component proportional to velocity

    :type: float
    """

    noise: float
    """ Amount of noise for the force strength

    :type: float
    """

    quadratic_drag: float
    """ Drag component proportional to the square of velocity

    :type: float
    """

    radial_falloff: float
    """ Radial falloff power (real gravitational falloff = 2)

    :type: float
    """

    radial_max: float
    """ Maximum radial distance for the field to work

    :type: float
    """

    radial_min: float
    """ Minimum radial distance for the field's falloff

    :type: float
    """

    rest_length: float
    """ Rest length of the harmonic force

    :type: float
    """

    seed: int
    """ Seed of the noise

    :type: int
    """

    shape: str
    """ Which direction is used to calculate the effector force

    :type: str
    """

    size: float
    """ Size of the turbulence

    :type: float
    """

    source_object: Object
    """ Select domain object of the smoke simulation

    :type: Object
    """

    strength: float
    """ Strength of force field

    :type: float
    """

    texture: Texture
    """ Texture to use as force

    :type: Texture
    """

    texture_mode: str
    """ How the texture effect is calculated (RGB and Curl need a RGB texture, else Gradient will be used instead)

    :type: str
    """

    texture_nabla: float
    """ Defines size of derivative offset used for calculating gradient and curl

    :type: float
    """

    type: str
    """ Type of field

    :type: str
    """

    use_2d_force: bool
    """ Apply force only in 2D

    :type: bool
    """

    use_absorption: bool
    """ Force gets absorbed by collision objects

    :type: bool
    """

    use_global_coords: bool
    """ Use effector/global coordinates for turbulence

    :type: bool
    """

    use_gravity_falloff: bool
    """ Multiply force by 1/distance²

    :type: bool
    """

    use_guide_path_add: bool
    """ Based on distance/falloff it adds a portion of the entire path

    :type: bool
    """

    use_guide_path_weight: bool
    """ Use curve weights to influence the particle influence along the curve

    :type: bool
    """

    use_max_distance: bool
    """ Use a maximum distance for the field to work

    :type: bool
    """

    use_min_distance: bool
    """ Use a minimum distance for the field's falloff

    :type: bool
    """

    use_multiple_springs: bool
    """ Every point is affected by multiple springs

    :type: bool
    """

    use_object_coords: bool
    """ Use object/global coordinates for texture

    :type: bool
    """

    use_radial_max: bool
    """ Use a maximum radial distance for the field to work

    :type: bool
    """

    use_radial_min: bool
    """ Use a minimum radial distance for the field's falloff

    :type: bool
    """

    use_root_coords: bool
    """ Texture coordinates from root particle locations

    :type: bool
    """

    use_smoke_density: bool
    """ Adjust force strength based on smoke density

    :type: bool
    """

    wind_factor: float
    """ How much the force is reduced when acting parallel to a surface, e.g. cloth

    :type: float
    """

    z_direction: str
    """ Effect in full or only positive/negative Z direction

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
