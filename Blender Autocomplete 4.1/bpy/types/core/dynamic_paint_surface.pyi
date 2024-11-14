import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .effector_weights import EffectorWeights
from .bpy_prop_array import bpy_prop_array
from .texture import Texture
from .point_cache import PointCache
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DynamicPaintSurface(bpy_struct):
    """A canvas surface layer"""

    brush_collection: Collection
    """ Only use brush objects from this collection

    :type: Collection
    """

    brush_influence_scale: float
    """ Adjust influence brush objects have on this surface

    :type: float
    """

    brush_radius_scale: float
    """ Adjust radius of proximity brushes or particles for this surface

    :type: float
    """

    color_dry_threshold: float
    """ The wetness level when colors start to shift to the background

    :type: float
    """

    color_spread_speed: float
    """ How fast colors get mixed within wet paint

    :type: float
    """

    depth_clamp: float
    """ Maximum level of depth intersection in object space (use 0.0 to disable)

    :type: float
    """

    displace_factor: float
    """ Strength of displace when applied to the mesh

    :type: float
    """

    displace_type: str
    """ 

    :type: str
    """

    dissolve_speed: int
    """ Approximately in how many frames should dissolve happen

    :type: int
    """

    drip_acceleration: float
    """ How much surface acceleration affects dripping

    :type: float
    """

    drip_velocity: float
    """ How much surface velocity affects dripping

    :type: float
    """

    dry_speed: int
    """ Approximately in how many frames should drying happen

    :type: int
    """

    effect_ui: str
    """ 

    :type: str
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    frame_end: int
    """ Simulation end frame

    :type: int
    """

    frame_start: int
    """ Simulation start frame

    :type: int
    """

    frame_substeps: int
    """ Do extra frames between scene frames to ensure smooth motion

    :type: int
    """

    image_fileformat: str
    """ 

    :type: str
    """

    image_output_path: str
    """ Directory to save the textures

    :type: str
    """

    image_resolution: int
    """ Output image resolution

    :type: int
    """

    init_color: bpy_prop_array[float]
    """ Initial color of the surface

    :type: bpy_prop_array[float]
    """

    init_color_type: str
    """ 

    :type: str
    """

    init_layername: str
    """ 

    :type: str
    """

    init_texture: Texture
    """ 

    :type: Texture
    """

    is_active: bool
    """ Toggle whether surface is processed or ignored

    :type: bool
    """

    is_cache_user: bool
    """ 

    :type: bool
    """

    name: str
    """ Surface name

    :type: str
    """

    output_name_a: str
    """ Name used to save output from this surface

    :type: str
    """

    output_name_b: str
    """ Name used to save output from this surface

    :type: str
    """

    point_cache: PointCache
    """ 

    :type: PointCache
    """

    shrink_speed: float
    """ How fast shrink effect moves on the canvas surface

    :type: float
    """

    spread_speed: float
    """ How fast spread effect moves on the canvas surface

    :type: float
    """

    surface_format: str
    """ Surface Format

    :type: str
    """

    surface_type: str
    """ Surface Type

    :type: str
    """

    use_antialiasing: bool
    """ Use 5× multisampling to smooth paint edges

    :type: bool
    """

    use_dissolve: bool
    """ Enable to make surface changes disappear over time

    :type: bool
    """

    use_dissolve_log: bool
    """ Use logarithmic dissolve (makes high values to fade faster than low values)

    :type: bool
    """

    use_drip: bool
    """ Process drip effect (drip wet paint to gravity direction)

    :type: bool
    """

    use_dry_log: bool
    """ Use logarithmic drying (makes high values to dry faster than low values)

    :type: bool
    """

    use_drying: bool
    """ Enable to make surface wetness dry over time

    :type: bool
    """

    use_incremental_displace: bool
    """ New displace is added cumulatively on top of existing

    :type: bool
    """

    use_output_a: bool
    """ Save this output layer

    :type: bool
    """

    use_output_b: bool
    """ Save this output layer

    :type: bool
    """

    use_premultiply: bool
    """ Multiply color by alpha (recommended for Blender input)

    :type: bool
    """

    use_shrink: bool
    """ Process shrink effect (shrink paint areas)

    :type: bool
    """

    use_spread: bool
    """ Process spread effect (spread wet paint around surface)

    :type: bool
    """

    use_wave_open_border: bool
    """ Pass waves through mesh edges

    :type: bool
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    wave_damping: float
    """ Wave damping factor

    :type: float
    """

    wave_smoothness: float
    """ Limit maximum steepness of wave slope between simulation points (use higher values for smoother waves at expense of reduced detail)

    :type: float
    """

    wave_speed: float
    """ Wave propagation speed

    :type: float
    """

    wave_spring: float
    """ Spring force that pulls water level back to zero

    :type: float
    """

    wave_timescale: float
    """ Wave time scaling factor

    :type: float
    """

    def output_exists(self, object: Object, index: int | None) -> bool:
        """Checks if surface output layer of given name exists

        :param object:
        :type object: Object
        :param index: Index
        :type index: int | None
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
