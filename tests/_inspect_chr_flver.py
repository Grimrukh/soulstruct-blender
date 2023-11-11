from soulstruct import FLVER, Path


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")


def test_artorias():
    van_artorias = FLVER.from_binder_path(WB_PATH / "chr/c4100.chrbnd.dcx.bak")
    artorias = FLVER.from_binder_path(WB_PATH / "chr/c4100.chrbnd.dcx")

    print(van_artorias.bones)
    print(artorias.bones)
    return


    van_submesh = van_artorias.submeshes[0]  # arms
    submesh = artorias.submeshes[0]

    print(van_artorias)
    print(van_submesh.vertices.dtype)
    print(van_submesh.material)
    print(van_submesh.layout)
    print(van_submesh.vertices["uv_0"][:5])

    print(submesh.vertices.dtype)
    print(submesh.material)
    print(submesh.layout)
    print(submesh.vertices["uv_0"][:5])


if __name__ == '__main__':
    test_artorias()
