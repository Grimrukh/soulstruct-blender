import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class View3DOverlay(bpy_struct):
    """Settings for display of overlays in the 3D viewport"""

    bone_wire_alpha: float
    """ Maximum opacity of bones in wireframe display mode

    :type: float
    """

    display_handle: str
    """ Limit the display of curve handles in edit mode

    :type: str
    """

    fade_inactive_alpha: float
    """ Strength of the fade effect

    :type: float
    """

    gpencil_fade_layer: float
    """ Fade layer opacity for Grease Pencil layers except the active one

    :type: float
    """

    gpencil_fade_objects: float
    """ Fade factor

    :type: float
    """

    gpencil_grid_opacity: float
    """ Canvas grid opacity

    :type: float
    """

    gpencil_vertex_paint_opacity: float
    """ Vertex Paint mix factor

    :type: float
    """

    grid_lines: int
    """ Number of grid lines to display in perspective view

    :type: int
    """

    grid_scale: float
    """ Multiplier for the distance between 3D View grid lines

    :type: float
    """

    grid_scale_unit: float
    """ Grid cell size scaled by scene unit system settings

    :type: float
    """

    grid_subdivisions: int
    """ Number of subdivisions between grid lines

    :type: int
    """

    normals_constant_screen_size: float
    """ Screen size for normals in the 3D view

    :type: float
    """

    normals_length: float
    """ Display size for normals in the 3D view

    :type: float
    """

    retopology_offset: float
    """ Offset used to draw edit mesh in front of other geometry

    :type: float
    """

    sculpt_curves_cage_opacity: float
    """ Opacity of the cage overlay in curves sculpt mode

    :type: float
    """

    sculpt_mode_face_sets_opacity: float
    """ 

    :type: float
    """

    sculpt_mode_mask_opacity: float
    """ 

    :type: float
    """

    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_axis_x: bool
    """ Show the X axis line

    :type: bool
    """

    show_axis_y: bool
    """ Show the Y axis line

    :type: bool
    """

    show_axis_z: bool
    """ Show the Z axis line

    :type: bool
    """

    show_bones: bool
    """ Display bones (disable to show motion paths only)

    :type: bool
    """

    show_cursor: bool
    """ Display 3D Cursor Overlay

    :type: bool
    """

    show_curve_normals: bool
    """ Display 3D curve normals in editmode

    :type: bool
    """

    show_edge_bevel_weight: bool
    """ Display weights created for the Bevel modifier

    :type: bool
    """

    show_edge_crease: bool
    """ Display creases created for Subdivision Surface modifier

    :type: bool
    """

    show_edge_seams: bool
    """ Display UV unwrapping seams

    :type: bool
    """

    show_edge_sharp: bool
    """ Display sharp edges, used with the Edge Split modifier

    :type: bool
    """

    show_extra_edge_angle: bool
    """ Display selected edge angle, using global values when set in the transform panel

    :type: bool
    """

    show_extra_edge_length: bool
    """ Display selected edge lengths, using global values when set in the transform panel

    :type: bool
    """

    show_extra_face_angle: bool
    """ Display the angles in the selected edges, using global values when set in the transform panel

    :type: bool
    """

    show_extra_face_area: bool
    """ Display the area of selected faces, using global values when set in the transform panel

    :type: bool
    """

    show_extra_indices: bool
    """ Display the index numbers of selected vertices, edges, and faces

    :type: bool
    """

    show_extras: bool
    """ Object details, including empty wire, cameras and other visual guides

    :type: bool
    """

    show_face_center: bool
    """ Display face center when face selection is enabled in solid shading modes

    :type: bool
    """

    show_face_normals: bool
    """ Display face normals as lines

    :type: bool
    """

    show_face_orientation: bool
    """ Show the Face Orientation Overlay

    :type: bool
    """

    show_faces: bool
    """ Highlight selected faces

    :type: bool
    """

    show_fade_inactive: bool
    """ Fade inactive geometry using the viewport background color

    :type: bool
    """

    show_floor: bool
    """ Show the ground plane grid

    :type: bool
    """

    show_freestyle_edge_marks: bool
    """ Display Freestyle edge marks, used with the Freestyle renderer

    :type: bool
    """

    show_freestyle_face_marks: bool
    """ Display Freestyle face marks, used with the Freestyle renderer

    :type: bool
    """

    show_light_colors: bool
    """ Show light colors

    :type: bool
    """

    show_look_dev: bool
    """ Show HDRI preview spheres

    :type: bool
    """

    show_motion_paths: bool
    """ Show the Motion Paths Overlay

    :type: bool
    """

    show_object_origins: bool
    """ Show object center dots

    :type: bool
    """

    show_object_origins_all: bool
    """ Show the object origin center dot for all (selected and unselected) objects

    :type: bool
    """

    show_onion_skins: bool
    """ Show the Onion Skinning Overlay

    :type: bool
    """

    show_ortho_grid: bool
    """ Show grid in orthographic side view

    :type: bool
    """

    show_outline_selected: bool
    """ Show an outline highlight around selected objects

    :type: bool
    """

    show_overlays: bool
    """ Display overlays like gizmos and outlines

    :type: bool
    """

    show_paint_wire: bool
    """ Use wireframe display in painting modes

    :type: bool
    """

    show_relationship_lines: bool
    """ Show dashed lines indicating parent or constraint relationships

    :type: bool
    """

    show_retopology: bool
    """ Hide the solid mesh and offset the overlay towards the view. Selection is occluded by inactive geometry, unless X-Ray is enabled

    :type: bool
    """

    show_sculpt_curves_cage: bool
    """ Show original curves that are currently being edited

    :type: bool
    """

    show_sculpt_face_sets: bool
    """ 

    :type: bool
    """

    show_sculpt_mask: bool
    """ 

    :type: bool
    """

    show_split_normals: bool
    """ Display vertex-per-face normals as lines

    :type: bool
    """

    show_stats: bool
    """ Display scene statistics overlay text

    :type: bool
    """

    show_statvis: bool
    """ Display statistical information about the mesh

    :type: bool
    """

    show_text: bool
    """ Display overlay text

    :type: bool
    """

    show_vertex_normals: bool
    """ Display vertex normals as lines

    :type: bool
    """

    show_viewer_attribute: bool
    """ Show attribute overlay for active viewer node

    :type: bool
    """

    show_viewer_text: bool
    """ Show attribute values as text in viewport

    :type: bool
    """

    show_weight: bool
    """ Display weights in editmode

    :type: bool
    """

    show_wireframes: bool
    """ Show face edges wires

    :type: bool
    """

    show_wpaint_contours: bool
    """ Show contour lines formed by points with the same interpolated weight

    :type: bool
    """

    show_xray_bone: bool
    """ Show the bone selection overlay

    :type: bool
    """

    texture_paint_mode_opacity: float
    """ Opacity of the texture paint mode stencil mask overlay

    :type: float
    """

    use_debug_freeze_view_culling: bool
    """ Freeze view culling bounds

    :type: bool
    """

    use_gpencil_canvas_xray: bool
    """ Show Canvas grid in front

    :type: bool
    """

    use_gpencil_edit_lines: bool
    """ Show Edit Lines when editing strokes

    :type: bool
    """

    use_gpencil_fade_gp_objects: bool
    """ Fade Grease Pencil Objects, except the active one

    :type: bool
    """

    use_gpencil_fade_layers: bool
    """ Toggle fading of Grease Pencil layers except the active one

    :type: bool
    """

    use_gpencil_fade_objects: bool
    """ Fade all viewport objects with a full color layer to improve visibility

    :type: bool
    """

    use_gpencil_grid: bool
    """ Display a grid over grease pencil paper

    :type: bool
    """

    use_gpencil_multiedit_line_only: bool
    """ Show Edit Lines only in multiframe

    :type: bool
    """

    use_gpencil_onion_skin: bool
    """ Show ghosts of the keyframes before and after the current frame

    :type: bool
    """

    use_gpencil_show_directions: bool
    """ Show stroke drawing direction with a bigger green dot (start) and smaller red dot (end) points

    :type: bool
    """

    use_gpencil_show_material_name: bool
    """ Show material name assigned to each stroke

    :type: bool
    """

    use_normals_constant_screen_size: bool
    """ Keep size of normals constant in relation to 3D view

    :type: bool
    """

    vertex_opacity: float
    """ Opacity for edit vertices

    :type: float
    """

    vertex_paint_mode_opacity: float
    """ Opacity of the texture paint mode stencil mask overlay

    :type: float
    """

    viewer_attribute_opacity: float
    """ Opacity of the attribute that is currently visualized

    :type: float
    """

    weight_paint_mode_opacity: float
    """ Opacity of the weight paint mode overlay

    :type: float
    """

    wireframe_opacity: float
    """ Opacity of the displayed edges (1.0 for opaque)

    :type: float
    """

    wireframe_threshold: float
    """ Adjust the angle threshold for displaying edges (1.0 for all)

    :type: float
    """

    xray_alpha_bone: float
    """ Opacity to use for bone selection

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
