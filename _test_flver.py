"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.base.models.flver import FLVER


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr")
VANILLA_MAP_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map")
TEST_PATH = Path(__file__).parent / "tests"


def exported_flver():
    exported = FLVER("C:/Users/Scott/Documents/untitled.flver")
    print(exported.meshes)


def test_chr():

    chrbnd = Binder(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")
    for entry in chrbnd:
        print(entry, entry.flags.has_flag_1)
    # chr_flver = FLVER.from_chrbnd(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")
    # exported = FLVER("C:/Users/Scott/Documents/untitled.flver")

    # for dummy in chr_flver.dummies:
    #     print(dummy)


def test():

    map_flver = FLVER(VANILLA_MAP_PATH / "m10_01_00_00/m3220B1A10.flver.dcx")

    mesh = map_flver.meshes[11]
    for v in mesh.vertices:
        print(v.uvs[1])


if __name__ == '__main__':
    test_chr()
    # test()
    # exported_flver()
