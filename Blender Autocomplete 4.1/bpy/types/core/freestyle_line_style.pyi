import typing
import collections.abc
import mathutils
from .line_style_geometry_modifiers import LineStyleGeometryModifiers
from .line_style_color_modifiers import LineStyleColorModifiers
from .line_style_thickness_modifiers import LineStyleThicknessModifiers
from .struct import Struct
from .line_style_texture_slots import LineStyleTextureSlots
from .bpy_struct import bpy_struct
from .id import ID
from .anim_data import AnimData
from .texture import Texture
from .line_style_alpha_modifiers import LineStyleAlphaModifiers
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FreestyleLineStyle(ID, bpy_struct):
    """Freestyle line style, reusable by multiple line sets"""

    active_texture: Texture | None
    """ Active texture slot being displayed

    :type: Texture | None
    """

    active_texture_index: int | None
    """ Index of active texture slot

    :type: int | None
    """

    alpha: float
    """ Base alpha transparency, possibly modified by alpha transparency modifiers

    :type: float
    """

    alpha_modifiers: LineStyleAlphaModifiers
    """ List of alpha transparency modifiers

    :type: LineStyleAlphaModifiers
    """

    angle_max: float
    """ Maximum 2D angle for splitting chains

    :type: float
    """

    angle_min: float
    """ Minimum 2D angle for splitting chains

    :type: float
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    caps: str
    """ Select the shape of both ends of strokes

    :type: str
    """

    chain_count: int
    """ Chain count for the selection of first N chains

    :type: int
    """

    chaining: str
    """ Select the way how feature edges are jointed to form chains

    :type: str
    """

    color: mathutils.Color
    """ Base line color, possibly modified by line color modifiers

    :type: mathutils.Color
    """

    color_modifiers: LineStyleColorModifiers
    """ List of line color modifiers

    :type: LineStyleColorModifiers
    """

    dash1: int
    """ Length of the 1st dash for dashed lines

    :type: int
    """

    dash2: int
    """ Length of the 2nd dash for dashed lines

    :type: int
    """

    dash3: int
    """ Length of the 3rd dash for dashed lines

    :type: int
    """

    gap1: int
    """ Length of the 1st gap for dashed lines

    :type: int
    """

    gap2: int
    """ Length of the 2nd gap for dashed lines

    :type: int
    """

    gap3: int
    """ Length of the 3rd gap for dashed lines

    :type: int
    """

    geometry_modifiers: LineStyleGeometryModifiers
    """ List of stroke geometry modifiers

    :type: LineStyleGeometryModifiers
    """

    integration_type: str
    """ Select the way how the sort key is computed for each chain

    :type: str
    """

    length_max: float
    """ Maximum curvilinear 2D length for the selection of chains

    :type: float
    """

    length_min: float
    """ Minimum curvilinear 2D length for the selection of chains

    :type: float
    """

    material_boundary: bool
    """ If true, chains of feature edges are split at material boundaries

    :type: bool
    """

    node_tree: NodeTree
    """ Node tree for node-based shaders

    :type: NodeTree
    """

    panel: str
    """ Select the property panel to be shown

    :type: str
    """

    rounds: int
    """ Number of rounds in a sketchy multiple touch

    :type: int
    """

    sort_key: str
    """ Select the sort key to determine the stacking order of chains

    :type: str
    """

    sort_order: str
    """ Select the sort order

    :type: str
    """

    split_dash1: int
    """ Length of the 1st dash for splitting

    :type: int
    """

    split_dash2: int
    """ Length of the 2nd dash for splitting

    :type: int
    """

    split_dash3: int
    """ Length of the 3rd dash for splitting

    :type: int
    """

    split_gap1: int
    """ Length of the 1st gap for splitting

    :type: int
    """

    split_gap2: int
    """ Length of the 2nd gap for splitting

    :type: int
    """

    split_gap3: int
    """ Length of the 3rd gap for splitting

    :type: int
    """

    split_length: float
    """ Curvilinear 2D length for chain splitting

    :type: float
    """

    texture_slots: LineStyleTextureSlots
    """ Texture slots defining the mapping and influence of textures

    :type: LineStyleTextureSlots
    """

    texture_spacing: float
    """ Spacing for textures along stroke length

    :type: float
    """

    thickness: float
    """ Base line thickness, possibly modified by line thickness modifiers

    :type: float
    """

    thickness_modifiers: LineStyleThicknessModifiers
    """ List of line thickness modifiers

    :type: LineStyleThicknessModifiers
    """

    thickness_position: str
    """ Thickness position of silhouettes and border edges (applicable when plain chaining is used with the Same Object option)

    :type: str
    """

    thickness_ratio: float
    """ A number between 0 (inside) and 1 (outside) specifying the relative position of stroke thickness

    :type: float
    """

    use_angle_max: bool
    """ Split chains at points with angles larger than the maximum 2D angle

    :type: bool
    """

    use_angle_min: bool
    """ Split chains at points with angles smaller than the minimum 2D angle

    :type: bool
    """

    use_chain_count: bool
    """ Enable the selection of first N chains

    :type: bool
    """

    use_chaining: bool
    """ Enable chaining of feature edges

    :type: bool
    """

    use_dashed_line: bool
    """ Enable or disable dashed line

    :type: bool
    """

    use_length_max: bool
    """ Enable the selection of chains by a maximum 2D length

    :type: bool
    """

    use_length_min: bool
    """ Enable the selection of chains by a minimum 2D length

    :type: bool
    """

    use_nodes: bool
    """ Use shader nodes for the line style

    :type: bool
    """

    use_same_object: bool
    """ If true, only feature edges of the same object are joined

    :type: bool
    """

    use_sorting: bool
    """ Arrange the stacking order of strokes

    :type: bool
    """

    use_split_length: bool
    """ Enable chain splitting by curvilinear 2D length

    :type: bool
    """

    use_split_pattern: bool
    """ Enable chain splitting by dashed line patterns

    :type: bool
    """

    use_texture: bool
    """ Enable or disable textured strokes

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
