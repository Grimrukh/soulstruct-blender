import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .color_ramp import ColorRamp

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesView(bpy_struct):
    """Preferences related to viewing data"""

    color_picker_type: str
    """ Different styles of displaying the color picker widget

    :type: str
    """

    factor_display_type: str
    """ How factor values are displayed

    :type: str
    """

    filebrowser_display_type: str
    """ Default location where the File Editor will be displayed in

    :type: str
    """

    font_path_ui: str
    """ Path to interface font

    :type: str
    """

    font_path_ui_mono: str
    """ Path to interface monospaced Font

    :type: str
    """

    gizmo_size: int
    """ Diameter of the gizmo

    :type: int
    """

    gizmo_size_navigate_v3d: int
    """ The Navigate Gizmo size

    :type: int
    """

    header_align: str
    """ Default header position for new space-types

    :type: str
    """

    language: str
    """ Language used for translation

    :type: str
    """

    lookdev_sphere_size: int
    """ Diameter of the HDRI preview spheres

    :type: int
    """

    mini_axis_brightness: int
    """ Brightness of the icon

    :type: int
    """

    mini_axis_size: int
    """ The axes icon's size

    :type: int
    """

    mini_axis_type: str
    """ Show small rotating 3D axes in the top right corner of the 3D viewport

    :type: str
    """

    open_sublevel_delay: int
    """ Time delay in 1/10 seconds before automatically opening sub level menus

    :type: int
    """

    open_toplevel_delay: int
    """ Time delay in 1/10 seconds before automatically opening top level menus

    :type: int
    """

    pie_animation_timeout: int
    """ Time needed to fully animate the pie to unfolded state (in 1/100ths of sec)

    :type: int
    """

    pie_initial_timeout: int
    """ Pie menus will use the initial mouse position as center for this amount of time (in 1/100ths of sec)

    :type: int
    """

    pie_menu_confirm: int
    """ Distance threshold after which selection is made (zero to disable)

    :type: int
    """

    pie_menu_radius: int
    """ Pie menu size in pixels

    :type: int
    """

    pie_menu_threshold: int
    """ Distance from center needed before a selection can be made

    :type: int
    """

    pie_tap_timeout: int
    """ Pie menu button held longer than this will dismiss menu on release (in 1/100ths of sec)

    :type: int
    """

    playback_fps_samples: int
    """ The number of frames to use for calculating FPS average. Zero to calculate this automatically, where the number of samples matches the target FPS

    :type: int
    """

    render_display_type: str
    """ Default location where rendered images will be displayed in

    :type: str
    """

    rotation_angle: float
    """ Rotation step for numerical pad keys (2 4 6 8)

    :type: float
    """

    show_addons_enabled_only: bool
    """ Only show enabled add-ons. Un-check to see all installed add-ons

    :type: bool
    """

    show_column_layout: bool
    """ Use a column layout for toolbox

    :type: bool
    """

    show_developer_ui: bool
    """ Show options for developers (edit source in context menu, geometry indices)

    :type: bool
    """

    show_gizmo: bool
    """ Use transform gizmos by default

    :type: bool
    """

    show_navigate_ui: bool
    """ Show navigation controls in 2D and 3D views which do not have scroll bars

    :type: bool
    """

    show_object_info: bool
    """ Include the name of the active object and the current frame number in the text info overlay

    :type: bool
    """

    show_playback_fps: bool
    """ Include the number of frames displayed per second in the text info overlay while animation is played back

    :type: bool
    """

    show_splash: bool
    """ Display splash screen on startup

    :type: bool
    """

    show_statusbar_memory: bool
    """ Show Blender memory usage

    :type: bool
    """

    show_statusbar_scene_duration: bool
    """ Show scene duration

    :type: bool
    """

    show_statusbar_stats: bool
    """ Show scene statistics

    :type: bool
    """

    show_statusbar_version: bool
    """ Show Blender version string

    :type: bool
    """

    show_statusbar_vram: bool
    """ Show GPU video memory usage

    :type: bool
    """

    show_tooltips: bool
    """ Display tooltips (when disabled, hold Alt to force display)

    :type: bool
    """

    show_tooltips_python: bool
    """ Show Python references in tooltips

    :type: bool
    """

    show_view_name: bool
    """ Include the name of the view orientation in the text info overlay

    :type: bool
    """

    smooth_view: int
    """ Time to animate the view in milliseconds, zero to disable

    :type: int
    """

    text_hinting: str
    """ Method for making user interface text render sharp

    :type: str
    """

    timecode_style: str
    """ Format of timecode displayed when not displaying timing in terms of frames

    :type: str
    """

    ui_line_width: str
    """ Changes the thickness of widget outlines, lines and dots in the interface

    :type: str
    """

    ui_scale: float
    """ Changes the size of the fonts and widgets in the interface

    :type: float
    """

    use_fresnel_edit: bool
    """ Enable a fresnel effect on edit mesh overlays.
It improves shape readability of very dense meshes, but increases eye fatigue when modeling lower poly

    :type: bool
    """

    use_mouse_over_open: bool
    """ Open menu buttons and pulldowns automatically when the mouse is hovering

    :type: bool
    """

    use_save_prompt: bool
    """ Ask for confirmation when quitting with unsaved changes

    :type: bool
    """

    use_text_antialiasing: bool
    """ Smooth jagged edges of user interface text

    :type: bool
    """

    use_text_render_subpixelaa: bool
    """ Render text for optimal horizontal placement

    :type: bool
    """

    use_translate_interface: bool
    """ Translate all labels in menus, buttons and panels (note that this might make it hard to follow tutorials or the manual)

    :type: bool
    """

    use_translate_new_dataname: bool
    """ Translate the names of new data-blocks (objects, materials...)

    :type: bool
    """

    use_translate_reports: bool
    """ Translate additional information, such as error messages

    :type: bool
    """

    use_translate_tooltips: bool
    """ Translate the descriptions when hovering UI elements (recommended)

    :type: bool
    """

    use_weight_color_range: bool
    """ Enable color range used for weight visualization in weight painting mode

    :type: bool
    """

    view2d_grid_spacing_min: int
    """ Minimum number of pixels between each gridline in 2D Viewports

    :type: int
    """

    view_frame_keyframes: int
    """ Keyframes around cursor that we zoom around

    :type: int
    """

    view_frame_seconds: float
    """ Seconds around cursor that we zoom around

    :type: float
    """

    view_frame_type: str
    """ How zooming to frame focuses around current frame

    :type: str
    """

    weight_color_range: ColorRamp
    """ Color range used for weight visualization in weight painting mode

    :type: ColorRamp
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
