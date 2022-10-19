"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.base.models.flver import FLVER


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr")
VANILLA_MAP_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map")
TEST_PATH = Path(__file__).parent / "tests"


def exported_flver():
    exported = FLVER("C:/Users/Scott/Documents/untitled.flver")
    print(exported.meshes)


def test_chr():

    chr_flver = FLVER.from_chrbnd(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")
    # exported = FLVER("C:/Users/Scott/Documents/untitled.flver")

    for dummy in chr_flver.dummies:
        print(dummy)


def test():

    map_flver = FLVER(VANILLA_MAP_PATH / "m10_01_00_00/m3220B1A10.flver.dcx")
    exported = FLVER("C:/Users/Scott/Documents/untitled.flver")

    for mesh, exp_mesh in zip(map_flver.meshes, exported.meshes):
        m = len(mesh.vertices)
        exp_m = len(exp_mesh.vertices)
        print(m, exp_m, exp_m / m)

    # for bone in map_flver.bones:
    #     print(bone.name, bone.translate, bone.rotate, bone.unk_x3c)

    # for material in map_flver.materials:
    #     print(material.name, material.name.encode("utf-16-le"))


if __name__ == '__main__':
    # test_chr()
    test()
    # exported_flver()
