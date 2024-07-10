from soulstruct import FLVER, Path, Binder


WB_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Workbench)")
ER_PATH = Path("C:/Steam/steamapps/common/ELDEN RING (Modding 1.12)/Game")


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
    from soulstruct.base.models.matbin import MATBINBND
    from soulstruct.eldenring.models.shaders import MatDef
    from soulstruct.eldenring.constants import CHARACTER_MODELS

    def model_lookup(name):
        for model_id, model_name in CHARACTER_MODELS.items():
            if name in model_name:
                return f"c{model_id}"
        raise ValueError(f"No model found starting with '{name}'.")

    matbinbnd = MATBINBND.from_bundled("ELDEN RING")

    model = model_lookup("Blaidd")

    chrbnd_path = ER_PATH / f"chr/{model}.chrbnd.dcx"
    flver = FLVER.from_binder_path(chrbnd_path, f"{model}.flver")

    for submesh in flver.submeshes:
        print(f"Submesh mat def name: {submesh.material.mat_def_name}")
        matbin = matbinbnd.get_matbin(submesh.material.mat_def_name)
        matdef = MatDef.from_matbin(matbin)
        print(f"{submesh.material.name} ({matdef.shader_stem})")

        for key, value in matdef.matbin_params.items():
            print(f"        {key} = {value}")

        all_samplers = {sampler.name: sampler for sampler in matdef.samplers}
        layer_sampler_paths = matdef.get_uv_group_sampler_paths()
        for group, sampler_paths in sorted(layer_sampler_paths.items()):
            print(f"    Sampler Group: {group}")
            for sampler_name, (sampler_path, uv_layer) in sampler_paths.items():
                print(f"        {sampler_name} = \"{Path(sampler_path).stem}\"")
                print(f"            alias = {all_samplers[sampler_name].alias}")
                print(f"            uv_layer = {all_samplers[sampler_name].uv_layer.name}")
                all_samplers.pop(sampler_name)
        if all_samplers:
            print("    UNUSED SAMPLERS:")
            for sampler in all_samplers.values():
                print(f"        ({sampler.sampler_group}) {sampler.name}")


if __name__ == '__main__':
    # test_artorias()
    test_blaidd()
