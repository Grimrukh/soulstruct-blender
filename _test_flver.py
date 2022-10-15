"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.base.models.flver import FLVER, Version
from soulstruct.utilities.inspection import profile_function


TEST_PATH = Path(__file__).parent / "tests"


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


@profile_function(20)
def test():
    c1200 = FLVER.from_chrbnd(TEST_PATH / "c5280.chrbnd.dcx")  # Quelaag
    # print(c1200.bones)


if __name__ == '__main__':
    test()
