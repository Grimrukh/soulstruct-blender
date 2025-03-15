__all__ = [
    "FLVERBoneDataType",
    "FLVERModelType",
]

from enum import Enum, StrEnum


class FLVERBoneDataType(StrEnum):
    """Indicates where FLVER bone data is kept in Blender:

        Edit bones ('is_bind_pose = True' rigged meshes - Characters, Equipment, and most Objects)
        Custom FLVER bone data ('is_bind_pose = False' unrigged meshes - Map Pieces and some Objects)
        Omitted (ignored) - FLVER has one default bone that can be ignored for simplicity (most Map Pieces)
    """
    EDIT = "EditBone"
    CUSTOM = "Custom"
    OMITTED = "Omitted"


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

    @classmethod
    def guess_from_name(cls, name: str):
        name = name.lower()
        if name[0] == "m":
            return cls.MapPiece
        if name[0] == "c":
            return cls.Character
        if name[0] == "o" or name.startswith("aeg"):
            return cls.Object
        if name[:2] in {"am", "bd", "hd", "hr", "lg", "wp"}:
            return cls.Equipment
        return cls.Unknown
