import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .material import Material
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineartGpencilModifier(GpencilModifier, bpy_struct):
    """Generate line art strokes from selected source"""

    chaining_image_threshold: float
    """ Segments with an image distance smaller than this will be chained together

    :type: float
    """

    crease_threshold: float
    """ Angles smaller than this will be treated as creases. Crease angle priority: object line art crease override > mesh auto smooth angle > line art default crease

    :type: float
    """

    invert_source_vertex_group: bool
    """ Invert source vertex group values

    :type: bool
    """

    is_baked: bool
    """ This modifier has baked data

    :type: bool
    """

    level_end: int
    """ Maximum number of occlusions for the generated strokes

    :type: int
    """

    level_start: int
    """ Minimum number of occlusions for the generated strokes

    :type: int
    """

    light_contour_object: Object
    """ Use this light object to generate light contour

    :type: Object
    """

    opacity: float
    """ The strength value for the generate strokes

    :type: float
    """

    overscan: float
    """ A margin to prevent strokes from ending abruptly at the edge of the image

    :type: float
    """

    shadow_camera_far: float
    """ Far clipping distance of shadow camera

    :type: float
    """

    shadow_camera_near: float
    """ Near clipping distance of shadow camera

    :type: float
    """

    shadow_camera_size: float
    """ Represents the "Orthographic Scale" of an orthographic camera. If the camera is positioned at the light's location with this scale, it will represent the coverage of the shadow "camera"

    :type: float
    """

    shadow_region_filtering: str
    """ Select feature lines that comes from lit or shaded regions. Will not affect cast shadow and light contour since they are at the border

    :type: str
    """

    silhouette_filtering: str
    """ Select contour or silhouette

    :type: str
    """

    smooth_tolerance: float
    """ Strength of smoothing applied on jagged chains

    :type: float
    """

    source_camera: Object
    """ Use specified camera object for generating line art

    :type: Object
    """

    source_collection: Collection
    """ Generate strokes from the objects in this collection

    :type: Collection
    """

    source_object: Object
    """ Generate strokes from this object

    :type: Object
    """

    source_type: str
    """ Line art stroke source type

    :type: str
    """

    source_vertex_group: str
    """ Match the beginning of vertex group names from mesh objects, match all when left empty

    :type: str
    """

    split_angle: float
    """ Angle in screen space below which a stroke is split in two

    :type: float
    """

    stroke_depth_offset: float
    """ Move strokes slightly towards the camera to avoid clipping while preserve depth for the viewport

    :type: float
    """

    target_layer: str
    """ Grease Pencil layer to which assign the generated strokes

    :type: str
    """

    target_material: Material
    """ Grease Pencil material assigned to the generated strokes

    :type: Material
    """

    thickness: int
    """ The thickness for the generated strokes

    :type: int
    """

    use_back_face_culling: bool
    """ Remove all back faces to speed up calculation, this will create edges in different occlusion levels than when disabled

    :type: bool
    """

    use_cache: bool
    """ Use cached scene data from the first line art modifier in the stack. Certain settings will be unavailable

    :type: bool
    """

    use_clip_plane_boundaries: bool
    """ Allow lines generated by the near/far clipping plane to be shown

    :type: bool
    """

    use_contour: bool
    """ Generate strokes from contours lines

    :type: bool
    """

    use_crease: bool
    """ Generate strokes from creased edges

    :type: bool
    """

    use_crease_on_sharp: bool
    """ Allow crease to show on sharp edges

    :type: bool
    """

    use_crease_on_smooth: bool
    """ Allow crease edges to show inside smooth surfaces

    :type: bool
    """

    use_custom_camera: bool
    """ Use custom camera instead of the active camera

    :type: bool
    """

    use_detail_preserve: bool
    """ Keep the zig-zag "noise" in initial chaining

    :type: bool
    """

    use_edge_mark: bool
    """ Generate strokes from freestyle marked edges

    :type: bool
    """

    use_edge_overlap: bool
    """ Allow edges in the same location (i.e. from edge split) to show properly. May run slower

    :type: bool
    """

    use_face_mark: bool
    """ Filter feature lines using freestyle face marks

    :type: bool
    """

    use_face_mark_boundaries: bool
    """ Filter feature lines based on face mark boundaries

    :type: bool
    """

    use_face_mark_invert: bool
    """ Invert face mark filtering

    :type: bool
    """

    use_face_mark_keep_contour: bool
    """ Preserve contour lines while filtering

    :type: bool
    """

    use_fuzzy_all: bool
    """ Treat all lines as the same line type so they can be chained together

    :type: bool
    """

    use_fuzzy_intersections: bool
    """ Treat intersection and contour lines as if they were the same type so they can be chained together

    :type: bool
    """

    use_geometry_space_chain: bool
    """ Use geometry distance for chaining instead of image space

    :type: bool
    """

    use_image_boundary_trimming: bool
    """ Trim all edges right at the boundary of image (including overscan region)

    :type: bool
    """

    use_intersection: bool
    """ Generate strokes from intersections

    :type: bool
    """

    use_intersection_mask: list[bool]
    """ Mask bits to match from Collection Line Art settings

    :type: list[bool]
    """

    use_intersection_match: bool
    """ Require matching all intersection masks instead of just one

    :type: bool
    """

    use_invert_collection: bool
    """ Select everything except lines from specified collection

    :type: bool
    """

    use_invert_silhouette: bool
    """ Select anti-silhouette lines

    :type: bool
    """

    use_light_contour: bool
    """ Generate light/shadow separation lines from a reference light object

    :type: bool
    """

    use_loose: bool
    """ Generate strokes from loose edges

    :type: bool
    """

    use_loose_as_contour: bool
    """ Loose edges will have contour type

    :type: bool
    """

    use_loose_edge_chain: bool
    """ Allow loose edges to be chained together

    :type: bool
    """

    use_material: bool
    """ Generate strokes from borders between materials

    :type: bool
    """

    use_material_mask: bool
    """ Use material masks to filter out occluded strokes

    :type: bool
    """

    use_material_mask_bits: list[bool]
    """ Mask bits to match from Material Line Art settings

    :type: list[bool]
    """

    use_material_mask_match: bool
    """ Require matching all material masks instead of just one

    :type: bool
    """

    use_multiple_levels: bool
    """ Generate strokes from a range of occlusion levels

    :type: bool
    """

    use_object_instances: bool
    """ Allow particle objects and face/vertex instances to show in line art

    :type: bool
    """

    use_offset_towards_custom_camera: bool
    """ Offset strokes towards selected camera instead of the active camera

    :type: bool
    """

    use_output_vertex_group_match_by_name: bool
    """ Match output vertex group based on name

    :type: bool
    """

    use_overlap_edge_type_support: bool
    """ Allow an edge to have multiple overlapping types. This will create a separate stroke for each overlapping type

    :type: bool
    """

    use_shadow: bool
    """ Project contour lines using a light source object

    :type: bool
    """

    vertex_group: str
    """ Vertex group name for selected strokes

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