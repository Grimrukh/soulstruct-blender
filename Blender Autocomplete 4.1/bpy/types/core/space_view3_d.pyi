import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .space import Space
from .region_view3_d import RegionView3D
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .view3_d_overlay import View3DOverlay
from .view3_d_shading import View3DShading

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceView3D(Space, bpy_struct):
    """3D View space data"""

    camera: Object
    """ Active camera used in this view (when unlocked from the scene's active camera)

    :type: Object
    """

    clip_end: float
    """ 3D View far clipping distance

    :type: float
    """

    clip_start: float
    """ 3D View near clipping distance (perspective view only)

    :type: float
    """

    icon_from_show_object_viewport: int
    """ 

    :type: int
    """

    lens: float
    """ Viewport lens angle

    :type: float
    """

    local_view: SpaceView3D
    """ Display an isolated subset of objects, apart from the scene visibility

    :type: SpaceView3D
    """

    lock_bone: str
    """ 3D View center is locked to this bone's position

    :type: str
    """

    lock_camera: bool
    """ Enable view navigation within the camera view

    :type: bool
    """

    lock_cursor: bool
    """ 3D View center is locked to the cursor's position

    :type: bool
    """

    lock_object: Object
    """ 3D View center is locked to this object's position

    :type: Object
    """

    mirror_xr_session: bool
    """ Synchronize the viewer perspective of virtual reality sessions with this 3D viewport

    :type: bool
    """

    overlay: View3DOverlay
    """ Settings for display of overlays in the 3D viewport

    :type: View3DOverlay
    """

    region_3d: RegionView3D
    """ 3D region for this space. When the space is in quad view, the camera region

    :type: RegionView3D
    """

    region_quadviews: bpy_prop_collection[RegionView3D]
    """ 3D regions (the third one defines quad view settings, the fourth one is same as 'region_3d')

    :type: bpy_prop_collection[RegionView3D]
    """

    render_border_max_x: float
    """ Maximum X value for the render region

    :type: float
    """

    render_border_max_y: float
    """ Maximum Y value for the render region

    :type: float
    """

    render_border_min_x: float
    """ Minimum X value for the render region

    :type: float
    """

    render_border_min_y: float
    """ Minimum Y value for the render region

    :type: float
    """

    shading: View3DShading
    """ Settings for shading in the 3D viewport

    :type: View3DShading
    """

    show_bundle_names: bool
    """ Show names for reconstructed tracks objects

    :type: bool
    """

    show_camera_path: bool
    """ Show reconstructed camera path

    :type: bool
    """

    show_gizmo: bool
    """ Show gizmos of all types

    :type: bool
    """

    show_gizmo_camera_dof_distance: bool
    """ Gizmo to adjust camera focus distance (depends on limits display)

    :type: bool
    """

    show_gizmo_camera_lens: bool
    """ Gizmo to adjust camera focal length or orthographic scale

    :type: bool
    """

    show_gizmo_context: bool
    """ Context sensitive gizmos for the active item

    :type: bool
    """

    show_gizmo_empty_force_field: bool
    """ Gizmo to adjust the force field

    :type: bool
    """

    show_gizmo_empty_image: bool
    """ Gizmo to adjust image size and position

    :type: bool
    """

    show_gizmo_light_look_at: bool
    """ Gizmo to adjust the direction of the light

    :type: bool
    """

    show_gizmo_light_size: bool
    """ Gizmo to adjust spot and area size

    :type: bool
    """

    show_gizmo_navigate: bool
    """ Viewport navigation gizmo

    :type: bool
    """

    show_gizmo_object_rotate: bool
    """ Gizmo to adjust rotation

    :type: bool
    """

    show_gizmo_object_scale: bool
    """ Gizmo to adjust scale

    :type: bool
    """

    show_gizmo_object_translate: bool
    """ Gizmo to adjust location

    :type: bool
    """

    show_gizmo_tool: bool
    """ Active tool gizmo

    :type: bool
    """

    show_object_select_armature: bool
    """ Allow selection of armatures

    :type: bool
    """

    show_object_select_camera: bool
    """ Allow selection of cameras

    :type: bool
    """

    show_object_select_curve: bool
    """ Allow selection of curves

    :type: bool
    """

    show_object_select_curves: bool
    """ Allow selection of hair curves

    :type: bool
    """

    show_object_select_empty: bool
    """ Allow selection of empties

    :type: bool
    """

    show_object_select_font: bool
    """ Allow selection of text objects

    :type: bool
    """

    show_object_select_grease_pencil: bool
    """ Allow selection of grease pencil objects

    :type: bool
    """

    show_object_select_lattice: bool
    """ Allow selection of lattices

    :type: bool
    """

    show_object_select_light: bool
    """ Allow selection of lights

    :type: bool
    """

    show_object_select_light_probe: bool
    """ Allow selection of light probes

    :type: bool
    """

    show_object_select_mesh: bool
    """ Allow selection of mesh objects

    :type: bool
    """

    show_object_select_meta: bool
    """ Allow selection of metaballs

    :type: bool
    """

    show_object_select_pointcloud: bool
    """ Allow selection of point clouds

    :type: bool
    """

    show_object_select_speaker: bool
    """ Allow selection of speakers

    :type: bool
    """

    show_object_select_surf: bool
    """ Allow selection of surfaces

    :type: bool
    """

    show_object_select_volume: bool
    """ Allow selection of volumes

    :type: bool
    """

    show_object_viewport_armature: bool
    """ Show armatures

    :type: bool
    """

    show_object_viewport_camera: bool
    """ Show cameras

    :type: bool
    """

    show_object_viewport_curve: bool
    """ Show curves

    :type: bool
    """

    show_object_viewport_curves: bool
    """ Show hair curves

    :type: bool
    """

    show_object_viewport_empty: bool
    """ Show empties

    :type: bool
    """

    show_object_viewport_font: bool
    """ Show text objects

    :type: bool
    """

    show_object_viewport_grease_pencil: bool
    """ Show grease pencil objects

    :type: bool
    """

    show_object_viewport_lattice: bool
    """ Show lattices

    :type: bool
    """

    show_object_viewport_light: bool
    """ Show lights

    :type: bool
    """

    show_object_viewport_light_probe: bool
    """ Show light probes

    :type: bool
    """

    show_object_viewport_mesh: bool
    """ Show mesh objects

    :type: bool
    """

    show_object_viewport_meta: bool
    """ Show metaballs

    :type: bool
    """

    show_object_viewport_pointcloud: bool
    """ Show point clouds

    :type: bool
    """

    show_object_viewport_speaker: bool
    """ Show speakers

    :type: bool
    """

    show_object_viewport_surf: bool
    """ Show surfaces

    :type: bool
    """

    show_object_viewport_volume: bool
    """ Show volumes

    :type: bool
    """

    show_reconstruction: bool
    """ Display reconstruction data from active movie clip

    :type: bool
    """

    show_region_asset_shelf: bool
    """ 

    :type: bool
    """

    show_region_hud: bool
    """ 

    :type: bool
    """

    show_region_tool_header: bool
    """ 

    :type: bool
    """

    show_region_toolbar: bool
    """ 

    :type: bool
    """

    show_region_ui: bool
    """ 

    :type: bool
    """

    show_stereo_3d_cameras: bool
    """ Show the left and right cameras

    :type: bool
    """

    show_stereo_3d_convergence_plane: bool
    """ Show the stereo 3D convergence plane

    :type: bool
    """

    show_stereo_3d_volume: bool
    """ Show the stereo 3D frustum volume

    :type: bool
    """

    show_viewer: bool
    """ Display non-final geometry from viewer nodes

    :type: bool
    """

    stereo_3d_camera: str
    """ 

    :type: str
    """

    stereo_3d_convergence_plane_alpha: float
    """ Opacity (alpha) of the convergence plane

    :type: float
    """

    stereo_3d_eye: str
    """ Current stereo eye being displayed

    :type: str
    """

    stereo_3d_volume_alpha: float
    """ Opacity (alpha) of the cameras' frustum volume

    :type: float
    """

    tracks_display_size: float
    """ Display size of tracks from reconstructed data

    :type: float
    """

    tracks_display_type: str
    """ Viewport display style for tracks

    :type: str
    """

    use_local_camera: bool
    """ Use a local camera in this view, rather than scene's active camera

    :type: bool
    """

    use_local_collections: bool
    """ Display a different set of collections in this viewport

    :type: bool
    """

    use_render_border: bool
    """ Use a region within the frame size for rendered viewport (when not viewing through the camera)

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

    @classmethod
    def draw_handler_add(
        cls,
        callback: typing.Any | None,
        args: tuple | None,
        region_type: str | None,
        draw_type: str | None,
    ) -> typing.Any:
        """Add a new draw handler to this space type.
        It will be called every time the specified region in the space type will be drawn.
        Note: All arguments are positional only for now.

                :param callback: A function that will be called when the region is drawn.
        It gets the specified arguments as input.
                :type callback: typing.Any | None
                :param args: Arguments that will be passed to the callback.
                :type args: tuple | None
                :param region_type: The region type the callback draws in; usually WINDOW. (`bpy.types.Region.type`)
                :type region_type: str | None
                :param draw_type: Usually POST_PIXEL for 2D drawing and POST_VIEW for 3D drawing. In some cases PRE_VIEW can be used. BACKDROP can be used for backdrops in the node editor.
                :type draw_type: str | None
                :return: Handler that can be removed later on.
                :rtype: typing.Any
        """
        ...

    @classmethod
    def draw_handler_remove(cls, handler: typing.Any | None, region_type: str | None):
        """Remove a draw handler that was added previously.

        :param handler: The draw handler that should be removed.
        :type handler: typing.Any | None
        :param region_type: Region type the callback was added to.
        :type region_type: str | None
        """
        ...
