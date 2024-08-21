from soulstruct import Path, FLVER
from soulstruct.utilities.text import indent_lines


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")
VAN_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup 1.03.1)")


def main():
    map_piece = FLVER.from_path(VAN_PATH / "map/m11_00_00_00/m2000B0A11.flver.dcx")
    for submesh in map_piece.submeshes:
        print(submesh.material.name)
        for i, face_set in enumerate(submesh.face_sets):
            print(f"  Face Set {i}: {indent_lines(repr(face_set))}")


if __name__ == '__main__':
    main()
