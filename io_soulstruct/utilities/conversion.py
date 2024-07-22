from __future__ import annotations

__all__ = [
    "GAME_TO_BL_VECTOR",
    "GAME_TO_BL_EULER",
    "GAME_TO_BL_MAT3",
    "GAME_TO_BL_ARRAY",
    "game_forward_up_vectors_to_bl_euler",
    "BL_TO_GAME_VECTOR3",
    "BL_TO_GAME_VECTOR4",
    "BL_TO_GAME_EULER",
    "BL_TO_GAME_MAT3",
    "BL_TO_GAME_ARRAY",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
    "Transform",
    "BlenderTransform",
]

import math
import numpy as np
import typing as tp
from dataclasses import dataclass

from mathutils import Vector, Euler, Matrix

from soulstruct.utilities.maths import Vector3, Vector4, Matrix3


def GAME_TO_BL_VECTOR(game_vector: Vector3 | Vector4 | tp.Sequence[float, float, float]) -> Vector:
    """Just swaps Y and Z axes. X increases to the right in both systems; the game is left-handed and Blender is
    right-handed.

    This function is its own inverse, but an explicit converter that produces a Soulstruct class is given below.
    """
    return Vector((game_vector[0], game_vector[2], game_vector[1]))


def BL_TO_GAME_VECTOR3(bl_vector: Vector):
    """See above."""
    return Vector3((bl_vector.x, bl_vector.z, bl_vector.y))


def GAME_TO_BL_ARRAY(game_array: np.ndarray) -> np.ndarray:
    """Just swaps Y and Z axes. X increases to the right in both systems; the game is left-handed and Blender is
    right-handed.

    This function is its own inverse, but an explicit converter that produces a Soulstruct class is given below.
    """
    return np.array((game_array[:, 0], game_array[:, 2], game_array[:, 1])).T


def BL_TO_GAME_ARRAY(bl_array: np.ndarray) -> np.ndarray:
    """See above."""
    return np.array((bl_array[:, 0], bl_array[:, 2], bl_array[:, 1])).T


def BL_TO_GAME_VECTOR4(bl_vector: Vector, w=0.0):
    """See above."""
    return Vector4((bl_vector.x, bl_vector.z, bl_vector.y, w))


def GAME_TO_BL_EULER(game_euler) -> Euler:
    """All three Euler angles need negating to preserve rotations.

    This function is its own inverse, but an explicit converted that produces a Soulstruct class is given below.

    NOTE: Blender Euler rotation mode should be 'XYZ' (corresponding to game 'XZY').
    """
    return Euler((-game_euler[0], -game_euler[2], -game_euler[1]))


def GAME_TO_BL_MAT3(game_mat3: Matrix3) -> Matrix:
    """Converts a 3x3 rotation matrix from the game to a Blender Matrix.

    Swaps columns 1 and 2, and rows 1 and 2.
    """
    r = game_mat3
    return Matrix((
        (r[0, 0], r[0, 2], r[0, 1]),
        (r[2, 0], r[2, 2], r[2, 1]),
        (r[1, 0], r[1, 2], r[1, 1]),
    ))


def game_forward_up_vectors_to_bl_euler(forward: Vector3, up: Vector3) -> Euler:
    """Convert `forward` and `up` vectors to Euler angles `(x, y, z)` (in Blender coordinates).

    Mainly used for representing FLVER dummies in Blender.
    """
    right = up.cross(forward)
    rotation_matrix = Matrix3([
        [right.x, up.x, forward.x],
        [right.y, up.y, forward.y],
        [right.z, up.z, forward.z],
    ])
    game_euler = rotation_matrix.to_euler_angles(radians=True)
    return GAME_TO_BL_EULER(game_euler)


def BL_TO_GAME_MAT3(bl_mat3: Matrix) -> Matrix3:
    """Converts a 3x3 rotation matrix from Blender to the game.

    This is the same transformation as GAME_TO_BL_MAT3, but the types are swapped.
    """
    r = bl_mat3
    return Matrix3((
        (r[0][0], r[0][2], r[0][1]),
        (r[2][0], r[2][2], r[2][1]),
        (r[1][0], r[1][2], r[1][1]),
    ))


def BL_TO_GAME_EULER(bl_euler: Euler) -> Vector3:
    """Convert a Blender XYZ `Euler` in Blender space to game XZY Euler angles as a `Vector3`."""
    return Vector3((-bl_euler.x, -bl_euler.z, -bl_euler.y))


def bl_euler_to_game_forward_up_vectors(bl_euler: Euler) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Euler` to its forward-axis and up-axis vectors in game space (for `FLVER.Dummy`)."""
    game_euler = BL_TO_GAME_EULER(bl_euler)
    game_mat = Matrix3.from_euler_angles(game_euler)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


def bl_rotmat_to_game_forward_up_vectors(bl_rotmat: Matrix) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Matrix` to its game equivalent's forward-axis and up-axis vectors (for `FLVER.Dummy`)."""
    game_mat = BL_TO_GAME_MAT3(bl_rotmat)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


@dataclass(slots=True)
class Transform:
    """Store a FromSoft translate/rotate/scale combo, with property access to Blender conversions for all three."""

    translate: Vector3
    rotate: Vector3  # Euler angles
    scale: Vector3
    radians: bool = False

    @classmethod
    def from_msb_entry(cls, entry) -> Transform:
        return cls(entry.translate, entry.rotate, getattr(entry, "scale", Vector3.one()))

    @property
    def bl_translate(self) -> Vector:
        return GAME_TO_BL_VECTOR(self.translate)

    @property
    def bl_rotate(self) -> Euler:
        if not self.radians:
            return GAME_TO_BL_EULER(math.pi / 180.0 * self.rotate)
        return GAME_TO_BL_EULER(self.rotate)

    @property
    def bl_scale(self) -> Vector:
        return GAME_TO_BL_VECTOR(self.scale)


@dataclass(slots=True)
class BlenderTransform:
    """Store a Blender translate/rotate/scale combo."""

    bl_translate: Vector
    bl_rotate: Euler  # radians
    bl_scale: Vector

    @property
    def game_translate(self) -> Vector3:
        return BL_TO_GAME_VECTOR3(self.bl_translate)

    @property
    def game_rotate_deg(self) -> Vector3:
        return 180.0 / math.pi * self.game_rotate_rad

    @property
    def game_rotate_rad(self) -> Vector3:
        return BL_TO_GAME_EULER(self.bl_rotate)

    @property
    def game_scale(self) -> Vector3:
        return BL_TO_GAME_VECTOR3(self.bl_scale)

    @classmethod
    def from_bl_obj(cls, bl_obj) -> BlenderTransform:
        return BlenderTransform(
            bl_obj.location,
            bl_obj.rotation_euler,
            bl_obj.scale,
        )

    def to_matrix(self) -> Matrix:
        return Matrix.LocRotScale(self.bl_translate, self.bl_rotate, self.bl_scale)

    def inverse(self) -> BlenderTransform:
        inv_rotate_mat = self.bl_rotate.to_matrix().inverted()
        inv_translate = -(inv_rotate_mat @ self.bl_translate)
        inv_scale = Vector((1.0 / self.bl_scale.x, 1.0 / self.bl_scale.y, 1.0 / self.bl_scale.z))
        return BlenderTransform(inv_translate, inv_rotate_mat.to_euler(), inv_scale)

    def compose(self, other: BlenderTransform):
        """Apply to another transform."""
        rot_mat = self.bl_rotate.to_matrix()
        new_translate = self.bl_translate + rot_mat @ other.bl_translate
        new_rotate = (rot_mat @ other.bl_rotate.to_matrix()).to_euler()
        new_scale = self.bl_scale * other.bl_scale
        return BlenderTransform(new_translate, new_rotate, new_scale)
