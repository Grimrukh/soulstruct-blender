"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.base.models.flver import FLVER, Version


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr")


class BlenderFLVERHeader:
    """FLVER header information that needs tracking in Blender.

    TODO: Should be able to set sensible defaults for these in DSR...
    """

    # Custom properties:
    endian: bytes
    version: Version
    unicode: bool
    unk_x4a: bool
    unk_x4c: int
    unk_x5c: int
    unk_x5d: int
    unk_x68: int


class BlenderFLVERDummy:
    """FLVER Dummy information."""

    # TODO: Set `position` from Blender position and `forward` and `upward` from Blender rotation.
    #  Will need to convert to parent bone space.

    reference_id: int
    parent_bone_name: str  # TODO: bind/pose to this bone?
    attach_bone_name: str  # TODO: only matters in animations?
    flag_1: bool  # TODO: True in DS1?
    use_upward_vector: bool  # TODO: True in DS1?


class BlenderFLVERMaterial:
    """FLVER Material information."""

    # TODO: Storing most of these already in Blender, I think.

    name: str
    mtd_path: str
    flags: int
    gx_index: int
    unk_x18: int


class BLenderFLVERMesh:
    """FLVER Mesh information."""

    # TODO: Should mostly be already set?

    is_bind_pose: bool
    material_index: int
    default_bone_index: int
    # bounding_box: tp.Optional[BoundingBox]

    # bone_indices: list[int]
    # face_sets: list[FaceSet]
    # vertex_buffers: list[VertexBuffer]
    # vertices: list[Vertex]


def test():
    c1200 = FLVER.from_chrbnd(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")  # Large Rat
    print(c1200.bones)


if __name__ == '__main__':
    test()
