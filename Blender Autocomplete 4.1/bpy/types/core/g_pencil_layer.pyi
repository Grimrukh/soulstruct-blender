import typing
import collections.abc
import mathutils
from .g_pencil_frame import GPencilFrame
from .struct import Struct
from .bpy_struct import bpy_struct
from .grease_pencil_mask_layers import GreasePencilMaskLayers
from .object import Object
from .g_pencil_frames import GPencilFrames

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilLayer(bpy_struct):
    """Collection of related sketches"""

    active_frame: GPencilFrame
    """ Frame currently being displayed for this layer

    :type: GPencilFrame
    """

    annotation_hide: bool
    """ Set annotation Visibility

    :type: bool
    """

    annotation_onion_after_color: mathutils.Color
    """ Base color for ghosts after the active frame

    :type: mathutils.Color
    """

    annotation_onion_after_range: int
    """ Maximum number of frames to show after current frame

    :type: int
    """

    annotation_onion_before_color: mathutils.Color
    """ Base color for ghosts before the active frame

    :type: mathutils.Color
    """

    annotation_onion_before_range: int
    """ Maximum number of frames to show before current frame

    :type: int
    """

    annotation_opacity: float
    """ Annotation Layer Opacity

    :type: float
    """

    blend_mode: str
    """ Blend mode

    :type: str
    """

    channel_color: mathutils.Color
    """ Custom color for animation channel in Dopesheet

    :type: mathutils.Color
    """

    color: mathutils.Color
    """ Color for all strokes in this layer

    :type: mathutils.Color
    """

    frames: GPencilFrames
    """ Sketches for this layer on different frames

    :type: GPencilFrames
    """

    hide: bool
    """ Set layer Visibility

    :type: bool
    """

    info: str
    """ Layer name

    :type: str
    """

    is_parented: bool
    """ True when the layer parent object is set

    :type: bool
    """

    is_ruler: bool
    """ This is a special ruler layer

    :type: bool
    """

    line_change: int
    """ Thickness change to apply to current strokes (in pixels)

    :type: int
    """

    location: mathutils.Vector
    """ Values for change location

    :type: mathutils.Vector
    """

    lock: bool
    """ Protect layer from further editing and/or frame changes

    :type: bool
    """

    lock_frame: bool
    """ Lock current frame displayed by layer

    :type: bool
    """

    lock_material: bool
    """ Avoids editing locked materials in the layer

    :type: bool
    """

    mask_layers: GreasePencilMaskLayers
    """ List of Masking Layers

    :type: GreasePencilMaskLayers
    """

    matrix_inverse: mathutils.Matrix
    """ Parent inverse transformation matrix

    :type: mathutils.Matrix
    """

    matrix_inverse_layer: mathutils.Matrix
    """ Local Layer transformation inverse matrix

    :type: mathutils.Matrix
    """

    matrix_layer: mathutils.Matrix
    """ Local Layer transformation matrix

    :type: mathutils.Matrix
    """

    opacity: float
    """ Layer Opacity

    :type: float
    """

    parent: Object
    """ Parent object

    :type: Object
    """

    parent_bone: str
    """ Name of parent bone in case of a bone parenting relation

    :type: str
    """

    parent_type: str
    """ Type of parent relation

    :type: str
    """

    pass_index: int
    """ Index number for the "Layer Index" pass

    :type: int
    """

    rotation: mathutils.Euler
    """ Values for changes in rotation

    :type: mathutils.Euler
    """

    scale: mathutils.Vector
    """ Values for changes in scale

    :type: mathutils.Vector
    """

    select: bool
    """ Layer is selected for editing in the Dope Sheet

    :type: bool
    """

    show_in_front: bool
    """ Make the layer display in front of objects

    :type: bool
    """

    show_points: bool
    """ Show the points which make up the strokes (for debugging purposes)

    :type: bool
    """

    thickness: int
    """ Thickness of annotation strokes

    :type: int
    """

    tint_color: mathutils.Color
    """ Color for tinting stroke colors

    :type: mathutils.Color
    """

    tint_factor: float
    """ Factor of tinting color

    :type: float
    """

    use_annotation_onion_skinning: bool
    """ Display annotation onion skins before and after the current frame

    :type: bool
    """

    use_lights: bool
    """ Enable the use of lights on stroke and fill materials

    :type: bool
    """

    use_mask_layer: bool
    """ The visibility of drawings on this layer is affected by the layers in its masks list

    :type: bool
    """

    use_onion_skinning: bool
    """ Display onion skins before and after the current frame

    :type: bool
    """

    use_solo_mode: bool
    """ In Draw Mode only display layers with keyframe in current frame

    :type: bool
    """

    use_viewlayer_masks: bool
    """ Include the mask layers when rendering the view-layer

    :type: bool
    """

    vertex_paint_opacity: float
    """ Vertex Paint mix factor

    :type: float
    """

    viewlayer_render: str
    """ Only include Layer in this View Layer render output (leave blank to include always)

    :type: str
    """

    def clear(self):
        """Remove all the grease pencil layer data"""
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
