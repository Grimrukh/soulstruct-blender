"""Functions that find and/or create Blender objects, and copy data between them."""
from __future__ import annotations

__all__ = [
    "new_mesh_object",
    "new_armature_object",
    "new_empty_object",
    "find_obj",
    "find_obj_or_create_empty",
    "copy_obj_property_group",
    "copy_armature_pose",
    "get_or_create_collection",
]

import typing as tp

import bpy

from .misc import remove_dupe_suffix
from .bpy_types import ObjectType, SoulstructType

if tp.TYPE_CHECKING:
    PROPS_TYPE = tp.Union[tp.Dict[str, tp.Any], bpy.types.Object, None]


def new_mesh_object(
    name: str, data: bpy.types.Mesh, soulstruct_type: SoulstructType = SoulstructType.NONE
) -> bpy.types.MeshObject:
    mesh_obj = bpy.data.objects.new(name, data)
    mesh_obj.soulstruct_type = soulstruct_type
    # noinspection PyTypeChecker
    return mesh_obj


def new_armature_object(
    name: str,
    data: bpy.types.Armature,
    soulstruct_type: SoulstructType = SoulstructType.NONE,
) -> bpy.types.ArmatureObject:
    armature_obj = bpy.data.objects.new(name, data)
    armature_obj.soulstruct_type = soulstruct_type
    # noinspection PyTypeChecker
    return armature_obj


def new_empty_object(name: str, soulstruct_type: SoulstructType = SoulstructType.NONE) -> bpy.types.Object:
    # noinspection PyTypeChecker
    empty_obj = bpy.data.objects.new(name, None)
    empty_obj.soulstruct_type = soulstruct_type
    return empty_obj


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.MESH] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
) -> bpy.types.MeshObject | None:
    ...


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.ARMATURE] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
) -> bpy.types.ArmatureObject | None:
    ...


@tp.overload
def find_obj(
    name: str,
    object_type: tp.Literal[ObjectType.EMPTY] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
) -> bpy.types.EmptyObject | None:
    ...


def find_obj(
    name: str,
    object_type: ObjectType | str | None = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
) -> bpy.types.Object | None:
    """Search for a Blender object, optionally restricting its Blender type and/or Soulstruct type.

    We can't just do a `bpy.data.objects` look-up for this, because an object with the exact same name (even without
    dupe suffix) may exist but have the wrong type, while the correctly-typed one has a dupe suffix or requires other
    processing to match the name. So we iterate over all objects and check each one's name and type carefully.

    You should restrict `objects` as much as possible before calling this (e.g. from specific Collections). Otherwise,
    it will default to the full `bpy.data.objects` list.

    If `bl_name_func` is given, objects will have their names passed through it before checking for quality with `name`.
    For example, this function may just split at the first space so existing object 'h1234B0 (Floor).003' can be found
    with `name = 'h1234B0'`.

    If `bl_name_func` is left as `None`, it will still remove Blender's dupe suffix from each checked object. If you
    (for some reason) actually want to match a `name` that has a dupe-like suffix, you will need to pass an identity
    function as `bl_name_func`.
    """
    if objects is None:
        objects = bpy.data.objects

    if not bl_name_func:
        bl_name_func = remove_dupe_suffix

    for obj in objects:
        if object_type and obj.type != object_type:
            continue
        if soulstruct_type and obj.soulstruct_type != soulstruct_type:
            continue
        if bl_name_func(obj.name) == name:
            return obj
    return None


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.MESH] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
    missing_reference_callback: tp.Callable[[bpy.types.Object], None] = None,
) -> tuple[bool, bpy.types.MeshObject]:
    ...


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.ARMATURE] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
    process_new_object: tp.Callable[[bpy.types.Object], None] = None,
) -> tuple[bool, bpy.types.ArmatureObject]:
    ...


@tp.overload
def find_obj_or_create_empty(
    name: str,
    object_type: tp.Literal[ObjectType.EMPTY] = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
    process_new_object: tp.Callable[[bpy.types.Object], None] = None,
) -> tuple[bool, bpy.types.EmptyObject]:
    ...


def find_obj_or_create_empty(
    name: str,
    object_type: ObjectType | str | None = None,
    soulstruct_type: SoulstructType | None = None,
    bl_name_func: tp.Callable[[str], str] | None = None,
    objects: tp.Iterable[bpy.types.Object] | None = None,
    process_new_object: tp.Callable[[bpy.types.Object], None] = None,
) -> tuple[bool, bpy.types.Object]:
    """Search for a Blender object, optionally restricting its Blender type and/or Soulstruct type. If the object isn't
    found, an Empty is created with the appropriate Soulstruct type and passed to `process_new_object` (if given) or
    added to the current scene collection.

    You should restrict `objects` as much as possible before calling this (e.g. from specific Collections). Otherwise,
    it will default to the full `bpy.data.objects` list.

    If `bl_name_func` is given, objects will have their names passed through it before checking for quality with `name`
    UNLESS an exact name match exists (which should obviously also be a processed match). For example, this function may
    just split at the first space so existing object 'h1234 (Floor).003' can be found with `name = 'h1234'`.

    If object isn't found, create it in collection `missing_collection_name`.

    Returns `(was_created, object)`.
    """
    obj = find_obj(name, object_type, soulstruct_type, bl_name_func, objects)
    if obj:
        return False, obj

    obj = bpy.data.objects.new(name, None)  # always Empty
    if soulstruct_type:
        obj.soulstruct_type = soulstruct_type

    if process_new_object:
        # This should add the new `obj` to a Collection, plus anything else needed.
        process_new_object(obj)
    else:
        # As as backup, we will at least add it to the scene (NOTE: `context` is not passed in).
        bpy.context.scene.collection.objects.link(obj)

    return True, obj


def copy_obj_property_group(
    source_obj: bpy.types.Object,
    dest_obj: bpy.types.Object,
    props_name: str,
    filter_func: tp.Callable[[str], bool] | None = None,
):
    """Use annotations of `source_obj.props_name` to copy properties to `dest_obj.props_name`."""
    source_props = getattr(source_obj, props_name)
    dest_props = getattr(dest_obj, props_name)
    for prop_name in source_props.__class__.__annotations__:
        if filter_func and not filter_func(prop_name):
            continue
        setattr(dest_props, prop_name, getattr(source_props, prop_name))


def copy_armature_pose(
    source_armature: bpy.types.ArmatureObject,
    dest_armature: bpy.types.ArmatureObject,
    ignore_bone_names: tp.Collection[str] = (),
):
    """Copy pose bone transforms.

    NOTE: You need to call `context.view_layer.update()` between creating an `Armature` and accessing its `pose`.
    """

    for pose_bone in dest_armature.pose.bones:
        if pose_bone.name in ignore_bone_names:
            continue  # e.g. '<PART_ROOT>'
        source_bone = source_armature.pose.bones[pose_bone.name]
        pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
        pose_bone.location = source_bone.location
        pose_bone.rotation_quaternion = source_bone.rotation_quaternion
        pose_bone.scale = source_bone.scale


def get_or_create_collection(root_collection: bpy.types.Collection, *names: str) -> bpy.types.Collection:
    """Find or create Collection `names[-1]`. If it doesn't exist, create it, nested inside the given `names` hierarchy,
    starting at `root_collection`.

    `hide_viewport` is only used if a new Collection is created.
    """
    names = list(names)
    if not names:
        raise ValueError("At least one Collection name must be provided.")
    target_name = names.pop()
    try:
        return bpy.data.collections[target_name]
    except KeyError:
        collection = bpy.data.collections.new(target_name)
        if not names:
            # Reached top of hierarchy.
            if root_collection:
                root_collection.children.link(collection)
            return collection
        parent_collection = get_or_create_collection(root_collection, *names)
        parent_collection.children.link(collection)
        return collection
