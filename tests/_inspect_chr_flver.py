from soulstruct import FLVER, Path, Binder


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")


def test_artorias():
    # TODO: Why do some animations glitch for certain vertices?
    #  - Looks possibly like submesh 7 (his dress).
    #  - My export has ~3 times as many vertices: 1623? Why? There are 541 faces, but literally every face is producing
    #  three unique vertices. Why are no loops being merged?
    #  - My tangent data is nowhere close to the original. This shouldn't affect this issue though.
    van_artorias = FLVER.from_binder_path(WB_PATH / "chr/c4100.chrbnd.dcx.bak")
    artorias_binder = Binder.from_path(WB_PATH / "chr/c4100.chrbnd.dcx")
    artorias = FLVER.from_binder_entry(artorias_binder[200])

    for i in range(len(van_artorias.bones)):
        v_bone = van_artorias.bones[i]
        a_bone = artorias.bones[i]
        if v_bone == a_bone:
            continue
        print()
        print(v_bone)
        print(a_bone)
        a_bone.usage_flags = v_bone.usage_flags

    # i = 13
    # artorias.submeshes[i] = van_artorias.submeshes[i]

    # artorias_binder[200].set_uncompressed_data(bytes(artorias))
    # artorias_binder.write()


if __name__ == '__main__':
    test_artorias()
