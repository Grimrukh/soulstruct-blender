"""Decorators to register classes (Operator, UIPanel, etc.) and PointerProperties in Blender.

Use the decorators on classes and PropertyGroups, then call `io_soulstruct_register` and `io_soulstruct_unregister`
in the add-on `__init__.py` register/unregister functions.
"""
from __future__ import annotations

__all__ = [
    "io_soulstruct_register",
    "io_soulstruct_unregister",
    "io_soulstruct_class",
    "io_soulstruct_pointer_property",
    "io_soulstruct_space_view_3d_draw_handler",
    "io_soulstruct_depsgraph_update_post_handler",
    "register_io_soulstruct",
    "unregister_io_soulstruct",
]

import typing as tp

import bpy

if tp.TYPE_CHECKING:
    # Types (subtypes) that add-ons can register as classes.
    BL_REGISTER_CLS_TYPES = tp.Union[
        type[bpy.types.Panel],
        type[bpy.types.UIList],
        type[bpy.types.Menu],
        type[bpy.types.Header],
        type[bpy.types.Operator],
        type[bpy.types.KeyingSetInfo],
        type[bpy.types.RenderEngine],
        type[bpy.types.AssetShelf],
        type[bpy.types.FileHandler],
        type[bpy.types.PropertyGroup],
        type[bpy.types.AddonPreferences],
        type[bpy.types.NodeTree],
        type[bpy.types.Node],
        type[bpy.types.NodeSocket],
    ]

    # Subset of Blender ID types that support `PointerProperty` definitions.
    BL_ID_TYPES = tp.Union[
        type[bpy.types.Scene],
        type[bpy.types.Collection],
        type[bpy.types.Object],
        type[bpy.types.Material],
        type[bpy.types.Image],
        type[bpy.types.Bone],
    ]
    BL_POINTER_PROPERTY_TYPES = tp.Union[
        type[bpy.types.PropertyGroup],
    ]
    BL_CALLBACK = tp.Callable[[], None]
    BL_DEPSGRAPH_HANDLER = tp.Callable[[bpy.types.Scene, bpy.types.Depsgraph], None]

# Global list of callbacks for `register()` and `unregister()`.
_REGISTER_CALLBACKS = []  # type: list[BL_CALLBACK]
_UNREGISTER_CALLBACKS = []  # type: list[BL_CALLBACK]

# Global `{name: cls}` dict that decorator appends to.
_CLASSES_TO_REGISTER = {}  # type: dict[str, BL_REGISTER_CLS_TYPES]

# PointerProperty instances defined on Blender types.
_POINTER_PROPERTIES = {
    bpy.types.Scene: {},
    bpy.types.Collection: {},
    bpy.types.Object: {},
    bpy.types.Material: {},
    bpy.types.Image: {},
    bpy.types.Bone: {},
}  # type: dict[BL_ID_TYPES, dict[str, BL_POINTER_PROPERTY_TYPES]]

# Global draw handler callbacks and options that decorator appends to for SpaceView3D draw handlers.
_SPACE_VIEW_3D_HANDLERS = []  # type: list[tuple[BL_CALLBACK, str, str]]
# Tracks returned handlers from `SpaceView3D.draw_handler_add` for removal at unregister.
_ADDED_SPACE_VIEW_3D_HANDLERS = []  # type: list[tuple[tp.Any, str]]

# Global list of depsgraph update post handlers. Does not have any internal 'add/remove' method interface.
_DEPSGRAPH_UPDATE_POST_HANDLERS = []  # type: list[BL_DEPSGRAPH_HANDLER]


def io_soulstruct_register(func: BL_CALLBACK) -> BL_CALLBACK:
    """Decorate any arbitrary function to be called at add-on registration."""
    global _REGISTER_CALLBACKS
    _REGISTER_CALLBACKS.append(func)
    return func


def io_soulstruct_unregister(func: BL_CALLBACK) -> BL_CALLBACK:
    """Decorate any arbitrary function to be called at add-on unregistration."""
    global _UNREGISTER_CALLBACKS
    _UNREGISTER_CALLBACKS.append(func)
    return func


def io_soulstruct_class(cls: BL_REGISTER_CLS_TYPES) -> BL_REGISTER_CLS_TYPES:
    """Decorator that tracks class for registration in `io_soulstruct` add-on."""
    global _CLASSES_TO_REGISTER
    if cls.__name__ in _CLASSES_TO_REGISTER:
        raise ValueError(f"Class {cls.__name__} already registered in `io_soulstruct` add-on.")
    _CLASSES_TO_REGISTER[cls.__name__] = cls
    return cls


def io_soulstruct_pointer_property(
    bl_id_type: BL_ID_TYPES, prop_name: str
) -> tp.Callable[[BL_POINTER_PROPERTY_TYPES], BL_POINTER_PROPERTY_TYPES]:
    """Decorator (factory) that tracks types, e.g. `PropertyGroup`s, to regsiter as `PointerProperty`."""
    global _POINTER_PROPERTIES
    if bl_id_type not in _POINTER_PROPERTIES:
        raise ValueError(f"Cannot register PointerProperties on Blender type `{bl_id_type.__name__}`.")

    def _decorator(cls: BL_POINTER_PROPERTY_TYPES):
        _POINTER_PROPERTIES[bl_id_type][prop_name] = cls
        return cls

    return _decorator


def io_soulstruct_space_view_3d_draw_handler(
    region_type: str = "WINDOW", draw_type = "POST_PIXEL"
) -> tp.Callable[[BL_CALLBACK], BL_CALLBACK]:
    """Decorator (factory) for draw handler functions to add to SpaceView3D. No args supported."""

    global _SPACE_VIEW_3D_HANDLERS
    global _ADDED_SPACE_VIEW_3D_HANDLERS

    def decorator(func: BL_CALLBACK):
        _SPACE_VIEW_3D_HANDLERS.append((func, region_type, draw_type))
        return func

    return decorator


def io_soulstruct_depsgraph_update_post_handler(
    func: BL_DEPSGRAPH_HANDLER
) -> BL_DEPSGRAPH_HANDLER:

    global _DEPSGRAPH_UPDATE_POST_HANDLERS
    _DEPSGRAPH_UPDATE_POST_HANDLERS.append(func)
    return func


def register_io_soulstruct() -> None:

    global _REGISTER_CALLBACKS
    global _CLASSES_TO_REGISTER
    global _POINTER_PROPERTIES
    global _SPACE_VIEW_3D_HANDLERS
    global _ADDED_SPACE_VIEW_3D_HANDLERS
    global _DEPSGRAPH_UPDATE_POST_HANDLERS

    for callback in _REGISTER_CALLBACKS:
        callback()

    for cls_name, cls in _CLASSES_TO_REGISTER.items():
        try:
            bpy.utils.register_class(cls)
        except Exception as ex:
            print(f"Failed to register `io_soulstruct` class {cls_name}: {ex}")
            raise

    for bl_type, props in _POINTER_PROPERTIES.items():
        for prop_name, prop_cls in props.items():
            try:
                setattr(bl_type, prop_name, bpy.props.PointerProperty(type=prop_cls))
            except Exception as ex:
                print(f"Failed to register `io_soulstruct` PointerProperty {bl_type.__name__}.{prop_name}: {ex}")
                raise

    for callback, region_type, draw_type in _SPACE_VIEW_3D_HANDLERS:
        handler = bpy.types.SpaceView3D.draw_handler_add(callback, (), region_type, draw_type)
        _ADDED_SPACE_VIEW_3D_HANDLERS.append((handler, region_type))

    for callback in _DEPSGRAPH_UPDATE_POST_HANDLERS:
        bpy.app.handlers.depsgraph_update_post.append(callback)


def unregister_io_soulstruct() -> None:
    """Removal is done completely in reverse to `register_io_soulstruct`."""

    global _UNREGISTER_CALLBACKS
    global _CLASSES_TO_REGISTER
    global _POINTER_PROPERTIES
    global _ADDED_SPACE_VIEW_3D_HANDLERS

    for callback in reversed(_DEPSGRAPH_UPDATE_POST_HANDLERS):
        bpy.app.handlers.depsgraph_update_post.remove(callback)

    for handler, region_type in reversed(_ADDED_SPACE_VIEW_3D_HANDLERS):
        bpy.types.SpaceView3D.draw_handler_remove(handler, region_type)
    _ADDED_SPACE_VIEW_3D_HANDLERS.clear()

    for bl_type, props in reversed(_POINTER_PROPERTIES.items()):
        for prop_name in props.keys():
            try:
                delattr(bl_type, prop_name)
            except Exception as ex:
                print(f"Failed to unregister PointerProperty {bl_type.__name__}.{prop_name}: {ex}")
                continue

    for cls_name, cls in reversed(_CLASSES_TO_REGISTER.items()):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as ex:
            print(f"Failed to unregister `io_soulstruct` class {cls_name}: {ex}")
            continue

    for callback in reversed(_UNREGISTER_CALLBACKS):
        callback()
