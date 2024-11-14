import typing
import collections.abc
import mathutils
from .blend_data import BlendData
from .context import Context
from .struct import Struct
from .scene import Scene
from .depsgraph import Depsgraph
from .object import Object
from .bpy_struct import bpy_struct
from .node import Node
from .render_settings import RenderSettings
from .view_layer import ViewLayer
from .render_result import RenderResult
from .render_pass import RenderPass

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderEngine(bpy_struct):
    """Render engine"""

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ 

    :type: str
    """

    bl_use_alembic_procedural: bool
    """ Support loading Alembic data at render time

    :type: bool
    """

    bl_use_custom_freestyle: bool
    """ Handles freestyle rendering on its own, instead of delegating it to EEVEE

    :type: bool
    """

    bl_use_eevee_viewport: bool
    """ Uses EEVEE for viewport shading in Material Preview shading mode

    :type: bool
    """

    bl_use_gpu_context: bool
    """ Enable OpenGL context for the render method, for engines that render using OpenGL

    :type: bool
    """

    bl_use_image_save: bool
    """ Save images/movie to disk while rendering an animation. Disabling image saving is only supported when bl_use_postprocess is also disabled

    :type: bool
    """

    bl_use_materialx: bool
    """ Use MaterialX for exporting materials to Hydra

    :type: bool
    """

    bl_use_postprocess: bool
    """ Apply compositing on render results

    :type: bool
    """

    bl_use_preview: bool
    """ Render engine supports being used for rendering previews of materials, lights and worlds

    :type: bool
    """

    bl_use_shading_nodes_custom: bool
    """ Don't expose Cycles and EEVEE shading nodes in the node editor user interface, so own nodes can be used instead

    :type: bool
    """

    bl_use_spherical_stereo: bool
    """ Support spherical stereo camera models

    :type: bool
    """

    bl_use_stereo_viewport: bool
    """ Support rendering stereo 3D viewport

    :type: bool
    """

    camera_override: Object
    """ 

    :type: Object
    """

    is_animation: bool
    """ 

    :type: bool
    """

    is_preview: bool
    """ 

    :type: bool
    """

    layer_override: list[bool]
    """ 

    :type: list[bool]
    """

    render: RenderSettings
    """ 

    :type: RenderSettings
    """

    resolution_x: int
    """ 

    :type: int
    """

    resolution_y: int
    """ 

    :type: int
    """

    temporary_directory: str
    """ 

    :type: str
    """

    use_highlight_tiles: bool
    """ 

    :type: bool
    """

    def update(self, data: BlendData | None = None, depsgraph: Depsgraph | None = None):
        """Export scene data for render

        :param data:
        :type data: BlendData | None
        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def render(self, depsgraph: Depsgraph | None):
        """Render scene into an image

        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def render_frame_finish(self):
        """Perform finishing operations after all view layers in a frame were rendered"""
        ...

    def draw(self, context: Context | None, depsgraph: Depsgraph | None):
        """Draw render image

        :param context:
        :type context: Context | None
        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def bake(
        self,
        depsgraph: Depsgraph | None,
        object: Object | None,
        pass_type: str | None,
        pass_filter: int | None,
        width: int | None,
        height: int | None,
    ):
        """Bake passes

        :param depsgraph:
        :type depsgraph: Depsgraph | None
        :param object:
        :type object: Object | None
        :param pass_type: Pass, Pass to bake
        :type pass_type: str | None
        :param pass_filter: Pass Filter, Filter to combined, diffuse, glossy and transmission passes
        :type pass_filter: int | None
        :param width: Width, Image width
        :type width: int | None
        :param height: Height, Image height
        :type height: int | None
        """
        ...

    def view_update(self, context: Context | None, depsgraph: Depsgraph | None):
        """Update on data changes for viewport render

        :param context:
        :type context: Context | None
        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def view_draw(self, context: Context | None, depsgraph: Depsgraph | None):
        """Draw viewport render

        :param context:
        :type context: Context | None
        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def update_script_node(self, node: Node | None = None):
        """Compile shader script node

        :param node:
        :type node: Node | None
        """
        ...

    def update_render_passes(
        self, scene: Scene | None = None, renderlayer: ViewLayer | None = None
    ):
        """Update the render passes that will be generated

        :param scene:
        :type scene: Scene | None
        :param renderlayer:
        :type renderlayer: ViewLayer | None
        """
        ...

    def tag_redraw(self):
        """Request redraw for viewport rendering"""
        ...

    def tag_update(self):
        """Request update call for viewport rendering"""
        ...

    def begin_result(
        self,
        x: int | None,
        y: int | None,
        w: int | None,
        h: int | None,
        layer: str | typing.Any = "",
        view: str | typing.Any = "",
    ) -> RenderResult:
        """Create render result to write linear floating-point render layers and passes

        :param x: X
        :type x: int | None
        :param y: Y
        :type y: int | None
        :param w: Width
        :type w: int | None
        :param h: Height
        :type h: int | None
        :param layer: Layer, Single layer to get render result for
        :type layer: str | typing.Any
        :param view: View, Single view to get render result for
        :type view: str | typing.Any
        :return: Result
        :rtype: RenderResult
        """
        ...

    def update_result(self, result: RenderResult | None):
        """Signal that pixels have been updated and can be redrawn in the user interface

        :param result: Result
        :type result: RenderResult | None
        """
        ...

    def end_result(
        self,
        result: RenderResult | None,
        cancel: bool | typing.Any | None = False,
        highlight: bool | typing.Any | None = False,
        do_merge_results: bool | typing.Any | None = False,
    ):
        """All pixels in the render result have been set and are final

        :param result: Result
        :type result: RenderResult | None
        :param cancel: Cancel, Don't mark tile as done, don't merge results unless forced
        :type cancel: bool | typing.Any | None
        :param highlight: Highlight, Don't mark tile as done yet
        :type highlight: bool | typing.Any | None
        :param do_merge_results: Merge Results, Merge results even if cancel=true
        :type do_merge_results: bool | typing.Any | None
        """
        ...

    def add_pass(
        self,
        name: str | typing.Any,
        channels: int | None,
        chan_id: str | typing.Any,
        layer: str | typing.Any = "",
    ):
        """Add a pass to the render layer

        :param name: Name, Name of the Pass, without view or channel tag
        :type name: str | typing.Any
        :param channels: Channels
        :type channels: int | None
        :param chan_id: Channel IDs, Channel names, one character per channel
        :type chan_id: str | typing.Any
        :param layer: Layer, Single layer to add render pass to
        :type layer: str | typing.Any
        """
        ...

    def get_result(self) -> RenderResult:
        """Get final result for non-pixel operations

        :return: Result
        :rtype: RenderResult
        """
        ...

    def test_break(self) -> bool:
        """Test if the render operation should been canceled, this is a fast call that should be used regularly for responsiveness

        :return: Break
        :rtype: bool
        """
        ...

    def pass_by_index_get(
        self, layer: str | typing.Any, index: int | None
    ) -> RenderPass:
        """pass_by_index_get

        :param layer: Layer, Name of render layer to get pass for
        :type layer: str | typing.Any
        :param index: Index, Index of pass to get
        :type index: int | None
        :return: Index, Index of pass to get
        :rtype: RenderPass
        """
        ...

    def active_view_get(self) -> str | typing.Any:
        """active_view_get

        :return: View, Single view active
        :rtype: str | typing.Any
        """
        ...

    def active_view_set(self, view: str | typing.Any):
        """active_view_set

        :param view: View, Single view to set as active
        :type view: str | typing.Any
        """
        ...

    def camera_shift_x(
        self,
        camera: Object | None,
        use_spherical_stereo: bool | typing.Any | None = False,
    ) -> float:
        """camera_shift_x

        :param camera:
        :type camera: Object | None
        :param use_spherical_stereo: Spherical Stereo
        :type use_spherical_stereo: bool | typing.Any | None
        :return: Shift X
        :rtype: float
        """
        ...

    def camera_model_matrix(
        self,
        camera: Object | None,
        use_spherical_stereo: bool | typing.Any | None = False,
    ) -> mathutils.Matrix:
        """camera_model_matrix

        :param camera:
        :type camera: Object | None
        :param use_spherical_stereo: Spherical Stereo
        :type use_spherical_stereo: bool | typing.Any | None
        :return: Model Matrix, Normalized camera model matrix
        :rtype: mathutils.Matrix
        """
        ...

    def use_spherical_stereo(self, camera: Object | None) -> bool:
        """use_spherical_stereo

        :param camera:
        :type camera: Object | None
        :return: Spherical Stereo
        :rtype: bool
        """
        ...

    def update_stats(self, stats: str | typing.Any, info: str | typing.Any):
        """Update and signal to redraw render status text

        :param stats: Stats
        :type stats: str | typing.Any
        :param info: Info
        :type info: str | typing.Any
        """
        ...

    def frame_set(self, frame: int | None, subframe: float | None):
        """Evaluate scene at a different frame (for motion blur)

        :param frame: Frame
        :type frame: int | None
        :param subframe: Subframe
        :type subframe: float | None
        """
        ...

    def update_progress(self, progress: float | None):
        """Update progress percentage of render

        :param progress: Percentage of render that's done
        :type progress: float | None
        """
        ...

    def update_memory_stats(
        self, memory_used: typing.Any | None = 0.0, memory_peak: typing.Any | None = 0.0
    ):
        """Update memory usage statistics

        :param memory_used: Current memory usage in megabytes
        :type memory_used: typing.Any | None
        :param memory_peak: Peak memory usage in megabytes
        :type memory_peak: typing.Any | None
        """
        ...

    def report(self, type, message: str | typing.Any):
        """Report info, warning or error messages

        :param type: Type
        :param message: Report Message
        :type message: str | typing.Any
        """
        ...

    def error_set(self, message: str | typing.Any):
        """Set error message displaying after the render is finished

        :param message: Report Message
        :type message: str | typing.Any
        """
        ...

    def bind_display_space_shader(self, scene: Scene | None):
        """Bind GLSL fragment shader that converts linear colors to display space colors using scene color management settings

        :param scene:
        :type scene: Scene | None
        """
        ...

    def unbind_display_space_shader(self):
        """Unbind GLSL display space shader, must always be called after binding the shader"""
        ...

    def support_display_space_shader(self, scene: Scene | None) -> bool:
        """Test if GLSL display space shader is supported for the combination of graphics card and scene settings

        :param scene:
        :type scene: Scene | None
        :return: Supported
        :rtype: bool
        """
        ...

    def get_preview_pixel_size(self, scene: Scene | None) -> int:
        """Get the pixel size that should be used for preview rendering

        :param scene:
        :type scene: Scene | None
        :return: Pixel Size
        :rtype: int
        """
        ...

    def free_blender_memory(self):
        """Free Blender side memory of render engine"""
        ...

    def tile_highlight_set(
        self,
        x: int | None,
        y: int | None,
        width: int | None,
        height: int | None,
        highlight: bool | None,
    ):
        """Set highlighted state of the given tile

        :param x: X
        :type x: int | None
        :param y: Y
        :type y: int | None
        :param width: Width
        :type width: int | None
        :param height: Height
        :type height: int | None
        :param highlight: Highlight
        :type highlight: bool | None
        """
        ...

    def tile_highlight_clear_all(self):
        """The temp directory used by Blender"""
        ...

    def register_pass(
        self,
        scene: Scene | None,
        view_layer: ViewLayer | None,
        name: str | typing.Any,
        channels: int | None,
        chanid: str | typing.Any,
        type: str | None,
    ):
        """Register a render pass that will be part of the render with the current settings

        :param scene:
        :type scene: Scene | None
        :param view_layer:
        :type view_layer: ViewLayer | None
        :param name: Name
        :type name: str | typing.Any
        :param channels: Channels
        :type channels: int | None
        :param chanid: Channel IDs
        :type chanid: str | typing.Any
        :param type: Type
        :type type: str | None
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
