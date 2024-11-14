import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LightProbe(ID, bpy_struct):
    """Light Probe data-block for lighting capture objects"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    clip_end: float
    """ Probe clip end, beyond which objects will not appear in reflections

    :type: float
    """

    clip_start: float
    """ Probe clip start, below which objects will not appear in reflections

    :type: float
    """

    data_display_size: float
    """ Viewport display size of the sampled data

    :type: float
    """

    falloff: float
    """ Control how fast the probe influence decreases

    :type: float
    """

    grid_bake_samples: int
    """ Number of ray directions to evaluate when baking

    :type: int
    """

    grid_capture_emission: bool
    """ Bake emissive surfaces for more accurate lighting

    :type: bool
    """

    grid_capture_indirect: bool
    """ Bake light bounces from light sources for more accurate lighting

    :type: bool
    """

    grid_capture_world: bool
    """ Bake incoming light from the world, instead of just the visibility, for more accurate lighting, but lose correct blending to surrounding irradiance volumes

    :type: bool
    """

    grid_clamp_direct: float
    """ Clamp the direct lighting intensity to reduce noise (0 to disable)

    :type: float
    """

    grid_clamp_indirect: float
    """ Clamp the indirect lighting intensity to reduce noise (0 to disable)

    :type: float
    """

    grid_dilation_radius: float
    """ Radius in grid sample to search valid grid samples to copy into invalid grid samples

    :type: float
    """

    grid_dilation_threshold: float
    """ Ratio of front-facing surface hits under which a grid sample will reuse neighbors grid sample lighting

    :type: float
    """

    grid_escape_bias: float
    """ Moves capture points outside objects

    :type: float
    """

    grid_irradiance_smoothing: float
    """ Smoother irradiance interpolation but introduce light bleeding

    :type: float
    """

    grid_normal_bias: float
    """ Offset sampling of the irradiance grid in the surface normal direction to reduce light bleeding

    :type: float
    """

    grid_resolution_x: int
    """ Number of samples along the x axis of the volume

    :type: int
    """

    grid_resolution_y: int
    """ Number of samples along the y axis of the volume

    :type: int
    """

    grid_resolution_z: int
    """ Number of samples along the z axis of the volume

    :type: int
    """

    grid_surface_bias: float
    """ Moves capture points position away from surfaces to avoid artifacts

    :type: float
    """

    grid_validity_threshold: float
    """ Ratio of front-facing surface hits under which a grid sample will not be considered for lighting

    :type: float
    """

    grid_view_bias: float
    """ Offset sampling of the irradiance grid in the viewing direction to reduce light bleeding

    :type: float
    """

    influence_distance: float
    """ Influence distance of the probe

    :type: float
    """

    influence_type: str
    """ Type of influence volume

    :type: str
    """

    intensity: float
    """ Modify the intensity of the lighting captured by this probe

    :type: float
    """

    invert_visibility_collection: bool
    """ Invert visibility collection

    :type: bool
    """

    parallax_distance: float
    """ Lowest corner of the parallax bounding box

    :type: float
    """

    parallax_type: str
    """ Type of parallax volume

    :type: str
    """

    show_clip: bool
    """ Show the clipping distances in the 3D view

    :type: bool
    """

    show_data: bool
    """ Deprecated, use use_data_display instead

    :type: bool
    """

    show_influence: bool
    """ Show the influence volume in the 3D view

    :type: bool
    """

    show_parallax: bool
    """ Show the parallax correction volume in the 3D view

    :type: bool
    """

    surfel_density: float
    """ Number of surfels per unit distance (higher values improve quality)

    :type: float
    """

    type: str
    """ Type of light probe

    :type: str
    """

    use_custom_parallax: bool
    """ Enable custom settings for the parallax correction volume

    :type: bool
    """

    use_data_display: bool
    """ Display sampled data in the viewport to debug captured light

    :type: bool
    """

    visibility_bleed_bias: float
    """ Bias for reducing light-bleed on variance shadow maps

    :type: float
    """

    visibility_blur: float
    """ Filter size of the visibility blur

    :type: float
    """

    visibility_buffer_bias: float
    """ Bias for reducing self shadowing

    :type: float
    """

    visibility_collection: Collection
    """ Restrict objects visible for this probe

    :type: Collection
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
