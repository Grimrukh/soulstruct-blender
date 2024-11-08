import colorama
import numpy as np

from soulstruct import FLVER, Path
from soulstruct.base.models.matbin import MATBINBND
from soulstruct.eldenring.models.shaders import MatDef
from soulstruct.eldenring.constants import CHARACTER_MODELS

colorama.just_fix_windows_console()
Fore = colorama.Fore


ER_PATH = Path("C:/Steam/steamapps/common/ELDEN RING (Modding 1.12)/Game")


def model_lookup(name):
    for model_id, model_name in CHARACTER_MODELS.items():
        if name in model_name:
            return f"c{model_id}"
    raise ValueError(f"No model found starting with '{name}'.")


def test_model(model_id):

    matbinbnd = MATBINBND.from_bundled("ELDEN RING")
    chrbnd_path = ER_PATH / f"chr/c{model_id:04d}.chrbnd.dcx"
    flver = FLVER.from_binder_path(chrbnd_path, f"c{model_id:04d}.flver")

    for submesh in flver.meshes:

        print(f"\nMATDEF: {submesh.material.mat_def_name}")
        matbin = matbinbnd.get_matbin(submesh.material.mat_def_name)
        matdef = MatDef.from_matbin(matbin)
        print(f"    FLVER Stem: {submesh.material.name}")
        print(f"    Shader Stem: {matdef.shader_stem}")

        mesh_uv_count = submesh.vertex_arrays[0].layout.get_uv_count()
        matdef_uv_layers = matdef.get_used_uv_layers()
        if mesh_uv_count != len(matdef_uv_layers):
            print(f"    {Fore.RED}UV COUNT MISMATCH: {mesh_uv_count} != len({matdef_uv_layers}){Fore.RESET}")

        # Print vertex array layout.
        layout = submesh.vertex_arrays[0].layout
        print("    Layout:")
        for data_type in layout:
            print(f"        {data_type}")
        # Reconstruct layout and compare.
        re_layout = matdef.get_character_layout()
        if re_layout == layout:
            print(f"    {Fore.GREEN}Reconstructed Character Layout:{Fore.RESET}")
        else:
            print(f"    {Fore.RED}Reconstructed Character Layout:{Fore.RESET}")
        for data_type in re_layout:
            print(f"        {data_type}")

        # print("    Params:")
        # for key, value in matdef.matbin_params.items():
        #     print(f"        {key} = {value}")

        # print("    Samplers:")
        # for sampler in matbin.samplers:
        #     print(f"        {sampler.sampler_type} = {sampler.path}")

        all_samplers = {sampler.name: sampler for sampler in matdef.samplers}
        layer_sampler_paths = matdef.get_uv_group_sampler_paths()
        for group, sampler_paths in sorted(layer_sampler_paths.items()):
            print(f"    Sampler Group: {group}")
            for sampler_name, (sampler_path, uv_layer) in sampler_paths.items():
                print(f"        {sampler_name} = \"{Path(sampler_path).stem}\"")
                print(f"            alias = {Fore.YELLOW}{all_samplers[sampler_name].alias}{Fore.RESET}")
                print(f"            uv_layer = {Fore.CYAN}{all_samplers[sampler_name].uv_layer_name}{Fore.RESET}")
                all_samplers.pop(sampler_name)
        if all_samplers:
            print("    UNUSED SAMPLERS:")
            for sampler in all_samplers.values():
                print(f"        ({sampler.sampler_group}) {sampler.name} (UV = {sampler.uv_layer_name})")

        # # Inspecting UVs for 'Mask1Map' materials.
        # if matdef.UVLayer.UVBlend01 in matdef.get_used_uv_layers():
        #     print("    UVs:")
        #     uv_0 = submesh.vertices["uv_0"]
        #     print(uv_0[:5], np.min(uv_0), np.max(uv_0))
        #     uv_1 = submesh.vertices["uv_1"]
        #     print(uv_1[:5], np.min(uv_1), np.max(uv_1))
        #     exit()

        print("    UV ARRAYS:")
        for field_name in submesh.vertices_dtype.names:
            if field_name.startswith("uv_"):
                print(f"        {field_name}: {submesh.vertices[field_name].shape}")


if __name__ == '__main__':
    # for m_id in CHARACTER_MODELS:
    #     test_model(m_id)
    test_model(2030)
