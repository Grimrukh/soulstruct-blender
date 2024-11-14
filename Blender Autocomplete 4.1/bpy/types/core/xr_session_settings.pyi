import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .view3_d_shading import View3DShading

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrSessionSettings(bpy_struct):
    base_pose_angle: float
    """ Rotation angle around the Z-Axis to apply the rotation deltas from the VR headset to

    :type: float
    """

    base_pose_location: mathutils.Vector
    """ Coordinates to apply translation deltas from the VR headset to

    :type: mathutils.Vector
    """

    base_pose_object: Object
    """ Object to take the location and rotation to which translation and rotation deltas from the VR headset will be applied to

    :type: Object
    """

    base_pose_type: str
    """ Define where the location and rotation for the VR view come from, to which translation and rotation deltas from the VR headset will be applied to

    :type: str
    """

    base_scale: float
    """ Uniform scale to apply to VR view

    :type: float
    """

    clip_end: float
    """ VR viewport far clipping distance

    :type: float
    """

    clip_start: float
    """ VR viewport near clipping distance

    :type: float
    """

    controller_draw_style: str
    """ Style to use when drawing VR controllers

    :type: str
    """

    icon_from_show_object_viewport: int
    """ 

    :type: int
    """

    shading: View3DShading
    """ 

    :type: View3DShading
    """

    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_controllers: bool
    """ Show VR controllers (requires VR actions for controller poses)

    :type: bool
    """

    show_custom_overlays: bool
    """ Show custom VR overlays

    :type: bool
    """

    show_floor: bool
    """ Show the ground plane grid

    :type: bool
    """

    show_object_extras: bool
    """ Show object extras, including empties, lights, and cameras

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

    show_selection: bool
    """ Show selection outlines

    :type: bool
    """

    use_absolute_tracking: bool
    """ Allow the VR tracking origin to be defined independently of the headset location

    :type: bool
    """

    use_positional_tracking: bool
    """ Allow VR headsets to affect the location in virtual space, in addition to the rotation

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
