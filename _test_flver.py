"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.base.models.flver import FLVER, Version
from soulstruct.utilities.inspection import profile_function


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr")
VANILLA_MAP_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map")
TEST_PATH = Path(__file__).parent / "tests"


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


# @profile_function(20)
def test():
    # chrbnd = Binder(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")
    # flver = FLVER(chrbnd[200])
    # for mesh in flver.meshes:
    #     print(mesh.is_bind_pose)
    # for bone in flver.bones:
    #     print(bone.name)

    outside_parish = FLVER(VANILLA_MAP_PATH / "m10_01_00_00/m3210B1A10.flver.dcx")
    mesh_11 = outside_parish.meshes[11]  # main ground mesh
    print(outside_parish.materials[mesh_11.material_index])

    # chrbnd[200].set_uncompressed_data(flver.pack_dcx())
    # chrbnd.write("c5280_write.chrbnd.dcx")


if __name__ == '__main__':
    test()
