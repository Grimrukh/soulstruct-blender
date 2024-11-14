import typing
import collections.abc
import mathutils
from .raytrace_eevee import RaytraceEEVEE
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SceneEEVEE(bpy_struct):
    """Scene display settings for 3D viewport"""

    bloom_clamp: float
    """ Maximum intensity a bloom pixel can have (0 to disable)

    :type: float
    """

    bloom_color: mathutils.Color
    """ Color applied to the bloom effect

    :type: mathutils.Color
    """

    bloom_intensity: float
    """ Blend factor

    :type: float
    """

    bloom_knee: float
    """ Makes transition between under/over-threshold gradual

    :type: float
    """

    bloom_radius: float
    """ Bloom spread distance

    :type: float
    """

    bloom_threshold: float
    """ Filters out pixels under this level of brightness

    :type: float
    """

    bokeh_denoise_fac: float
    """ Amount of flicker removal applied to bokeh highlights

    :type: float
    """

    bokeh_max_size: float
    """ Max size of the bokeh shape for the depth of field (lower is faster)

    :type: float
    """

    bokeh_neighbor_max: float
    """ Maximum brightness to consider when rejecting bokeh sprites based on neighborhood (lower is faster)

    :type: float
    """

    bokeh_overblur: float
    """ Apply blur to each jittered sample to reduce under-sampling artifacts

    :type: float
    """

    bokeh_threshold: float
    """ Brightness threshold for using sprite base depth of field

    :type: float
    """

    gi_auto_bake: bool
    """ Auto bake indirect lighting when editing probes

    :type: bool
    """

    gi_cache_info: str
    """ Info on current cache status

    :type: str
    """

    gi_cubemap_display_size: float
    """ Size of the cubemap spheres to debug captured light

    :type: float
    """

    gi_cubemap_resolution: str
    """ Size of every cubemaps

    :type: str
    """

    gi_diffuse_bounces: int
    """ Number of times the light is reinjected inside light grids, 0 disable indirect diffuse light

    :type: int
    """

    gi_filter_quality: float
    """ Take more samples during cubemap filtering to remove artifacts

    :type: float
    """

    gi_glossy_clamp: float
    """ Clamp pixel intensity to reduce noise inside glossy reflections from reflection cubemaps (0 to disable)

    :type: float
    """

    gi_irradiance_display_size: float
    """ Size of the irradiance sample spheres to debug captured light

    :type: float
    """

    gi_irradiance_pool_size: str
    """ Size of the irradiance pool, a bigger pool size allows for more irradiance grid in the scene but might not fit into GPU memory and decrease performance

    :type: str
    """

    gi_irradiance_smoothing: float
    """ Smoother irradiance interpolation but introduce light bleeding

    :type: float
    """

    gi_show_cubemaps: bool
    """ Display captured cubemaps in the viewport

    :type: bool
    """

    gi_show_irradiance: bool
    """ Display irradiance samples in the viewport

    :type: bool
    """

    gi_visibility_resolution: str
    """ Size of the shadow map applied to each irradiance sample

    :type: str
    """

    gtao_distance: float
    """ Distance of object that contribute to the ambient occlusion effect

    :type: float
    """

    gtao_factor: float
    """ Factor for ambient occlusion blending

    :type: float
    """

    gtao_quality: float
    """ Precision of the horizon search

    :type: float
    """

    horizon_bias: float
    """ Bias the horizon angles to reduce self intersection artifacts

    :type: float
    """

    horizon_quality: float
    """ Precision of the horizon scan

    :type: float
    """

    horizon_thickness: float
    """ Constant thickness of the surfaces considered when doing horizon scan and by extension ambient occlusion

    :type: float
    """

    light_threshold: float
    """ Minimum light intensity for a light to contribute to the lighting

    :type: float
    """

    motion_blur_depth_scale: float
    """ Lower values will reduce background bleeding onto foreground elements

    :type: float
    """

    motion_blur_max: int
    """ Maximum blur distance a pixel can spread over

    :type: int
    """

    motion_blur_position: str
    """ Offset for the shutter's time interval, allows to change the motion blur trails

    :type: str
    """

    motion_blur_shutter: float
    """ Time taken in frames between shutter open and close

    :type: float
    """

    motion_blur_steps: int
    """ Controls accuracy of motion blur, more steps means longer render time

    :type: int
    """

    overscan_size: float
    """ Percentage of render size to add as overscan to the internal render buffers

    :type: float
    """

    ray_tracing_method: str
    """ Select the tracing method used to find scene-ray intersections

    :type: str
    """

    ray_tracing_options: RaytraceEEVEE
    """ EEVEE settings for tracing reflections

    :type: RaytraceEEVEE
    """

    shadow_cascade_size: str
    """ Size of sun light shadow maps

    :type: str
    """

    shadow_cube_size: str
    """ Size of point and area light shadow maps

    :type: str
    """

    shadow_normal_bias: float
    """ Move shadows along their normal

    :type: float
    """

    shadow_pool_size: str
    """ Size of the shadow pool, a bigger pool size allows for more shadows in the scene but might not fit into GPU memory

    :type: str
    """

    shadow_ray_count: int
    """ Amount of shadow ray to trace for each light

    :type: int
    """

    shadow_step_count: int
    """ Amount of shadow map sample per shadow ray

    :type: int
    """

    ssr_border_fade: float
    """ Screen percentage used to fade the SSR

    :type: float
    """

    ssr_firefly_fac: float
    """ Clamp pixel intensity to remove noise (0 to disable)

    :type: float
    """

    ssr_max_roughness: float
    """ Do not raytrace reflections for roughness above this value

    :type: float
    """

    ssr_quality: float
    """ Precision of the screen space ray-tracing

    :type: float
    """

    ssr_thickness: float
    """ Pixel thickness used to detect intersection

    :type: float
    """

    sss_jitter_threshold: float
    """ Rotate samples that are below this threshold

    :type: float
    """

    sss_samples: int
    """ Number of samples to compute the scattering effect

    :type: int
    """

    taa_render_samples: int
    """ Number of samples per pixel for rendering

    :type: int
    """

    taa_samples: int
    """ Number of samples, unlimited if 0

    :type: int
    """

    use_bloom: bool
    """ High brightness pixels generate a glowing effect

    :type: bool
    """

    use_bokeh_high_quality_slight_defocus: bool
    """ Sample all pixels in almost in-focus regions to eliminate noise

    :type: bool
    """

    use_bokeh_jittered: bool
    """ Jitter camera position to create accurate blurring using render samples

    :type: bool
    """

    use_gtao: bool
    """ Enable ambient occlusion to simulate medium scale indirect shadowing

    :type: bool
    """

    use_gtao_bent_normals: bool
    """ Compute main non occluded direction to sample the environment

    :type: bool
    """

    use_gtao_bounce: bool
    """ An approximation to simulate light bounces giving less occlusion on brighter objects

    :type: bool
    """

    use_motion_blur: bool
    """ Enable motion blur effect (only in camera view)

    :type: bool
    """

    use_overscan: bool
    """ Internally render past the image border to avoid screen-space effects disappearing

    :type: bool
    """

    use_raytracing: bool
    """ Enable the ray-tracing module

    :type: bool
    """

    use_shadow_high_bitdepth: bool
    """ Use 32-bit shadows

    :type: bool
    """

    use_shadows: bool
    """ Enable shadow casting from lights

    :type: bool
    """

    use_soft_shadows: bool
    """ Randomize shadowmaps origin to create soft shadows

    :type: bool
    """

    use_ssr: bool
    """ Enable screen space reflection

    :type: bool
    """

    use_ssr_halfres: bool
    """ Raytrace at a lower resolution

    :type: bool
    """

    use_ssr_refraction: bool
    """ Enable screen space Refractions

    :type: bool
    """

    use_taa_reprojection: bool
    """ Denoise image using temporal reprojection (can leave some ghosting)

    :type: bool
    """

    use_volumetric_lights: bool
    """ Enable scene light interactions with volumetrics

    :type: bool
    """

    use_volumetric_shadows: bool
    """ Generate shadows from volumetric material (Very expensive)

    :type: bool
    """

    volumetric_end: float
    """ End distance of the volumetric effect

    :type: float
    """

    volumetric_light_clamp: float
    """ Maximum light contribution, reducing noise

    :type: float
    """

    volumetric_ray_depth: int
    """ Maximum surface intersection count used by the accurate volume intersection method. Will create artifact if it is exceeded

    :type: int
    """

    volumetric_sample_distribution: float
    """ Distribute more samples closer to the camera

    :type: float
    """

    volumetric_samples: int
    """ Number of samples to compute volumetric effects

    :type: int
    """

    volumetric_shadow_samples: int
    """ Number of samples to compute volumetric shadowing

    :type: int
    """

    volumetric_start: float
    """ Start distance of the volumetric effect

    :type: float
    """

    volumetric_tile_size: str
    """ Control the quality of the volumetric effects (lower size increase vram usage and quality)

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
