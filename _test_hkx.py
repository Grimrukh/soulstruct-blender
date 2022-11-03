from pathlib import Path

from soulstruct.containers import Binder
from soulstruct_havok.wrappers.hkx2015 import CollisionHKX


PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map/m11_00_00_00/")


def main():
    low_path = Binder(PATH / "l11_00_00_00.hkxbhd")
    low = CollisionHKX(low_path["l0000B0A11.hkx.dcx"])
    print(low.get_root_tree_string(max_primitive_sequence_size=20))


if __name__ == '__main__':
    main()
