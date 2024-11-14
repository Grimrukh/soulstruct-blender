import typing
import collections.abc
import mathutils
from .struct import Struct
from .texture_slot import TextureSlot
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleSettingsTextureSlot(TextureSlot, bpy_struct):
    """Texture slot for textures in a Particle Settings data-block"""

    clump_factor: float
    """ Amount texture affects child clump

    :type: float
    """

    damp_factor: float
    """ Amount texture affects particle damping

    :type: float
    """

    density_factor: float
    """ Amount texture affects particle density

    :type: float
    """

    field_factor: float
    """ Amount texture affects particle force fields

    :type: float
    """

    gravity_factor: float
    """ Amount texture affects particle gravity

    :type: float
    """

    kink_amp_factor: float
    """ Amount texture affects child kink amplitude

    :type: float
    """

    kink_freq_factor: float
    """ Amount texture affects child kink frequency

    :type: float
    """

    length_factor: float
    """ Amount texture affects child hair length

    :type: float
    """

    life_factor: float
    """ Amount texture affects particle life time

    :type: float
    """

    mapping: str
    """ 

    :type: str
    """

    mapping_x: str
    """ 

    :type: str
    """

    mapping_y: str
    """ 

    :type: str
    """

    mapping_z: str
    """ 

    :type: str
    """

    object: Object
    """ Object to use for mapping with Object texture coordinates

    :type: Object
    """

    rough_factor: float
    """ Amount texture affects child roughness

    :type: float
    """

    size_factor: float
    """ Amount texture affects physical particle size

    :type: float
    """

    texture_coords: str
    """ Texture coordinates used to map the texture onto the background

    :type: str
    """

    time_factor: float
    """ Amount texture affects particle emission time

    :type: float
    """

    twist_factor: float
    """ Amount texture affects child twist

    :type: float
    """

    use_map_clump: bool
    """ Affect the child clumping

    :type: bool
    """

    use_map_damp: bool
    """ Affect the particle velocity damping

    :type: bool
    """

    use_map_density: bool
    """ Affect the density of the particles

    :type: bool
    """

    use_map_field: bool
    """ Affect the particle force fields

    :type: bool
    """

    use_map_gravity: bool
    """ Affect the particle gravity

    :type: bool
    """

    use_map_kink_amp: bool
    """ Affect the child kink amplitude

    :type: bool
    """

    use_map_kink_freq: bool
    """ Affect the child kink frequency

    :type: bool
    """

    use_map_length: bool
    """ Affect the child hair length

    :type: bool
    """

    use_map_life: bool
    """ Affect the life time of the particles

    :type: bool
    """

    use_map_rough: bool
    """ Affect the child rough

    :type: bool
    """

    use_map_size: bool
    """ Affect the particle size

    :type: bool
    """

    use_map_time: bool
    """ Affect the emission time of the particles

    :type: bool
    """

    use_map_twist: bool
    """ Affect the child twist

    :type: bool
    """

    use_map_velocity: bool
    """ Affect the particle initial velocity

    :type: bool
    """

    uv_layer: str
    """ UV map to use for mapping with UV texture coordinates

    :type: str
    """

    velocity_factor: float
    """ Amount texture affects particle initial velocity

    :type: float
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
