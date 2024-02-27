from soulstruct import FLVER, Path, Binder


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")
ER_PATH = Path("C:/Steam/steamapps/common/ELDEN RING/Game")


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
        if v_bone.usage_flags == a_bone.usage_flags:
            continue
        print()
        print(v_bone)
        print(a_bone)
        a_bone.usage_flags = v_bone.usage_flags

    # i = 13
    # artorias.submeshes[i] = van_artorias.submeshes[i]

    # artorias_binder[200].set_uncompressed_data(bytes(artorias))
    # artorias_binder.write()


def test_blaidd():
    from soulstruct.eldenring.models.matbin import MATBINBND
    matbinbnd = MATBINBND.from_bundled()

    model = "c2140"
    chrbnd_path = ER_PATH / f"chr/{model}.chrbnd.dcx"
    flver = FLVER.from_binder_path(chrbnd_path, f"{model}.flver")

    submesh = flver.submeshes[0]

    print(submesh.material)
    print(submesh.vertices[:10])
    print(submesh.vertices.dtype.names)
    uv_layer_count = len([f for f in submesh.vertices.dtype.names if "uv" in f])

    # TODO: Trying to figure out how to tell which MATBIN samplers go in which "UV group", so I know which FLVER UV
    #  layer to plug in to that sampler node in Blender shader.
    matbin = matbinbnd.get_matbin(submesh.material.mat_def_name)
    print(matbin)
    for sampler in matbin.samplers:
        print(sampler)
    print(f"FLVER submesh UV layer count = {uv_layer_count}")


if __name__ == '__main__':
    # test_artorias()
    test_blaidd()
