import typing
import collections.abc
import mathutils
from .curve_mapping import CurveMapping
from .color_ramp import ColorRamp
from .brush_curves_sculpt_settings import BrushCurvesSculptSettings
from .paint_curve import PaintCurve
from .struct import Struct
from .texture import Texture
from .brush_capabilities import BrushCapabilities
from .brush_capabilities_sculpt import BrushCapabilitiesSculpt
from .bpy_prop_array import bpy_prop_array
from .image import Image
from .bpy_struct import bpy_struct
from .brush_texture_slot import BrushTextureSlot
from .brush_capabilities_vertex_paint import BrushCapabilitiesVertexPaint
from .id import ID
from .brush_gpencil_settings import BrushGpencilSettings
from .brush_capabilities_weight_paint import BrushCapabilitiesWeightPaint
from .brush_capabilities_image_paint import BrushCapabilitiesImagePaint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Brush(ID, bpy_struct):
    """Brush data-block for storing brush settings for painting and sculpting"""

    area_radius_factor: float
    """ Ratio between the brush radius and the radius that is going to be used to sample the area center

    :type: float
    """

    auto_smooth_factor: float
    """ Amount of smoothing to automatically apply to each stroke

    :type: float
    """

    automasking_boundary_edges_propagation_steps: int
    """ Distance where boundary edge automasking is going to protect vertices from the fully masked edge

    :type: int
    """

    automasking_cavity_blur_steps: int
    """ The number of times the cavity mask is blurred

    :type: int
    """

    automasking_cavity_curve: CurveMapping
    """ Curve used for the sensitivity

    :type: CurveMapping
    """

    automasking_cavity_factor: float
    """ The contrast of the cavity mask

    :type: float
    """

    automasking_start_normal_falloff: float
    """ Extend the angular range with a falloff gradient

    :type: float
    """

    automasking_start_normal_limit: float
    """ The range of angles that will be affected

    :type: float
    """

    automasking_view_normal_falloff: float
    """ Extend the angular range with a falloff gradient

    :type: float
    """

    automasking_view_normal_limit: float
    """ The range of angles that will be affected

    :type: float
    """

    blend: str
    """ Brush blending mode

    :type: str
    """

    blur_kernel_radius: int
    """ Radius of kernel used for soften and sharpen in pixels

    :type: int
    """

    blur_mode: str
    """ 

    :type: str
    """

    boundary_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    boundary_falloff_type: str
    """ How the brush falloff is applied across the boundary

    :type: str
    """

    boundary_offset: float
    """ Offset of the boundary origin in relation to the brush radius

    :type: float
    """

    brush_capabilities: BrushCapabilities
    """ Brush's capabilities

    :type: BrushCapabilities
    """

    clone_alpha: float
    """ Opacity of clone image display

    :type: float
    """

    clone_image: Image
    """ Image for clone tool

    :type: Image
    """

    clone_offset: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    cloth_constraint_softbody_strength: float
    """ How much the cloth preserves the original shape, acting as a soft body

    :type: float
    """

    cloth_damping: float
    """ How much the applied forces are propagated through the cloth

    :type: float
    """

    cloth_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    cloth_force_falloff_type: str
    """ Shape used in the brush to apply force to the cloth

    :type: str
    """

    cloth_mass: float
    """ Mass of each simulation particle

    :type: float
    """

    cloth_sim_falloff: float
    """ Area to apply deformation falloff to the effects of the simulation

    :type: float
    """

    cloth_sim_limit: float
    """ Factor added relative to the size of the radius to limit the cloth simulation effects

    :type: float
    """

    cloth_simulation_area_type: str
    """ Part of the mesh that is going to be simulated when the stroke is active

    :type: str
    """

    color: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    color_type: str
    """ Use single color or gradient when painting

    :type: str
    """

    crease_pinch_factor: float
    """ How much the crease brush pinches

    :type: float
    """

    cursor_color_add: bpy_prop_array[float]
    """ Color of cursor when adding

    :type: bpy_prop_array[float]
    """

    cursor_color_subtract: bpy_prop_array[float]
    """ Color of cursor when subtracting

    :type: bpy_prop_array[float]
    """

    cursor_overlay_alpha: int
    """ 

    :type: int
    """

    curve: CurveMapping
    """ Editable falloff curve

    :type: CurveMapping
    """

    curve_preset: str
    """ 

    :type: str
    """

    curves_sculpt_settings: BrushCurvesSculptSettings
    """ 

    :type: BrushCurvesSculptSettings
    """

    curves_sculpt_tool: str
    """ 

    :type: str
    """

    dash_ratio: float
    """ Ratio of samples in a cycle that the brush is enabled

    :type: float
    """

    dash_samples: int
    """ Length of a dash cycle measured in stroke samples

    :type: int
    """

    deform_target: str
    """ How the deformation of the brush will affect the object

    :type: str
    """

    density: float
    """ Amount of random elements that are going to be affected by the brush

    :type: float
    """

    direction: str
    """ 

    :type: str
    """

    disconnected_distance_max: float
    """ Maximum distance to search for disconnected loose parts in the mesh

    :type: float
    """

    elastic_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    elastic_deform_volume_preservation: float
    """ Poisson ratio for elastic deformation. Higher values preserve volume more, but also lead to more bulging

    :type: float
    """

    falloff_angle: float
    """ Paint most on faces pointing towards the view according to this angle

    :type: float
    """

    falloff_shape: str
    """ Use projected or spherical falloff

    :type: str
    """

    fill_threshold: float
    """ Threshold above which filling is not propagated

    :type: float
    """

    flow: float
    """ Amount of paint that is applied per stroke sample

    :type: float
    """

    gpencil_sculpt_tool: str
    """ 

    :type: str
    """

    gpencil_settings: BrushGpencilSettings
    """ 

    :type: BrushGpencilSettings
    """

    gpencil_tool: str
    """ 

    :type: str
    """

    gpencil_vertex_tool: str
    """ 

    :type: str
    """

    gpencil_weight_tool: str
    """ 

    :type: str
    """

    grad_spacing: int
    """ Spacing before brush gradient goes full circle

    :type: int
    """

    gradient: ColorRamp
    """ 

    :type: ColorRamp
    """

    gradient_fill_mode: str
    """ 

    :type: str
    """

    gradient_stroke_mode: str
    """ 

    :type: str
    """

    hardness: float
    """ How close the brush falloff starts from the edge of the brush

    :type: float
    """

    height: float
    """ Affectable height of brush (layer height for layer tool, i.e.)

    :type: float
    """

    icon_filepath: str
    """ File path to brush icon

    :type: str
    """

    image_paint_capabilities: BrushCapabilitiesImagePaint
    """ 

    :type: BrushCapabilitiesImagePaint
    """

    image_tool: str
    """ 

    :type: str
    """

    input_samples: int
    """ Number of input samples to average together to smooth the brush stroke

    :type: int
    """

    invert_density_pressure: bool
    """ Invert the modulation of pressure in density

    :type: bool
    """

    invert_flow_pressure: bool
    """ Invert the modulation of pressure in flow

    :type: bool
    """

    invert_hardness_pressure: bool
    """ Invert the modulation of pressure in hardness

    :type: bool
    """

    invert_to_scrape_fill: bool
    """ Use Scrape or Fill tool when inverting this brush instead of inverting its displacement direction

    :type: bool
    """

    invert_wet_mix_pressure: bool
    """ Invert the modulation of pressure in wet mix

    :type: bool
    """

    invert_wet_persistence_pressure: bool
    """ Invert the modulation of pressure in wet persistence

    :type: bool
    """

    jitter: float
    """ Jitter the position of the brush while painting

    :type: float
    """

    jitter_absolute: int
    """ Jitter the position of the brush in pixels while painting

    :type: int
    """

    jitter_unit: str
    """ Jitter in screen space or relative to brush size

    :type: str
    """

    mask_overlay_alpha: int
    """ 

    :type: int
    """

    mask_stencil_dimension: mathutils.Vector
    """ Dimensions of mask stencil in viewport

    :type: mathutils.Vector
    """

    mask_stencil_pos: mathutils.Vector
    """ Position of mask stencil in viewport

    :type: mathutils.Vector
    """

    mask_texture: Texture
    """ 

    :type: Texture
    """

    mask_texture_slot: BrushTextureSlot
    """ 

    :type: BrushTextureSlot
    """

    mask_tool: str
    """ 

    :type: str
    """

    multiplane_scrape_angle: float
    """ Angle between the planes of the crease

    :type: float
    """

    normal_radius_factor: float
    """ Ratio between the brush radius and the radius that is going to be used to sample the normal

    :type: float
    """

    normal_weight: float
    """ How much grab will pull vertices out of surface during a grab

    :type: float
    """

    paint_curve: PaintCurve
    """ Active paint curve

    :type: PaintCurve
    """

    plane_offset: float
    """ Adjust plane on which the brush acts towards or away from the object surface

    :type: float
    """

    plane_trim: float
    """ If a vertex is further away from offset plane than this, then it is not affected

    :type: float
    """

    pose_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    pose_ik_segments: int
    """ Number of segments of the inverse kinematics chain that will deform the mesh

    :type: int
    """

    pose_offset: float
    """ Offset of the pose origin in relation to the brush radius

    :type: float
    """

    pose_origin_type: str
    """ Method to set the rotation origins for the segments of the brush

    :type: str
    """

    pose_smooth_iterations: int
    """ Smooth iterations applied after calculating the pose factor of each vertex

    :type: int
    """

    rake_factor: float
    """ How much grab will follow cursor rotation

    :type: float
    """

    rate: float
    """ Interval between paints for Airbrush

    :type: float
    """

    sculpt_capabilities: BrushCapabilitiesSculpt
    """ 

    :type: BrushCapabilitiesSculpt
    """

    sculpt_plane: str
    """ 

    :type: str
    """

    sculpt_tool: str
    """ 

    :type: str
    """

    secondary_color: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    sharp_threshold: float
    """ Threshold below which, no sharpening is done

    :type: float
    """

    show_multiplane_scrape_planes_preview: bool
    """ Preview the scrape planes in the cursor during the stroke

    :type: bool
    """

    size: int
    """ Radius of the brush in pixels

    :type: int
    """

    slide_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    smear_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    smooth_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    smooth_stroke_factor: float
    """ Higher values give a smoother stroke

    :type: float
    """

    smooth_stroke_radius: int
    """ Minimum distance from last point before stroke continues

    :type: int
    """

    snake_hook_deform_type: str
    """ Deformation type that is used in the brush

    :type: str
    """

    spacing: int
    """ Spacing between brush daubs as a percentage of brush diameter

    :type: int
    """

    stencil_dimension: mathutils.Vector
    """ Dimensions of stencil in viewport

    :type: mathutils.Vector
    """

    stencil_pos: mathutils.Vector
    """ Position of stencil in viewport

    :type: mathutils.Vector
    """

    strength: float
    """ How powerful the effect of the brush is when applied

    :type: float
    """

    stroke_method: str
    """ 

    :type: str
    """

    surface_smooth_current_vertex: float
    """ How much the position of each individual vertex influences the final result

    :type: float
    """

    surface_smooth_iterations: int
    """ Number of smoothing iterations per brush step

    :type: int
    """

    surface_smooth_shape_preservation: float
    """ How much of the original shape is preserved when smoothing

    :type: float
    """

    texture: Texture
    """ 

    :type: Texture
    """

    texture_overlay_alpha: int
    """ 

    :type: int
    """

    texture_sample_bias: float
    """ Value added to texture samples

    :type: float
    """

    texture_slot: BrushTextureSlot
    """ 

    :type: BrushTextureSlot
    """

    tilt_strength_factor: float
    """ How much the tilt of the pen will affect the brush

    :type: float
    """

    tip_roundness: float
    """ Roundness of the brush tip

    :type: float
    """

    tip_scale_x: float
    """ Scale of the brush tip in the X axis

    :type: float
    """

    topology_rake_factor: float
    """ Automatically align edges to the brush direction to generate cleaner topology and define sharp features. Best used on low-poly meshes as it has a performance impact

    :type: float
    """

    unprojected_radius: float
    """ Radius of brush in Blender units

    :type: float
    """

    use_accumulate: bool
    """ Accumulate stroke daubs on top of each other

    :type: bool
    """

    use_adaptive_space: bool
    """ Space daubs according to surface orientation instead of screen space

    :type: bool
    """

    use_airbrush: bool
    """ Keep applying paint effect while holding mouse (spray)

    :type: bool
    """

    use_alpha: bool
    """ When this is disabled, lock alpha while painting

    :type: bool
    """

    use_anchor: bool
    """ Keep the brush anchored to the initial location

    :type: bool
    """

    use_automasking_boundary_edges: bool
    """ Do not affect non manifold boundary edges

    :type: bool
    """

    use_automasking_boundary_face_sets: bool
    """ Do not affect vertices that belong to a Face Set boundary

    :type: bool
    """

    use_automasking_cavity: bool
    """ Do not affect vertices on peaks, based on the surface curvature

    :type: bool
    """

    use_automasking_cavity_inverted: bool
    """ Do not affect vertices within crevices, based on the surface curvature

    :type: bool
    """

    use_automasking_custom_cavity_curve: bool
    """ Use custom curve

    :type: bool
    """

    use_automasking_face_sets: bool
    """ Affect only vertices that share Face Sets with the active vertex

    :type: bool
    """

    use_automasking_start_normal: bool
    """ Affect only vertices with a similar normal to where the stroke starts

    :type: bool
    """

    use_automasking_topology: bool
    """ Affect only vertices connected to the active vertex under the brush

    :type: bool
    """

    use_automasking_view_normal: bool
    """ Affect only vertices with a normal that faces the viewer

    :type: bool
    """

    use_automasking_view_occlusion: bool
    """ Only affect vertices that are not occluded by other faces. (Slower performance)

    :type: bool
    """

    use_cloth_collision: bool
    """ Collide with objects during the simulation

    :type: bool
    """

    use_cloth_pin_simulation_boundary: bool
    """ Lock the position of the vertices in the simulation falloff area to avoid artifacts and create a softer transition with unaffected areas

    :type: bool
    """

    use_color_as_displacement: bool
    """ Handles each pixel color as individual vector for displacement. Works only with area plane mapping

    :type: bool
    """

    use_connected_only: bool
    """ Affect only topologically connected elements

    :type: bool
    """

    use_cursor_overlay: bool
    """ Show cursor in viewport

    :type: bool
    """

    use_cursor_overlay_override: bool
    """ Don't show overlay during a stroke

    :type: bool
    """

    use_curve: bool
    """ Define the stroke curve with a Bézier curve. Dabs are separated according to spacing

    :type: bool
    """

    use_custom_icon: bool
    """ Set the brush icon from an image file

    :type: bool
    """

    use_density_pressure: bool
    """ Use pressure to modulate density

    :type: bool
    """

    use_edge_to_edge: bool
    """ Drag anchor brush from edge-to-edge

    :type: bool
    """

    use_flow_pressure: bool
    """ Use pressure to modulate flow

    :type: bool
    """

    use_frontface: bool
    """ Brush only affects vertices that face the viewer

    :type: bool
    """

    use_frontface_falloff: bool
    """ Blend brush influence by how much they face the front

    :type: bool
    """

    use_grab_active_vertex: bool
    """ Apply the maximum grab strength to the active vertex instead of the cursor location

    :type: bool
    """

    use_grab_silhouette: bool
    """ Grabs trying to automask the silhouette of the object

    :type: bool
    """

    use_hardness_pressure: bool
    """ Use pressure to modulate hardness

    :type: bool
    """

    use_inverse_smooth_pressure: bool
    """ Lighter pressure causes more smoothing to be applied

    :type: bool
    """

    use_line: bool
    """ Draw a line with dabs separated according to spacing

    :type: bool
    """

    use_locked_size: str
    """ Measure brush size relative to the view or the scene

    :type: str
    """

    use_multiplane_scrape_dynamic: bool
    """ The angle between the planes changes during the stroke to fit the surface under the cursor

    :type: bool
    """

    use_offset_pressure: bool
    """ Enable tablet pressure sensitivity for offset

    :type: bool
    """

    use_original_normal: bool
    """ When locked keep using normal of surface where stroke was initiated

    :type: bool
    """

    use_original_plane: bool
    """ When locked keep using the plane origin of surface where stroke was initiated

    :type: bool
    """

    use_paint_antialiasing: bool
    """ Smooths the edges of the strokes

    :type: bool
    """

    use_paint_grease_pencil: bool
    """ Use this brush in grease pencil drawing mode

    :type: bool
    """

    use_paint_image: bool
    """ Use this brush in texture paint mode

    :type: bool
    """

    use_paint_sculpt: bool
    """ Use this brush in sculpt mode

    :type: bool
    """

    use_paint_sculpt_curves: bool
    """ Use this brush in sculpt curves mode

    :type: bool
    """

    use_paint_uv_sculpt: bool
    """ Use this brush in UV sculpt mode

    :type: bool
    """

    use_paint_vertex: bool
    """ Use this brush in vertex paint mode

    :type: bool
    """

    use_paint_weight: bool
    """ Use this brush in weight paint mode

    :type: bool
    """

    use_persistent: bool
    """ Sculpt on a persistent layer of the mesh

    :type: bool
    """

    use_plane_trim: bool
    """ Limit the distance from the offset plane that a vertex can be affected

    :type: bool
    """

    use_pose_ik_anchored: bool
    """ Keep the position of the last segment in the IK chain fixed

    :type: bool
    """

    use_pose_lock_rotation: bool
    """ Do not rotate the segment when using the scale deform mode

    :type: bool
    """

    use_pressure_area_radius: bool
    """ Enable tablet pressure sensitivity for area radius

    :type: bool
    """

    use_pressure_jitter: bool
    """ Enable tablet pressure sensitivity for jitter

    :type: bool
    """

    use_pressure_masking: str
    """ Pen pressure makes texture influence smaller

    :type: str
    """

    use_pressure_size: bool
    """ Enable tablet pressure sensitivity for size

    :type: bool
    """

    use_pressure_spacing: bool
    """ Enable tablet pressure sensitivity for spacing

    :type: bool
    """

    use_pressure_strength: bool
    """ Enable tablet pressure sensitivity for strength

    :type: bool
    """

    use_primary_overlay: bool
    """ Show texture in viewport

    :type: bool
    """

    use_primary_overlay_override: bool
    """ Don't show overlay during a stroke

    :type: bool
    """

    use_restore_mesh: bool
    """ Allow a single dot to be carefully positioned

    :type: bool
    """

    use_scene_spacing: str
    """ Calculate the brush spacing using view or scene distance

    :type: str
    """

    use_secondary_overlay: bool
    """ Show texture in viewport

    :type: bool
    """

    use_secondary_overlay_override: bool
    """ Don't show overlay during a stroke

    :type: bool
    """

    use_smooth_stroke: bool
    """ Brush lags behind mouse and follows a smoother path

    :type: bool
    """

    use_space: bool
    """ Limit brush application to the distance specified by spacing

    :type: bool
    """

    use_space_attenuation: bool
    """ Automatically adjust strength to give consistent results for different spacings

    :type: bool
    """

    use_vertex_grease_pencil: bool
    """ Use this brush in grease pencil vertex color mode

    :type: bool
    """

    use_wet_mix_pressure: bool
    """ Use pressure to modulate wet mix

    :type: bool
    """

    use_wet_persistence_pressure: bool
    """ Use pressure to modulate wet persistence

    :type: bool
    """

    uv_sculpt_tool: str
    """ 

    :type: str
    """

    vertex_paint_capabilities: BrushCapabilitiesVertexPaint
    """ 

    :type: BrushCapabilitiesVertexPaint
    """

    vertex_tool: str
    """ 

    :type: str
    """

    weight: float
    """ Vertex weight when brush is applied

    :type: float
    """

    weight_paint_capabilities: BrushCapabilitiesWeightPaint
    """ 

    :type: BrushCapabilitiesWeightPaint
    """

    weight_tool: str
    """ 

    :type: str
    """

    wet_mix: float
    """ Amount of paint that is picked from the surface into the brush color

    :type: float
    """

    wet_paint_radius_factor: float
    """ Ratio between the brush radius and the radius that is going to be used to sample the color to blend in wet paint

    :type: float
    """

    wet_persistence: float
    """ Amount of wet paint that stays in the brush after applying paint to the surface

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
