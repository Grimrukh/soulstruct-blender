from pathlib import Path

from soulstruct.containers import Binder, TPF


def main():
    bnd = Binder(Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr/c1200.chrbnd.dcx"))
    tpf = TPF(bnd["c1200.tpf"])
    print(tpf)
    tpf.export_to_pngs(".")


if __name__ == '__main__':
    main()
