import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .texture import Texture
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WaveModifier(Modifier, bpy_struct):
    """Wave effect modifier"""

    damping_time: float
    """ Number of frames in which the wave damps out after it dies

    :type: float
    """

    falloff_radius: float
    """ Distance after which it fades out

    :type: float
    """

    height: float
    """ Height of the wave

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    lifetime: float
    """ Lifetime of the wave in frames, zero means infinite

    :type: float
    """

    narrowness: float
    """ Distance between the top and the base of a wave, the higher the value, the more narrow the wave

    :type: float
    """

    speed: float
    """ Speed of the wave, towards the starting point when negative

    :type: float
    """

    start_position_object: Object
    """ Object which defines the wave center

    :type: Object
    """

    start_position_x: float
    """ X coordinate of the start position

    :type: float
    """

    start_position_y: float
    """ Y coordinate of the start position

    :type: float
    """

    texture: Texture
    """ 

    :type: Texture
    """

    texture_coords: str
    """ 

    :type: str
    """

    texture_coords_bone: str
    """ Bone to set the texture coordinates

    :type: str
    """

    texture_coords_object: Object
    """ Object to set the texture coordinates

    :type: Object
    """

    time_offset: float
    """ Either the starting frame (for positive speed) or ending frame (for negative speed)

    :type: float
    """

    use_cyclic: bool
    """ Cyclic wave effect

    :type: bool
    """

    use_normal: bool
    """ Displace along normals

    :type: bool
    """

    use_normal_x: bool
    """ Enable displacement along the X normal

    :type: bool
    """

    use_normal_y: bool
    """ Enable displacement along the Y normal

    :type: bool
    """

    use_normal_z: bool
    """ Enable displacement along the Z normal

    :type: bool
    """

    use_x: bool
    """ X axis motion

    :type: bool
    """

    use_y: bool
    """ Y axis motion

    :type: bool
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    vertex_group: str
    """ Vertex group name for modulating the wave

    :type: str
    """

    width: float
    """ Distance between the waves

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
