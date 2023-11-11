from pathlib import Path
from soulstruct import FLVER, DSR_PATH, PTDE_PATH
from soulstruct.darksouls1r.models.mtd import MTD


NF_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Nightfall)")
WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")


def ptde():
    flver = FLVER.from_path(PTDE_PATH + "/map/m14_00_00_00/m0010B0A14.flver")
    print(flver.submeshes[0].vertices.dtype)


def main():
    van_flver = FLVER.from_path(WB_PATH / "map/m14_00_00_00/m0010B0A14.flver.dcx.bak")
    flver = FLVER.from_path(WB_PATH / "map/m14_00_00_00/m0010B0A14.flver.dcx")
    print(van_flver.submeshes[0].vertices.dtype)
    print(van_flver.submeshes[0].material)
    print(flver.submeshes[0].vertices.dtype)
    print(flver.submeshes[0].material)
    print(flver.submeshes[0].vertices[:5])
    mtd = MTD.from_binder_path(WB_PATH / "mtd/mtd.mtdbnd.dcx", flver.submeshes[0].material.mtd_name)
    print(mtd)


def snow():
    van_flver = FLVER.from_path(WB_PATH / "map/m11_00_00_00/m2000B0A11.flver.dcx")
    flver = FLVER.from_path(WB_PATH / "map/m11_00_00_00/m2000B0A11.flver.dcx")
    for i in range(len(flver.submeshes)):
        van_submesh = van_flver.submeshes[i]
        submesh = flver.submeshes[i]
        print()
        # print(van_submesh.vertices.dtype)
        # print(van_submesh.material)
        # print(submesh.vertices.dtype)
        print(submesh.material)
        # print(submesh.vertices[:5])
        mtd = MTD.from_binder_path(WB_PATH / "mtd/mtd.mtdbnd.dcx", submesh.material.mtd_name)
        print(mtd)


if __name__ == '__main__':
    # ptde()
    # main()
    snow()
