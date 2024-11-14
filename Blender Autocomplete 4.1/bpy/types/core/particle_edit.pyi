import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .particle_brush import ParticleBrush

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleEdit(bpy_struct):
    """Properties of particle editing mode"""

    brush: ParticleBrush
    """ 

    :type: ParticleBrush
    """

    default_key_count: int
    """ How many keys to make new particles with

    :type: int
    """

    display_step: int
    """ How many steps to display the path with

    :type: int
    """

    emitter_distance: float
    """ Distance to keep particles away from the emitter

    :type: float
    """

    fade_frames: int
    """ How many frames to fade

    :type: int
    """

    is_editable: bool
    """ A valid edit mode exists

    :type: bool
    """

    is_hair: bool
    """ Editing hair

    :type: bool
    """

    object: Object
    """ The edited object

    :type: Object
    """

    select_mode: str
    """ Particle select and display mode

    :type: str
    """

    shape_object: Object
    """ Outer shape to use for tools

    :type: Object
    """

    show_particles: bool
    """ Display actual particles

    :type: bool
    """

    tool: str
    """ 

    :type: str
    """

    type: str
    """ 

    :type: str
    """

    use_auto_velocity: bool
    """ Calculate point velocities automatically

    :type: bool
    """

    use_default_interpolate: bool
    """ Interpolate new particles from the existing ones

    :type: bool
    """

    use_emitter_deflect: bool
    """ Keep paths from intersecting the emitter

    :type: bool
    """

    use_fade_time: bool
    """ Fade paths and keys further away from current frame

    :type: bool
    """

    use_preserve_length: bool
    """ Keep path lengths constant

    :type: bool
    """

    use_preserve_root: bool
    """ Keep root keys unmodified

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
