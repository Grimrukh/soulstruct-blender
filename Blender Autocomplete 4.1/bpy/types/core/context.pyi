import typing
import collections.abc
import mathutils
from .dynamic_paint_modifier import DynamicPaintModifier
from .blend_data import BlendData
from .region import Region
from .edit_bone import EditBone
from .nla_track import NlaTrack
from .sequence import Sequence
from .ui_list import UIList
from .brush import Brush
from .asset_library_reference import AssetLibraryReference
from .text import Text
from .bone import Bone
from .world import World
from .movie_tracking_track import MovieTrackingTrack
from .screen import Screen
from .mask import Mask
from .space import Space
from .mesh import Mesh
from .speaker import Speaker
from .material_slot import MaterialSlot
from .light_probe import LightProbe
from .struct import Struct
from .texture_slot import TextureSlot
from .particle_settings import ParticleSettings
from .property import Property
from .pose_bone import PoseBone
from .grease_pencil import GreasePencil
from .gizmo_group import GizmoGroup
from .asset_representation import AssetRepresentation
from .texture import Texture
from .window_manager import WindowManager
from .cloth_modifier import ClothModifier
from .operator import Operator
from .layer_collection import LayerCollection
from .scene import Scene
from .g_pencil_stroke import GPencilStroke
from .nla_strip import NlaStrip
from .depsgraph import Depsgraph
from .region_view3_d import RegionView3D
from .meta_ball import MetaBall
from .g_pencil_layer import GPencilLayer
from .material import Material
from .particle_system import ParticleSystem
from .area import Area
from .window import Window
from .work_space import WorkSpace
from .object import Object
from .curve import Curve
from .movie_clip import MovieClip
from .image import Image
from .keyframe import Keyframe
from .file_select_entry import FileSelectEntry
from .soft_body_modifier import SoftBodyModifier
from .freestyle_line_style import FreestyleLineStyle
from .action import Action
from .f_curve import FCurve
from .tool_settings import ToolSettings
from .collection import Collection
from .camera import Camera
from .bpy_struct import bpy_struct
from .volume import Volume
from .preferences import Preferences
from .node import Node
from .light import Light
from .id import ID
from .any_type import AnyType
from .armature import Armature
from .view_layer import ViewLayer
from .collision_modifier import CollisionModifier
from .lattice import Lattice

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Context(bpy_struct):
    """Current windowmanager and data context"""

    area: Area
    """ 

    :type: Area
    """

    asset: AssetRepresentation
    """ 

    :type: AssetRepresentation
    """

    blend_data: BlendData
    """ 

    :type: BlendData
    """

    collection: Collection
    """ 

    :type: Collection
    """

    engine: str
    """ 

    :type: str
    """

    gizmo_group: GizmoGroup
    """ 

    :type: GizmoGroup
    """

    layer_collection: LayerCollection
    """ 

    :type: LayerCollection
    """

    mode: str
    """ 

    :type: str
    """

    preferences: Preferences
    """ 

    :type: Preferences
    """

    region: Region
    """ 

    :type: Region
    """

    region_data: RegionView3D
    """ 

    :type: RegionView3D
    """

    scene: Scene
    """ 

    :type: Scene
    """

    screen: Screen
    """ 

    :type: Screen
    """

    space_data: Space
    """ The current space, may be None in background-mode, when the cursor is outside the window or when using menu-search

    :type: Space
    """

    tool_settings: ToolSettings
    """ 

    :type: ToolSettings
    """

    view_layer: ViewLayer
    """ 

    :type: ViewLayer
    """

    window: Window
    """ 

    :type: Window
    """

    window_manager: WindowManager
    """ 

    :type: WindowManager
    """

    workspace: WorkSpace
    """ 

    :type: WorkSpace
    """

    area: Area
    """ 

    :type: Area
    """

    asset: AssetRepresentation
    """ 

    :type: AssetRepresentation
    """

    blend_data: BlendData
    """ 

    :type: BlendData
    """

    collection: Collection
    """ 

    :type: Collection
    """

    engine: str
    """ 

    :type: str
    """

    gizmo_group: GizmoGroup
    """ 

    :type: GizmoGroup
    """

    layer_collection: LayerCollection
    """ 

    :type: LayerCollection
    """

    mode: str
    """ 

    :type: str
    """

    preferences: Preferences
    """ 

    :type: Preferences
    """

    region: Region
    """ 

    :type: Region
    """

    region_data: RegionView3D
    """ 

    :type: RegionView3D
    """

    scene: Scene
    """ 

    :type: Scene
    """

    screen: Screen
    """ 

    :type: Screen
    """

    space_data: Space
    """ The current space, may be None in background-mode, when the cursor is outside the window or when using menu-search

    :type: Space
    """

    tool_settings: ToolSettings
    """ 

    :type: ToolSettings
    """

    view_layer: ViewLayer
    """ 

    :type: ViewLayer
    """

    window: Window
    """ 

    :type: Window
    """

    window_manager: WindowManager
    """ 

    :type: WindowManager
    """

    workspace: WorkSpace
    """ 

    :type: WorkSpace
    """

    texture_slot: TextureSlot
    """ 

    :type: TextureSlot
    """

    scene: Scene
    """ 

    :type: Scene
    """

    world: World
    """ 

    :type: World
    """

    object: Object
    """ 

    :type: Object
    """

    mesh: Mesh
    """ 

    :type: Mesh
    """

    armature: Armature
    """ 

    :type: Armature
    """

    lattice: Lattice
    """ 

    :type: Lattice
    """

    curve: Curve
    """ 

    :type: Curve
    """

    meta_ball: MetaBall
    """ 

    :type: MetaBall
    """

    light: Light
    """ 

    :type: Light
    """

    speaker: Speaker
    """ 

    :type: Speaker
    """

    lightprobe: LightProbe
    """ 

    :type: LightProbe
    """

    camera: Camera
    """ 

    :type: Camera
    """

    material: Material
    """ 

    :type: Material
    """

    material_slot: MaterialSlot
    """ 

    :type: MaterialSlot
    """

    texture: Texture
    """ 

    :type: Texture
    """

    texture_user: ID
    """ 

    :type: ID
    """

    texture_user_property: Property
    """ 

    :type: Property
    """

    texture_node: Node
    """ 

    :type: Node
    """

    bone: Bone
    """ 

    :type: Bone
    """

    edit_bone: EditBone
    """ 

    :type: EditBone
    """

    pose_bone: PoseBone
    """ 

    :type: PoseBone
    """

    particle_system: ParticleSystem
    """ 

    :type: ParticleSystem
    """

    particle_system_editable: ParticleSystem
    """ 

    :type: ParticleSystem
    """

    particle_settings: ParticleSettings
    """ 

    :type: ParticleSettings
    """

    cloth: ClothModifier
    """ 

    :type: ClothModifier
    """

    soft_body: SoftBodyModifier
    """ 

    :type: SoftBodyModifier
    """

    fluid: typing.Any
    collision: CollisionModifier
    """ 

    :type: CollisionModifier
    """

    brush: Brush
    """ 

    :type: Brush
    """

    dynamic_paint: DynamicPaintModifier
    """ 

    :type: DynamicPaintModifier
    """

    line_style: FreestyleLineStyle
    """ 

    :type: FreestyleLineStyle
    """

    collection: LayerCollection
    """ 

    :type: LayerCollection
    """

    gpencil: GreasePencil
    """ 

    :type: GreasePencil
    """

    curves: typing.Any
    volume: Volume
    """ 

    :type: Volume
    """

    edit_movieclip: MovieClip
    """ 

    :type: MovieClip
    """

    edit_mask: Mask
    """ 

    :type: Mask
    """

    active_file: FileSelectEntry | None
    """ 

    :type: FileSelectEntry | None
    """

    selected_files: list[FileSelectEntry]
    """ 

    :type: list[FileSelectEntry]
    """

    asset_library_reference: AssetLibraryReference
    """ 

    :type: AssetLibraryReference
    """

    selected_assets: list[AssetRepresentation]
    """ 

    :type: list[AssetRepresentation]
    """

    id: ID
    """ 

    :type: ID
    """

    selected_ids: list[ID]
    """ 

    :type: list[ID]
    """

    edit_image: Image
    """ 

    :type: Image
    """

    edit_mask: Mask
    """ 

    :type: Mask
    """

    selected_nodes: list[Node]
    """ 

    :type: list[Node]
    """

    active_node: Node | None
    """ 

    :type: Node | None
    """

    light: Light
    """ 

    :type: Light
    """

    material: Material
    """ 

    :type: Material
    """

    world: World
    """ 

    :type: World
    """

    scene: Scene
    """ 

    :type: Scene
    """

    view_layer: ViewLayer
    """ 

    :type: ViewLayer
    """

    visible_objects: list[Object]
    """ 

    :type: list[Object]
    """

    selectable_objects: list[Object]
    """ 

    :type: list[Object]
    """

    selected_objects: list[Object]
    """ 

    :type: list[Object]
    """

    editable_objects: list[Object]
    """ 

    :type: list[Object]
    """

    selected_editable_objects: list[Object]
    """ 

    :type: list[Object]
    """

    objects_in_mode: list[Object]
    """ 

    :type: list[Object]
    """

    objects_in_mode_unique_data: list[Object]
    """ 

    :type: list[Object]
    """

    visible_bones: list[EditBone]
    """ 

    :type: list[EditBone]
    """

    editable_bones: list[EditBone]
    """ 

    :type: list[EditBone]
    """

    selected_bones: list[EditBone]
    """ 

    :type: list[EditBone]
    """

    selected_editable_bones: list[EditBone]
    """ 

    :type: list[EditBone]
    """

    visible_pose_bones: list[PoseBone]
    """ 

    :type: list[PoseBone]
    """

    selected_pose_bones: list[PoseBone]
    """ 

    :type: list[PoseBone]
    """

    selected_pose_bones_from_active_object: list[PoseBone]
    """ 

    :type: list[PoseBone]
    """

    active_bone: EditBone | None
    """ 

    :type: EditBone | None
    """

    active_pose_bone: PoseBone | None
    """ 

    :type: PoseBone | None
    """

    active_object: Object | None
    """ 

    :type: Object | None
    """

    object: Object
    """ 

    :type: Object
    """

    edit_object: Object
    """ 

    :type: Object
    """

    sculpt_object: Object
    """ 

    :type: Object
    """

    vertex_paint_object: Object
    """ 

    :type: Object
    """

    weight_paint_object: Object
    """ 

    :type: Object
    """

    image_paint_object: Object
    """ 

    :type: Object
    """

    particle_edit_object: Object
    """ 

    :type: Object
    """

    pose_object: Object
    """ 

    :type: Object
    """

    active_sequence_strip: Sequence | None
    """ 

    :type: Sequence | None
    """

    sequences: list[Sequence]
    """ 

    :type: list[Sequence]
    """

    selected_sequences: list[Sequence]
    """ 

    :type: list[Sequence]
    """

    selected_editable_sequences: list[Sequence]
    """ 

    :type: list[Sequence]
    """

    active_nla_track: NlaTrack | None
    """ 

    :type: NlaTrack | None
    """

    active_nla_strip: NlaStrip | None
    """ 

    :type: NlaStrip | None
    """

    selected_nla_strips: list[NlaStrip]
    """ 

    :type: list[NlaStrip]
    """

    selected_movieclip_tracks: list[MovieTrackingTrack]
    """ 

    :type: list[MovieTrackingTrack]
    """

    gpencil_data: GreasePencil
    """ 

    :type: GreasePencil
    """

    gpencil_data_owner: ID
    """ 

    :type: ID
    """

    annotation_data: GreasePencil
    """ 

    :type: GreasePencil
    """

    annotation_data_owner: ID
    """ 

    :type: ID
    """

    visible_gpencil_layers: list[GPencilLayer]
    """ 

    :type: list[GPencilLayer]
    """

    editable_gpencil_layers: list[GPencilLayer]
    """ 

    :type: list[GPencilLayer]
    """

    editable_gpencil_strokes: list[GPencilStroke]
    """ 

    :type: list[GPencilStroke]
    """

    active_gpencil_layer: list[GPencilLayer] | None
    """ 

    :type: list[GPencilLayer] | None
    """

    active_gpencil_frame: typing.Any
    active_annotation_layer: GPencilLayer | None
    """ 

    :type: GPencilLayer | None
    """

    active_operator: Operator | None
    """ 

    :type: Operator | None
    """

    active_action: Action | None
    """ 

    :type: Action | None
    """

    selected_visible_actions: list[Action]
    """ 

    :type: list[Action]
    """

    selected_editable_actions: list[Action]
    """ 

    :type: list[Action]
    """

    visible_fcurves: list[FCurve]
    """ 

    :type: list[FCurve]
    """

    editable_fcurves: list[FCurve]
    """ 

    :type: list[FCurve]
    """

    selected_visible_fcurves: list[FCurve]
    """ 

    :type: list[FCurve]
    """

    selected_editable_fcurves: list[FCurve]
    """ 

    :type: list[FCurve]
    """

    active_editable_fcurve: FCurve | None
    """ 

    :type: FCurve | None
    """

    selected_editable_keyframes: list[Keyframe]
    """ 

    :type: list[Keyframe]
    """

    ui_list: UIList
    """ 

    :type: UIList
    """

    property: tuple[AnyType]
    """ Get the property associated with a hovered button.
Returns a tuple of the data-block, data path to the property, and array index.

    :type: tuple[AnyType]
    """

    asset_library_reference: AssetLibraryReference
    """ 

    :type: AssetLibraryReference
    """

    edit_mask: Mask
    """ 

    :type: Mask
    """

    edit_text: Text
    """ 

    :type: Text
    """

    active_object: Object | None
    """ 

    :type: Object | None
    """

    selected_ids: list[ID]
    """ 

    :type: list[ID]
    """

    def evaluated_depsgraph_get(self) -> Depsgraph:
        """Get the dependency graph for the current scene and view layer, to access to data-blocks with animation and modifiers applied. If any data-blocks have been edited, the dependency graph will be updated. This invalidates all references to evaluated data-blocks from the dependency graph.

        :return: Evaluated dependency graph
        :rtype: Depsgraph
        """
        ...

    def copy(self): ...
    def path_resolve(self, path: str | None, coerce: bool | None = True):
        """Returns the property from the path, raise an exception when not found.

        :param path: patch which this property resolves.
        :type path: str | None
        :param coerce: optional argument, when True, the property will be converted into its Python representation.
        :type coerce: bool | None
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

    def temp_override(
        self,
        window: Window | None,
        area: Area | None,
        region: Region | None,
        **keywords,
    ):
        """Context manager to temporarily override members in the context.Overriding the context can be used to temporarily activate another window / area & region,
        as well as other members such as the active_object or bone.Notes:Overriding the context can be useful to set the context after loading files
        (which would otherwise by None). For example:This example shows how it's possible to add an object to the scene in another window.

                :param window: Window override or None.
                :type window: Window | None
                :param area: Area override or None.
                :type area: Area | None
                :param region: Region override or None.
                :type region: Region | None
                :param keywords: Additional keywords override context members.
                :return: The context manager .
        """
        ...
