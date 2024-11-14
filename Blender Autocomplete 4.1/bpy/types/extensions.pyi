"""Superior Soulstruct `Object` type hints for `bpy.types`."""

from .core.armature import Armature
from .core.camera import Camera
from .core.mesh import Mesh
from .core.object import Object


class EmptyObject(Object):
    data: None


class ArmatureObject(Object):
    data: Armature


class MeshObject(Object):
    data: Mesh


class CameraObject(Object):
    data: Camera
