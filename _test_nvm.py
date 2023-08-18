from soulstruct.containers import Binder
from soulstruct.darksouls1r.maps.navmesh import NVM
from soulstruct.config import DSR_PATH


def main():
    nvmbnd = Binder.from_path(DSR_PATH + r"\map\m10_00_00_00\m10_00_00_00.nvmbnd.dcx")
    nvm = nvmbnd[2].to_binary_file(NVM)
    nvm.write("test.nvm")


if __name__ == '__main__':
    main()
