from pathlib import Path

from soulstruct.containers import Binder
from soulstruct_havok.wrappers.hkx2015 import CollisionHKX


PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map/m10_01_00_00/")


def main():
    hi = Binder(PATH / "h10_01_00_00.hkxbhd")
    col = CollisionHKX(hi["h0029B1A10.hkx.dcx"])
    print(col.get_root_tree_string())


if __name__ == '__main__':
    main()
    # import timeit
    # seconds = timeit.timeit("main()", number=1)
    # print(f"{seconds} seconds")
