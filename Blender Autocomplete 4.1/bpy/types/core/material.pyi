import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .tex_paint_slot import TexPaintSlot
from .struct import Struct
from .material_g_pencil_style import MaterialGPencilStyle
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .anim_data import AnimData
from .id import ID
from .image import Image
from .node_tree import NodeTree
from .material_line_art import MaterialLineArt

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")

if typing.TYPE_CHECKING:
    from io_soulstruct import *


class Material(ID, bpy_struct):
    """Material data-block to define the appearance of geometric objects for rendering"""

    # region Soulstruct Extensions
    FLVER_MATERIAL: FLVERMaterialProps
    # endregion

    alpha_threshold: float
    """ A pixel is rendered only if its alpha value is above this threshold

    :type: float
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    blend_method: str
    """ Blend Mode for Transparent Faces

    :type: str
    """

    cycles: typing.Any
    """ Cycles material settings

    :type: typing.Any
    """

    diffuse_color: bpy_prop_array[float]
    """ Diffuse color of the material

    :type: bpy_prop_array[float]
    """

    displacement_method: str
    """ Method to use for the displacement

    :type: str
    """

    grease_pencil: MaterialGPencilStyle
    """ Grease pencil color settings for material

    :type: MaterialGPencilStyle
    """

    is_grease_pencil: bool
    """ True if this material has grease pencil data

    :type: bool
    """

    lightprobe_volume_single_sided: bool
    """ Consider material single sided for light probe volume capture. Additionally helps rejecting probes inside the object to avoid light leaks

    :type: bool
    """

    line_color: bpy_prop_array[float]
    """ Line color used for Freestyle line rendering

    :type: bpy_prop_array[float]
    """

    line_priority: int
    """ The line color of a higher priority is used at material boundaries

    :type: int
    """

    lineart: MaterialLineArt
    """ Line art settings for material

    :type: MaterialLineArt
    """

    max_vertex_displacement: float
    """ The max distance a vertex can be displaced. Displacements over this threshold may cause visibility issues

    :type: float
    """

    metallic: float
    """ Amount of mirror reflection for raytrace

    :type: float
    """

    node_tree: NodeTree
    """ Node tree for node based materials

    :type: NodeTree
    """

    paint_active_slot: int
    """ Index of active texture paint slot

    :type: int
    """

    paint_clone_slot: int
    """ Index of clone texture paint slot

    :type: int
    """

    pass_index: int
    """ Index number for the "Material Index" render pass

    :type: int
    """

    preview_render_type: str
    """ Type of preview render

    :type: str
    """

    refraction_depth: float
    """ Approximate the thickness of the object to compute two refraction events (0 is disabled)

    :type: float
    """

    roughness: float
    """ Roughness of the material

    :type: float
    """

    shadow_method: str
    """ Shadow mapping method

    :type: str
    """

    show_transparent_back: bool
    """ Render multiple transparent layers (may introduce transparency sorting problems)

    :type: bool
    """

    specular_color: mathutils.Color
    """ Specular color of the material

    :type: mathutils.Color
    """

    specular_intensity: float
    """ How intense (bright) the specular reflection is

    :type: float
    """

    surface_render_method: str
    """ Controls the blending and the compatibility with certain features

    :type: str
    """

    texture_paint_images: bpy_prop_collection[Image]
    """ Texture images used for texture painting

    :type: bpy_prop_collection[Image]
    """

    texture_paint_slots: bpy_prop_collection[TexPaintSlot]
    """ Texture slots defining the mapping and influence of textures

    :type: bpy_prop_collection[TexPaintSlot]
    """

    use_backface_culling: bool
    """ Use back face culling to hide the back side of faces

    :type: bool
    """

    use_backface_culling_shadow: bool
    """ Use back face culling when casting shadows

    :type: bool
    """

    use_nodes: bool
    """ Use shader nodes to render the material

    :type: bool
    """

    use_preview_world: bool
    """ Use the current world background to light the preview render

    :type: bool
    """

    use_screen_refraction: bool
    """ Use raytracing to determine refracted color instead of using only light probes. This prevents the surface from contributing to the lighting of surfaces not using this setting

    :type: bool
    """

    use_sss_translucency: bool
    """ Add translucency effect to subsurface

    :type: bool
    """

    use_transparent_shadow: bool
    """ Use transparent shadows for this material if it contains a Transparent BSDF, disabling will render faster but not give accurate shadows

    :type: bool
    """

    volume_intersection_method: str
    """ Determines which inner part of the mesh will produce volumetric effect

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
