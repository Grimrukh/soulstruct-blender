import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .image_format_settings import ImageFormatSettings
from .scene_render_view import SceneRenderView
from .struct import Struct
from .bpy_struct import bpy_struct
from .f_fmpeg_settings import FFmpegSettings
from .bpy_prop_array import bpy_prop_array
from .render_views import RenderViews
from .bake_settings import BakeSettings
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderSettings(bpy_struct):
    """Rendering settings for a Scene data-block"""

    bake: BakeSettings
    """ 

    :type: BakeSettings
    """

    bake_bias: float
    """ Bias towards faces further away from the object (in Blender units)

    :type: float
    """

    bake_margin: int
    """ Extends the baked result as a post process filter

    :type: int
    """

    bake_margin_type: str
    """ Algorithm to generate the margin

    :type: str
    """

    bake_samples: int
    """ Number of samples used for ambient occlusion baking from multires

    :type: int
    """

    bake_type: str
    """ Choose shading information to bake into the image

    :type: str
    """

    bake_user_scale: float
    """ Instead of automatically normalizing to the range 0 to 1, apply a user scale to the derivative map

    :type: float
    """

    border_max_x: float
    """ Maximum X value for the render region

    :type: float
    """

    border_max_y: float
    """ Maximum Y value for the render region

    :type: float
    """

    border_min_x: float
    """ Minimum X value for the render region

    :type: float
    """

    border_min_y: float
    """ Minimum Y value for the render region

    :type: float
    """

    dither_intensity: float
    """ Amount of dithering noise added to the rendered image to break up banding

    :type: float
    """

    engine: str
    """ Engine to use for rendering

    :type: str
    """

    ffmpeg: FFmpegSettings
    """ FFmpeg related settings for the scene

    :type: FFmpegSettings
    """

    file_extension: str
    """ The file extension used for saving renders

    :type: str
    """

    filepath: str
    """ Directory/name to save animations, # characters define the position and padding of frame numbers

    :type: str
    """

    film_transparent: bool
    """ World background is transparent, for compositing the render over another background

    :type: bool
    """

    filter_size: float
    """ Width over which the reconstruction filter combines samples

    :type: float
    """

    fps: int
    """ Framerate, expressed in frames per second

    :type: int
    """

    fps_base: float
    """ Framerate base

    :type: float
    """

    frame_map_new: int
    """ How many frames the Map Old will last

    :type: int
    """

    frame_map_old: int
    """ Old mapping value in frames

    :type: int
    """

    hair_subdiv: int
    """ Additional subdivision along the curves

    :type: int
    """

    hair_type: str
    """ Curves shape type

    :type: str
    """

    has_multiple_engines: bool
    """ More than one rendering engine is available

    :type: bool
    """

    image_settings: ImageFormatSettings
    """ 

    :type: ImageFormatSettings
    """

    is_movie_format: bool
    """ When true the format is a movie

    :type: bool
    """

    line_thickness: float
    """ Line thickness in pixels

    :type: float
    """

    line_thickness_mode: str
    """ Line thickness mode for Freestyle line drawing

    :type: str
    """

    metadata_input: str
    """ Where to take the metadata from

    :type: str
    """

    motion_blur_shutter: float
    """ Time taken in frames between shutter open and close

    :type: float
    """

    motion_blur_shutter_curve: CurveMapping
    """ Curve defining the shutter's openness over time

    :type: CurveMapping
    """

    pixel_aspect_x: float
    """ Horizontal aspect ratio - for anamorphic or non-square pixel output

    :type: float
    """

    pixel_aspect_y: float
    """ Vertical aspect ratio - for anamorphic or non-square pixel output

    :type: float
    """

    preview_pixel_size: str
    """ Pixel size for viewport rendering

    :type: str
    """

    resolution_percentage: int
    """ Percentage scale for render resolution

    :type: int
    """

    resolution_x: int
    """ Number of horizontal pixels in the rendered image

    :type: int
    """

    resolution_y: int
    """ Number of vertical pixels in the rendered image

    :type: int
    """

    sequencer_gl_preview: str
    """ Display method used in the sequencer view

    :type: str
    """

    simplify_child_particles: float
    """ Global child particles percentage

    :type: float
    """

    simplify_child_particles_render: float
    """ Global child particles percentage during rendering

    :type: float
    """

    simplify_gpencil: bool
    """ Simplify Grease Pencil drawing

    :type: bool
    """

    simplify_gpencil_antialiasing: bool
    """ Use Antialiasing to smooth stroke edges

    :type: bool
    """

    simplify_gpencil_modifier: bool
    """ Display modifiers

    :type: bool
    """

    simplify_gpencil_onplay: bool
    """ Simplify Grease Pencil only during animation playback

    :type: bool
    """

    simplify_gpencil_shader_fx: bool
    """ Display Shader Effects

    :type: bool
    """

    simplify_gpencil_tint: bool
    """ Display layer tint

    :type: bool
    """

    simplify_gpencil_view_fill: bool
    """ Display fill strokes in the viewport

    :type: bool
    """

    simplify_shadows: float
    """ Resolution percentage of shadows in viewport

    :type: float
    """

    simplify_shadows_render: float
    """ Resolution percentage of shadows in viewport

    :type: float
    """

    simplify_subdivision: int
    """ Global maximum subdivision level

    :type: int
    """

    simplify_subdivision_render: int
    """ Global maximum subdivision level during rendering

    :type: int
    """

    simplify_volumes: float
    """ Resolution percentage of volume objects in viewport

    :type: float
    """

    stamp_background: bpy_prop_array[float]
    """ Color to use behind stamp text

    :type: bpy_prop_array[float]
    """

    stamp_font_size: int
    """ Size of the font used when rendering stamp text

    :type: int
    """

    stamp_foreground: bpy_prop_array[float]
    """ Color to use for stamp text

    :type: bpy_prop_array[float]
    """

    stamp_note_text: str
    """ Custom text to appear in the stamp note

    :type: str
    """

    stereo_views: bpy_prop_collection[SceneRenderView]
    """ 

    :type: bpy_prop_collection[SceneRenderView]
    """

    threads: int
    """ Maximum number of CPU cores to use simultaneously while rendering (for multi-core/CPU systems)

    :type: int
    """

    threads_mode: str
    """ Determine the amount of render threads used

    :type: str
    """

    use_bake_clear: bool
    """ Clear Images before baking

    :type: bool
    """

    use_bake_lores_mesh: bool
    """ Calculate heights against unsubdivided low resolution mesh

    :type: bool
    """

    use_bake_multires: bool
    """ Bake directly from multires object

    :type: bool
    """

    use_bake_selected_to_active: bool
    """ Bake shading on the surface of selected objects to the active object

    :type: bool
    """

    use_bake_user_scale: bool
    """ Use a user scale for the derivative map

    :type: bool
    """

    use_border: bool
    """ Render a user-defined render region, within the frame size

    :type: bool
    """

    use_compositing: bool
    """ Process the render result through the compositing pipeline, if compositing nodes are enabled

    :type: bool
    """

    use_crop_to_border: bool
    """ Crop the rendered frame to the defined render region size

    :type: bool
    """

    use_file_extension: bool
    """ Add the file format extensions to the rendered file name (eg: filename + .jpg)

    :type: bool
    """

    use_freestyle: bool
    """ Draw stylized strokes using Freestyle

    :type: bool
    """

    use_high_quality_normals: bool
    """ Use high quality tangent space at the cost of lower performance

    :type: bool
    """

    use_lock_interface: bool
    """ Lock interface during rendering in favor of giving more memory to the renderer

    :type: bool
    """

    use_motion_blur: bool
    """ Use multi-sampled 3D scene motion blur

    :type: bool
    """

    use_multiview: bool
    """ Use multiple views in the scene

    :type: bool
    """

    use_overwrite: bool
    """ Overwrite existing files while rendering

    :type: bool
    """

    use_persistent_data: bool
    """ Keep render data around for faster re-renders and animation renders, at the cost of increased memory usage

    :type: bool
    """

    use_placeholder: bool
    """ Create empty placeholder files while rendering frames (similar to Unix 'touch')

    :type: bool
    """

    use_render_cache: bool
    """ Save render cache to EXR files (useful for heavy compositing, Note: affects indirectly rendered scenes)

    :type: bool
    """

    use_sequencer: bool
    """ Process the render (and composited) result through the video sequence editor pipeline, if sequencer strips exist

    :type: bool
    """

    use_sequencer_override_scene_strip: bool
    """ Use workbench render settings from the sequencer scene, instead of each individual scene used in the strip

    :type: bool
    """

    use_simplify: bool
    """ Enable simplification of scene for quicker preview renders

    :type: bool
    """

    use_simplify_normals: bool
    """ Skip computing custom normals and face corner normals for displaying meshes in the viewport

    :type: bool
    """

    use_single_layer: bool
    """ Only render the active layer. Only affects rendering from the interface, ignored for rendering from command line

    :type: bool
    """

    use_spherical_stereo: bool
    """ Active render engine supports spherical stereo rendering

    :type: bool
    """

    use_stamp: bool
    """ Render the stamp info text in the rendered image

    :type: bool
    """

    use_stamp_camera: bool
    """ Include the name of the active camera in image metadata

    :type: bool
    """

    use_stamp_date: bool
    """ Include the current date in image/video metadata

    :type: bool
    """

    use_stamp_filename: bool
    """ Include the .blend filename in image/video metadata

    :type: bool
    """

    use_stamp_frame: bool
    """ Include the frame number in image metadata

    :type: bool
    """

    use_stamp_frame_range: bool
    """ Include the rendered frame range in image/video metadata

    :type: bool
    """

    use_stamp_hostname: bool
    """ Include the hostname of the machine that rendered the frame

    :type: bool
    """

    use_stamp_labels: bool
    """ Display stamp labels ("Camera" in front of camera name, etc.)

    :type: bool
    """

    use_stamp_lens: bool
    """ Include the active camera's lens in image metadata

    :type: bool
    """

    use_stamp_marker: bool
    """ Include the name of the last marker in image metadata

    :type: bool
    """

    use_stamp_memory: bool
    """ Include the peak memory usage in image metadata

    :type: bool
    """

    use_stamp_note: bool
    """ Include a custom note in image/video metadata

    :type: bool
    """

    use_stamp_render_time: bool
    """ Include the render time in image metadata

    :type: bool
    """

    use_stamp_scene: bool
    """ Include the name of the active scene in image/video metadata

    :type: bool
    """

    use_stamp_sequencer_strip: bool
    """ Include the name of the foreground sequence strip in image metadata

    :type: bool
    """

    use_stamp_time: bool
    """ Include the rendered frame timecode as HH:MM:SS.FF in image metadata

    :type: bool
    """

    views: RenderViews
    """ 

    :type: RenderViews
    """

    views_format: str
    """ 

    :type: str
    """

    def frame_path(
        self,
        frame: typing.Any | None = -2147483648,
        preview: bool | typing.Any | None = False,
        view: str | typing.Any = "",
    ) -> str | typing.Any:
        """Return the absolute path to the filename to be written for a given frame

        :param frame: Frame number to use, if unset the current frame will be used
        :type frame: typing.Any | None
        :param preview: Preview, Use preview range
        :type preview: bool | typing.Any | None
        :param view: View, The name of the view to use to replace the "%" chars
        :type view: str | typing.Any
        :return: File Path, The resulting filepath from the scenes render settings
        :rtype: str | typing.Any
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
