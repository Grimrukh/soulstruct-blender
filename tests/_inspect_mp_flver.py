from soulstruct import Path, FLVER


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")


def main():
    van_m2030B1A10 = FLVER.from_path(WB_PATH / "map/m10_01_00_00/m2030B1A10.flver.dcx.bak")
    m2030B1A10 = FLVER.from_path(WB_PATH / "map/m10_01_00_00/m2030B1A10.flver.dcx")

    for van_submesh, submesh in zip(van_m2030B1A10.submeshes, m2030B1A10.submeshes, strict=True):
        print(van_submesh.vertices["uv_0"][:5])
        print(submesh.vertices["uv_0"][:5])
        print()


if __name__ == '__main__':
    main()
