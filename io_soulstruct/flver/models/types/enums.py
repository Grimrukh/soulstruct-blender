__all__ = [
    "FLVERBoneDataType",
    "FLVERModelType",
]

from enum import Enum, StrEnum


class FLVERBoneDataType(StrEnum):
    """Indicates where FLVER bone data is kept in Blender: Edit bones (rigged meshes) or Pose bones (static meshes)."""
    NONE = ""
    EDIT = "EditBone"
    POSE = "PoseBone"


class FLVERModelType(Enum):
    """Type of model represented by a FLVER object. Not stored on FLVERs, but passed in by type-specific operators to
    set some strategies and default values.

    Operators will make educated guesses from FLVER data for `Unknown` type.
    """
    Unknown = 0  # e.g. generic FLVER exporter used
    MapPiece = 1
    Character = 2
    Object = 3  # includes Asset
    Equipment = 4
    Other = 5  # e.g. FFX (not yet used)
