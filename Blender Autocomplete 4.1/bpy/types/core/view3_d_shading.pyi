import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .studio_light import StudioLight

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class View3DShading(bpy_struct):
    """Settings for shading in the 3D viewport"""

    aov_name: str
    """ Name of the active Shader AOV

    :type: str
    """

    background_color: mathutils.Color
    """ Color for custom background color

    :type: mathutils.Color
    """

    background_type: str
    """ Way to display the background

    :type: str
    """

    cavity_ridge_factor: float
    """ Factor for the cavity ridges

    :type: float
    """

    cavity_type: str
    """ Way to display the cavity shading

    :type: str
    """

    cavity_valley_factor: float
    """ Factor for the cavity valleys

    :type: float
    """

    color_type: str
    """ Color Type

    :type: str
    """

    curvature_ridge_factor: float
    """ Factor for the curvature ridges

    :type: float
    """

    curvature_valley_factor: float
    """ Factor for the curvature valleys

    :type: float
    """

    cycles: typing.Any
    """ 

    :type: typing.Any
    """

    light: str
    """ Lighting Method for Solid/Texture Viewport Shading

    :type: str
    """

    object_outline_color: mathutils.Color
    """ Color for object outline

    :type: mathutils.Color
    """

    render_pass: str
    """ Render Pass to show in the viewport

    :type: str
    """

    selected_studio_light: StudioLight
    """ Selected StudioLight

    :type: StudioLight
    """

    shadow_intensity: float
    """ Darkness of shadows

    :type: float
    """

    show_backface_culling: bool
    """ Use back face culling to hide the back side of faces

    :type: bool
    """

    show_cavity: bool
    """ Show Cavity

    :type: bool
    """

    show_object_outline: bool
    """ Show Object Outline

    :type: bool
    """

    show_shadows: bool
    """ Show Shadow

    :type: bool
    """

    show_specular_highlight: bool
    """ Render specular highlights

    :type: bool
    """

    show_xray: bool
    """ Show whole scene transparent

    :type: bool
    """

    show_xray_wireframe: bool
    """ Show whole scene transparent

    :type: bool
    """

    single_color: mathutils.Color
    """ Color for single color mode

    :type: mathutils.Color
    """

    studio_light: str
    """ Studio lighting setup

    :type: str
    """

    studiolight_background_alpha: float
    """ Show the studiolight in the background

    :type: float
    """

    studiolight_background_blur: float
    """ Blur the studiolight in the background

    :type: float
    """

    studiolight_intensity: float
    """ Strength of the studiolight

    :type: float
    """

    studiolight_rotate_z: float
    """ Rotation of the studiolight around the Z-Axis

    :type: float
    """

    type: str
    """ Method to display/shade objects in the 3D View

    :type: str
    """

    use_compositor: str
    """ When to preview the compositor output inside the viewport

    :type: str
    """

    use_dof: bool
    """ Use depth of field on viewport using the values from the active camera

    :type: bool
    """

    use_scene_lights: bool
    """ Render lights and light probes of the scene

    :type: bool
    """

    use_scene_lights_render: bool
    """ Render lights and light probes of the scene

    :type: bool
    """

    use_scene_world: bool
    """ Use scene world for lighting

    :type: bool
    """

    use_scene_world_render: bool
    """ Use scene world for lighting

    :type: bool
    """

    use_studiolight_view_rotation: bool
    """ Make the HDR rotation fixed and not follow the camera

    :type: bool
    """

    use_world_space_lighting: bool
    """ Make the lighting fixed and not follow the camera

    :type: bool
    """

    wireframe_color_type: str
    """ Wire Color Type

    :type: str
    """

    xray_alpha: float
    """ Amount of alpha to use

    :type: float
    """

    xray_alpha_wireframe: float
    """ Amount of alpha to use

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
