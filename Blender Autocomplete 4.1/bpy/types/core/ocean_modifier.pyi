import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class OceanModifier(Modifier, bpy_struct):
    """Simulate an ocean surface"""

    bake_foam_fade: float
    """ How much foam accumulates over time (baked ocean only)

    :type: float
    """

    choppiness: float
    """ Choppiness of the wave's crest (adds some horizontal component to the displacement)

    :type: float
    """

    damping: float
    """ Damp reflected waves going in opposite direction to the wind

    :type: float
    """

    depth: float
    """ Depth of the solid ground below the water surface

    :type: float
    """

    fetch_jonswap: float
    """ This is the distance from a lee shore, called the fetch, or the distance over which the wind blows with constant velocity. Used by 'JONSWAP' and 'TMA' models

    :type: float
    """

    filepath: str
    """ Path to a folder to store external baked images

    :type: str
    """

    foam_coverage: float
    """ Amount of generated foam

    :type: float
    """

    foam_layer_name: str
    """ Name of the vertex color layer used for foam

    :type: str
    """

    frame_end: int
    """ End frame of the ocean baking

    :type: int
    """

    frame_start: int
    """ Start frame of the ocean baking

    :type: int
    """

    geometry_mode: str
    """ Method of modifying geometry

    :type: str
    """

    invert_spray: bool
    """ Invert the spray direction map

    :type: bool
    """

    is_cached: bool
    """ Whether the ocean is using cached data or simulating

    :type: bool
    """

    random_seed: int
    """ Seed of the random generator

    :type: int
    """

    repeat_x: int
    """ Repetitions of the generated surface in X

    :type: int
    """

    repeat_y: int
    """ Repetitions of the generated surface in Y

    :type: int
    """

    resolution: int
    """ Resolution of the generated surface for rendering and baking

    :type: int
    """

    sharpen_peak_jonswap: float
    """ Peak sharpening for 'JONSWAP' and 'TMA' models

    :type: float
    """

    size: float
    """ Surface scale factor (does not affect the height of the waves)

    :type: float
    """

    spatial_size: int
    """ Size of the simulation domain (in meters), and of the generated geometry (in BU)

    :type: int
    """

    spectrum: str
    """ Spectrum to use

    :type: str
    """

    spray_layer_name: str
    """ Name of the vertex color layer used for the spray direction map

    :type: str
    """

    time: float
    """ Current time of the simulation

    :type: float
    """

    use_foam: bool
    """ Generate foam mask as a vertex color channel

    :type: bool
    """

    use_normals: bool
    """ Output normals for bump mapping - disabling can speed up performance if it's not needed

    :type: bool
    """

    use_spray: bool
    """ Generate map of spray direction as a vertex color channel

    :type: bool
    """

    viewport_resolution: int
    """ Viewport resolution of the generated surface

    :type: int
    """

    wave_alignment: float
    """ How much the waves are aligned to each other

    :type: float
    """

    wave_direction: float
    """ Main direction of the waves when they are (partially) aligned

    :type: float
    """

    wave_scale: float
    """ Scale of the displacement effect

    :type: float
    """

    wave_scale_min: float
    """ Shortest allowed wavelength

    :type: float
    """

    wind_velocity: float
    """ Wind speed

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
