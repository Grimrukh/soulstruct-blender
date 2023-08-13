from soulstruct.containers import Binder
from soulstruct.darksouls1r.maps.navmesh import NVM
from soulstruct.config import DSR_PATH


def main():
    nvmbnd = Binder.from_path(DSR_PATH + r"\map\m10_00_00_00\m10_00_00_00.nvmbnd.dcx")
    nvm = nvmbnd[0].to_binary_file(NVM)
    for tri in nvm.triangles:
        print(tri)


if __name__ == '__main__':
    main()
