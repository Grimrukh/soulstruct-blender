from __future__ import annotations

__all__ = [
    "to_blender",
    "game_vector_array_to_bl_vector_array",
    "game_trs_to_bl_matrix",
    "to_game",
    "bl_vector_array_to_game_vector_array",
    "bl_matrix_to_game_trs",
    "FSTransform",
    "BLTransform",
]

import math
import typing as tp
from dataclasses import dataclass
from functools import singledispatch

import numpy as np

import bpy
from mathutils import (
    Vector as BLVector,
    Euler as BLEuler,
    Matrix as BLMatrix,
    Quaternion as BLQuaternion,
)

from soulstruct.utilities.maths import Vector3, EulerDeg, EulerRad, Matrix3, Matrix4
from soulstruct.havok.utilities.maths import TRSTransform, Quaternion as FSQuaternion


# This is the CoB matrix that all the functions below are effectively applying. (They just do it in a more efficient
# way than actually multiplying by this matrix.) It is also its own inverse.
# It swaps the Y and Z axes, and because its determinant is -1 (i.e. we don't negate a single axis), it also reflects
# the coordinate system from left-handed (game) to right-handed (Blender).
FS_BL_CoB_3 = BLMatrix((
    (1.0, 0.0, 0.0),  # X_b  <=  X_g goes to Blender +X (1st column)
    (0.0, 0.0, 1.0),  # Y_b  <=  Y_g goes to Blender +Z (3rd column)
    (0.0, 1.0, 0.0),  # Z_b  <=  Z_g goes to Blender +Y (2nd column)
))
FS_BL_CoB_4 = BLMatrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
))


# =========================
# Game -> Blender
# =========================

BLENDER_TO_GAME_TYPES = tp.Union[BLEuler, BLVector, BLMatrix, BLQuaternion]

@singledispatch
def to_game(obj: BLENDER_TO_GAME_TYPES) -> tp.Union[Vector3, Matrix3, Matrix4, EulerRad, FSQuaternion]:
    """Default: raise for unsupported types."""
    raise TypeError(f"to_game() has no registered converter for type {type(obj)!r}")

@to_game.register(BLVector)
def _(v: BLVector) -> Vector3:
    """Swap Y and Z axes."""
    return Vector3((v.x, v.z, v.y))

@to_game.register(BLMatrix)
def _(m: BLMatrix) -> Matrix3 | Matrix4:
    """Convert a rotation or homogenous matrix.

    Swap rows 1 and 2, and columns 1 and 2.
    """
    if len(m) == 3:
        return Matrix3((
            (m[0][0], m[0][2], m[0][1]),
            (m[2][0], m[2][2], m[2][1]),
            (m[1][0], m[1][2], m[1][1]),
        ))
    elif len(m) == 4:
        return Matrix4((
            (m[0][0], m[0][2], m[0][1], m[0][3]),
            (m[2][0], m[2][2], m[2][1], m[2][3]),
            (m[1][0], m[1][2], m[1][1], m[1][3]),
            (m[3][0], m[3][2], m[3][1], m[3][3]),
        ))
    raise TypeError("to_game(Matrix): expected 3x3 or 4x4 Matrix.")

@to_game.register(BLEuler)
def _(e: BLEuler) -> EulerRad:
    """Negate all, swap Z and Y (== sandwiching with FS_BL_CoB_3).

    Blender Euler is XYZ, so this produces game XZY, as desired.
    """
    return EulerRad((-e.x, -e.z, -e.y))  # negate all, swap Z and Y


@to_game.register(BLQuaternion)
def _(q: BLQuaternion):
    """Move `w` to end, negate all, and swap Y and Z (== sandwiching with FS_BL_CoB_3 with 3x3 round trip)."""
    # TODO: Not 100% certain this is equivalent to the matrix round trip.
    return FSQuaternion((-q.x, -q.z, -q.y, q.w))

def bl_vector_array_to_game_vector_array(bl_array: np.ndarray) -> np.ndarray:
    """Convert an array of 3D vectors by simply swapping the Y and Z columns."""
    return np.array((bl_array[:, 0], bl_array[:, 2], bl_array[:, 1])).T


def bl_matrix_to_game_trs(matrix: BLMatrix) -> TRSTransform:
    """Convert a Blender 4x4 homogenous `Matrix` to a game `TRSTransform`.

    We decompose the Matrix to avoid issues with shear.
    """
    bl_translate, bl_rotate, bl_scale = matrix.decompose()
    game_translate = to_game(bl_translate)
    game_rotate = to_game(bl_rotate)  # quaternion
    game_scale = to_game(bl_scale)
    return TRSTransform(game_translate, game_rotate, game_scale)

# =========================
# Blender -> Game  (inverse)
# =========================

GAME_TO_BLENDER_TYPES = tp.Union[Vector3, Matrix3, Matrix4, EulerRad, EulerDeg, FSQuaternion]

@singledispatch
def to_blender(obj: GAME_TO_BLENDER_TYPES) -> tp.Union[BLVector, BLMatrix, BLEuler, BLQuaternion]:
    """Default: raise for unsupported types."""
    raise TypeError(f"to_blender() has no registered converter for type {type(obj)!r}")

@to_blender.register(Vector3)
def _(v: Vector3) -> BLVector:
    """Swap Y and Z axes."""
    return BLVector((v.x, v.z, v.y))

@to_blender.register(Matrix3)
def _(m: Matrix3) -> BLMatrix:
    """Swap rows 1 and 2, and columns 1 and 2."""
    return BLMatrix((
        (m[0][0], m[0][2], m[0][1]),
        (m[2][0], m[2][2], m[2][1]),
        (m[1][0], m[1][2], m[1][1]),
    ))

@to_blender.register(Matrix4)
def _(m: Matrix4) -> BLMatrix:
    """Swap rows 1 and 2, and columns 1 and 2."""
    return BLMatrix((
        (m[0][0], m[0][2], m[0][1], m[0][3]),
        (m[2][0], m[2][2], m[2][1], m[2][3]),
        (m[1][0], m[1][2], m[1][1], m[1][3]),
        (m[3][0], m[3][2], m[3][1], m[3][3]),
    ))

@to_blender.register(EulerDeg)
def _(e: EulerDeg) -> BLEuler:
    """Negate all, swap Z and Y (== sandwiching with FS_BL_CoB_3).

    Game Euler is XZY, so this produces Blender XYZ, as desired. Blender Eulers are always in radians.
    """
    e_rad = e.to_rad()
    return BLEuler((-e_rad.x, -e_rad.z, -e_rad.y))


@to_blender.register(EulerRad)
def _(e: EulerRad) -> BLEuler:
    """Negate all, swap Z and Y (== sandwiching with FS_BL_CoB_3).

    Game Euler is XZY, so this produces Blender XYZ, as desired. Blender Eulers are always in radians.
    """
    return BLEuler((-e.x, -e.z, -e.y))

@to_blender.register(FSQuaternion)
def _(q: FSQuaternion):
    """Move `w` to end, negate all, and swap Y and Z (== sandwiching with FS_BL_CoB_3 with 3x3 round trip)."""
    # TODO: Not 100% certain this is equivalent to the matrix round trip.
    return BLQuaternion((q.w, -q.x, -q.z, -q.y))

def game_vector_array_to_bl_vector_array(game_array: np.ndarray) -> np.ndarray:
    """Just swaps Y and Z axes. X increases to the right in both systems; the game is left-handed and Blender is
    right-handed.

    This function is its own inverse, but an explicit converter that produces a Soulstruct class is given below.
    """
    return np.array((game_array[:, 0], game_array[:, 2], game_array[:, 1])).T

def game_trs_to_bl_matrix(transform: TRSTransform) -> BLMatrix:
    """Convert a game `TRSTransform` to a Blender 4x4 `Matrix`."""
    bl_translate = to_blender(transform.translation)
    bl_rotate = to_blender(transform.rotation)  # quaternion
    bl_scale = to_blender(transform.scale)
    return BLMatrix.LocRotScale(bl_translate, bl_rotate, bl_scale)


@dataclass(slots=True)
class FSTransform:
    """Store a FromSoft translate/rotate/scale combo, with property access to Blender conversions for all three."""

    translate: Vector3
    rotate: EulerDeg
    scale: Vector3

    @classmethod
    def from_msb_entry(cls, entry) -> FSTransform:
        """Handles entries without `scale` (MSBRegion)."""
        return cls(entry.translate, entry.rotate, getattr(entry, "scale", Vector3.one()))

    @property
    def bl_translate(self) -> BLVector:
        return to_blender(self.translate)

    @property
    def bl_rotate(self) -> BLEuler:
        return to_blender(math.pi / 180.0 * self.rotate)

    @property
    def bl_scale(self) -> BLVector:
        return to_blender(self.scale)


@dataclass(slots=True)
class BLTransform:
    """Store a Blender translate/rotate/scale combo."""

    bl_translate: BLVector
    bl_rotate: BLEuler  # radians
    bl_scale: BLVector

    @property
    def game_translate(self) -> Vector3:
        return to_game(self.bl_translate)

    @property
    def game_rotate_deg(self) -> EulerDeg:
        return self.game_rotate_rad.to_deg()

    @property
    def game_rotate_rad(self) -> EulerRad:
        return to_game(self.bl_rotate)

    @property
    def game_scale(self) -> Vector3:
        return to_game(self.bl_scale)

    @classmethod
    def from_bl_obj(cls, bl_obj: bpy.types.Object, use_world_transform=False) -> BLTransform:
        if use_world_transform:
            matrix = bl_obj.matrix_world
            loc, rot, scale = matrix.decompose()  # rot is Quaternion
            rotation_euler = rot.to_euler()
        else:
            loc = bl_obj.location
            rotation_euler = bl_obj.rotation_euler
            scale = bl_obj.scale

        return BLTransform(loc, rotation_euler, scale)

    def to_4x4(self) -> BLMatrix:
        return BLMatrix.LocRotScale(self.bl_translate, self.bl_rotate, self.bl_scale)

    def inverse(self) -> BLTransform:
        inv_rotate_mat = self.bl_rotate.to_matrix().inverted()
        inv_translate = -(inv_rotate_mat @ self.bl_translate)
        inv_scale = BLVector((1.0 / self.bl_scale.x, 1.0 / self.bl_scale.y, 1.0 / self.bl_scale.z))
        return BLTransform(inv_translate, inv_rotate_mat.to_euler(), inv_scale)

    def compose(self, other: BLTransform):
        """Apply to another transform."""
        rot_mat = self.bl_rotate.to_matrix()
        new_translate = self.bl_translate + rot_mat @ other.bl_translate
        new_rotate = (rot_mat @ other.bl_rotate.to_matrix()).to_euler()
        new_scale = self.bl_scale * other.bl_scale
        return BLTransform(new_translate, new_rotate, new_scale)

