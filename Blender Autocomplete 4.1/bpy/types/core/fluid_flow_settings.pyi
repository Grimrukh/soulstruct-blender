import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .particle_system import ParticleSystem
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FluidFlowSettings(bpy_struct):
    """Fluid flow settings"""

    density: float
    """ 

    :type: float
    """

    density_vertex_group: str
    """ Name of vertex group which determines surface emission rate

    :type: str
    """

    flow_behavior: str
    """ Change flow behavior in the simulation

    :type: str
    """

    flow_source: str
    """ Change how fluid is emitted

    :type: str
    """

    flow_type: str
    """ Change type of fluid in the simulation

    :type: str
    """

    fuel_amount: float
    """ 

    :type: float
    """

    noise_texture: Texture
    """ Texture that controls emission strength

    :type: Texture
    """

    particle_size: float
    """ Particle size in simulation cells

    :type: float
    """

    particle_system: ParticleSystem
    """ Particle systems emitted from the object

    :type: ParticleSystem
    """

    smoke_color: mathutils.Color
    """ Color of smoke

    :type: mathutils.Color
    """

    subframes: int
    """ Number of additional samples to take between frames to improve quality of fast moving flows

    :type: int
    """

    surface_distance: float
    """ Controls fluid emission from the mesh surface (higher value results in emission further away from the mesh surface

    :type: float
    """

    temperature: float
    """ Temperature difference to ambient temperature

    :type: float
    """

    texture_map_type: str
    """ Texture mapping type

    :type: str
    """

    texture_offset: float
    """ Z-offset of texture mapping

    :type: float
    """

    texture_size: float
    """ Size of texture mapping

    :type: float
    """

    use_absolute: bool
    """ Only allow given density value in emitter area and will not add up

    :type: bool
    """

    use_inflow: bool
    """ Control when to apply fluid flow

    :type: bool
    """

    use_initial_velocity: bool
    """ Fluid has some initial velocity when it is emitted

    :type: bool
    """

    use_particle_size: bool
    """ Set particle size in simulation cells or use nearest cell

    :type: bool
    """

    use_plane_init: bool
    """ Treat this object as a planar and unclosed mesh. Fluid will only be emitted from the mesh surface and based on the surface emission value

    :type: bool
    """

    use_texture: bool
    """ Use a texture to control emission strength

    :type: bool
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    velocity_coord: mathutils.Vector
    """ Additional initial velocity in X, Y and Z direction (added to source velocity)

    :type: mathutils.Vector
    """

    velocity_factor: float
    """ Multiplier of source velocity passed to fluid (source velocity is non-zero only if object is moving)

    :type: float
    """

    velocity_normal: float
    """ Amount of normal directional velocity

    :type: float
    """

    velocity_random: float
    """ Amount of random velocity

    :type: float
    """

    volume_density: float
    """ Controls fluid emission from within the mesh (higher value results in greater emissions from inside the mesh)

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
