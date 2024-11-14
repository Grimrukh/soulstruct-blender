import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .walk_navigation import WalkNavigation

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesInput(bpy_struct):
    """Settings for input devices"""

    drag_threshold: int
    """ Number of pixels to drag before a drag event is triggered for keyboard and other non mouse/tablet input (otherwise click events are detected)

    :type: int
    """

    drag_threshold_mouse: int
    """ Number of pixels to drag before a drag event is triggered for mouse/trackpad input (otherwise click events are detected)

    :type: int
    """

    drag_threshold_tablet: int
    """ Number of pixels to drag before a drag event is triggered for tablet input (otherwise click events are detected)

    :type: int
    """

    invert_mouse_zoom: bool
    """ Invert the axis of mouse movement for zooming

    :type: bool
    """

    invert_zoom_wheel: bool
    """ Swap the Mouse Wheel zoom direction

    :type: bool
    """

    mouse_double_click_time: int
    """ Time/delay (in ms) for a double click

    :type: int
    """

    mouse_emulate_3_button_modifier: str
    """ Hold this modifier to emulate the middle mouse button

    :type: str
    """

    move_threshold: int
    """ Number of pixels to before the cursor is considered to have moved (used for cycling selected items on successive clicks)

    :type: int
    """

    navigation_mode: str
    """ Which method to use for viewport navigation

    :type: str
    """

    ndof_deadzone: float
    """ Threshold of initial movement needed from the device's rest position

    :type: float
    """

    ndof_fly_helicopter: bool
    """ Device up/down directly controls the Z position of the 3D viewport

    :type: bool
    """

    ndof_lock_camera_pan_zoom: bool
    """ Pan/zoom the camera view instead of leaving the camera view when orbiting

    :type: bool
    """

    ndof_lock_horizon: bool
    """ Keep horizon level while flying with 3D Mouse

    :type: bool
    """

    ndof_orbit_sensitivity: float
    """ Overall sensitivity of the 3D Mouse for orbiting

    :type: float
    """

    ndof_pan_yz_swap_axis: bool
    """ Pan using up/down on the device (otherwise forward/backward)

    :type: bool
    """

    ndof_panx_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_pany_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_panz_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_rotx_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_roty_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_rotz_invert_axis: bool
    """ 

    :type: bool
    """

    ndof_sensitivity: float
    """ Overall sensitivity of the 3D Mouse for panning

    :type: float
    """

    ndof_show_guide: bool
    """ Display the center and axis during rotation

    :type: bool
    """

    ndof_view_navigate_method: str
    """ Navigation style in the viewport

    :type: str
    """

    ndof_view_rotate_method: str
    """ Rotation style in the viewport

    :type: str
    """

    ndof_zoom_invert: bool
    """ Zoom using opposite direction

    :type: bool
    """

    pressure_softness: float
    """ Adjusts softness of the low pressure response onset using a gamma curve

    :type: float
    """

    pressure_threshold_max: float
    """ Raw input pressure value that is interpreted as 100% by Blender

    :type: float
    """

    tablet_api: str
    """ Select the tablet API to use for pressure sensitivity (may require restarting Blender for changes to take effect)

    :type: str
    """

    use_auto_perspective: bool
    """ Automatically switch between orthographic and perspective when changing from top/front/side views

    :type: bool
    """

    use_drag_immediately: bool
    """ Moving things with a mouse drag confirms when releasing the button

    :type: bool
    """

    use_emulate_numpad: bool
    """ Main 1 to 0 keys act as the numpad ones (useful for laptops)

    :type: bool
    """

    use_mouse_continuous: bool
    """ Let the mouse wrap around the view boundaries so mouse movements are not limited by the screen size (used by transform, dragging of UI controls, etc.)

    :type: bool
    """

    use_mouse_depth_navigate: bool
    """ Use the depth under the mouse to improve view pan/rotate/zoom functionality

    :type: bool
    """

    use_mouse_emulate_3_button: bool
    """ Emulate Middle Mouse with Alt+Left Mouse

    :type: bool
    """

    use_multitouch_gestures: bool
    """ Use multi-touch gestures for navigation with touchpad, instead of scroll wheel emulation

    :type: bool
    """

    use_ndof: bool
    """ 

    :type: bool
    """

    use_numeric_input_advanced: bool
    """ When entering numbers while transforming, default to advanced mode for full math expression evaluation

    :type: bool
    """

    use_rotate_around_active: bool
    """ Use selection as the pivot point

    :type: bool
    """

    use_zoom_to_mouse: bool
    """ Zoom in towards the mouse pointer's position in the 3D view, rather than the 2D window center

    :type: bool
    """

    view_rotate_method: str
    """ Orbit method in the viewport

    :type: str
    """

    view_rotate_sensitivity_trackball: float
    """ Scale trackball orbit sensitivity

    :type: float
    """

    view_rotate_sensitivity_turntable: float
    """ Rotation amount per pixel to control how fast the viewport orbits

    :type: float
    """

    view_zoom_axis: str
    """ Axis of mouse movement to zoom in or out on

    :type: str
    """

    view_zoom_method: str
    """ Which style to use for viewport scaling

    :type: str
    """

    walk_navigation: WalkNavigation
    """ Settings for walk navigation mode

    :type: WalkNavigation
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
