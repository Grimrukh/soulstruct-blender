from pathlib import Path

import numpy as np

from soulstruct.base.models.matbin import MATBINBND
from soulstruct.containers import Binder
from soulstruct.containers.core import EntryNotFoundError
from soulstruct.eldenring.models import FLVER
from soulstruct.config import Config


def main():
    matbinbnd = MATBINBND.from_bundled("ELDEN_RING")

    c2130 = FLVER.from_binder_path(Config.ER_PATH / "chr/c2130.chrbnd.dcx", 200)
    for mesh in c2130.meshes:
        print()
        print(mesh.material.mat_def_name)
        print(mesh.vertices.dtype.names)
        # matbin = matbinbnd.get_matbin(mesh.material.mat_def_name)
        # print(matbin)


def analyze_c2010():
    flver = FLVER.from_path("./dumped_flver/c2010.flver")

    # TODO: Findings:
    #  - Arrays 0 and 2 seem to be 100% identical: position, normal, normal_w, tangent_0
    #  - The tangent_0 value in Array 1 can differ subtly from that in Arrays 0/2:
    #     - tan[3] can be negated
    #     - other

    for mesh in flver:
        if mesh.material.mat_def_name.lower().endswith("_cloth.matxml"):
            # Cloth material.
            if len(mesh.vertex_arrays) != 3:
                print(f"  IGNORING UNEXPECTED Cloth / Array Count = {len(mesh.vertex_arrays)}")
                continue

            print(mesh.material.mat_def_name)

            pos_equal = True
            tan_01_equal = True
            tan_02_equal = True
            nor_equal = True
            nor_w_equal = True

            for v_i in range(len(mesh.vertices)):

                pos_0 = mesh.vertex_arrays[0]['position'][v_i]
                pos_2 = mesh.vertex_arrays[2]['position'][v_i]
                if not np.all(pos_0 == pos_2):
                    print(f"POSITION CLASH at vertex {v_i}: {pos_0} vs {pos_2}")
                    pos_equal = False

                nor_0 = mesh.vertex_arrays[0]['normal'][v_i]
                nor_2 = mesh.vertex_arrays[2]['normal'][v_i]
                if not np.all(nor_0 == nor_2):
                    print(f"NORMAL CLASH at vertex {v_i}: {nor_0} vs {nor_2}")
                    nor_equal = False

                nor_w_0 = mesh.vertex_arrays[0]['normal_w'][v_i]
                nor_w_2 = mesh.vertex_arrays[2]['normal_w'][v_i]
                if not np.all(nor_w_0 == nor_w_2):
                    print(f"NORMAL_W CLASH at vertex {v_i}: {nor_w_0} vs {nor_w_2}")
                    nor_w_equal = False

                tan_0 = mesh.vertex_arrays[0]['tangent_0'][v_i]
                try:
                    tan_1 = mesh.vertex_arrays[1]['tangent_0'][v_i]
                except ValueError:
                    pass
                else:
                    if not np.all(tan_0 == tan_1):
                        print(f"TANGENT 0/1 CLASH at vertex {v_i}: {tan_0} vs {tan_1}")
                        print(f"  bitangent: {mesh.vertex_arrays[1]['bitangent'][v_i]}")
                    else:
                        print(f"  NO CLASH at {v_i}: bitangent: {mesh.vertex_arrays[1]['bitangent'][v_i]}")
                    tan_01_equal = False

                tan_2 = mesh.vertex_arrays[2]['tangent_0'][v_i]
                if not np.all(tan_0 == tan_2):
                    print(f"TANGENT 0/2 CLASH at vertex {v_i}: {tan_0} vs {tan_2}")
                    tan_02_equal = False

            print(mesh.material.mat_def_name)
            print(f"  POSITIONS EQUAL: {pos_equal}")
            print(f"  TANGENT 0/1 EQUAL: {tan_01_equal}")
            print(f"  TANGENT 0/2 EQUAL: {tan_02_equal}")
            print(f"  NORMAL EQUAL: {nor_equal}")
            print(f"  NORMAL_W EQUAL: {nor_w_equal}")


def scan_all_er_flvers():
    """BIG: Load every single ER FLVER and compare mesh VA count to 'GXFT_Cloth' MATBIN param."""
    from soulstruct.utilities.files import write_json

    matbinbnd = MATBINBND.from_bundled("ELDEN_RING")

    dumped_flver_dir = Path("./dumped_flver")
    dumped_flver_dir.mkdir(parents=True, exist_ok=True)

    shader_stem_uv_counts = {}

    def scan_flver(flver: FLVER, path: Path):
        for mesh in flver:
            try:
                matbin = matbinbnd.get_matbin(mesh.material.mat_def_name)
            except KeyError:
                continue
            shader_stem_uv_counts.setdefault(matbin.shader_stem, set()).add(mesh.uv_count)

    def find_scan_flver(binder_path: Path):
        name = binder_path.name.split(".")[0]
        dumped_path = dumped_flver_dir / f"{name}.flver"
        if dumped_path.is_file():
            try:
                _flver = FLVER.from_path(dumped_path)
            except Exception as ex:
                print(f"DUMPED FLVER READ ERROR: {ex}. Skipping {dumped_path}.")
                return
        else:
            binder = Binder.from_path(binder_path)
            try:
                flver_entry = binder.find_entry_by_name_regex(r".*\.flver")
            except EntryNotFoundError:
                print(f"NO FLVER: {binder_path}")
                return
            dumped_path.write_bytes(flver_entry.get_uncompressed_data())
            try:
                _flver = FLVER.from_path(dumped_path)
            except Exception as ex:
                print(f"FLVER READ ERROR: {ex}. Skipping {binder_path}.")
                return

        print(f"FLVER: {dumped_path.name}")
        scan_flver(_flver, binder_path)

    # print("\nScanning CHRBNDs...")
    # for chrbnd_path in (ER_PATH / "chr").glob("*.chrbnd.dcx"):
    #     find_scan_flver(chrbnd_path)
    #
    # chr_lists = {
    #     k: next(iter(v)) if len(v) == 1 else list(v)
    #     for k, v in sorted(shader_stem_uv_counts.items())
    # }
    #
    # write_json("er_shader_uv_counts_chr.json", chr_lists, indent=2)

    shader_stem_uv_counts.clear()

    print("\nScanning GEOMBNDs...")
    for geombnd_path in (Config.ER_PATH / "asset/aeg/aeg001").rglob("*.geombnd.dcx"):
        find_scan_flver(geombnd_path)
    print("\nScanning MAPBNDs...")
    for mapbnd_path in (Config.ER_PATH / "map/m10/m10_00_00_00").glob("*.mapbnd.dcx"):
        find_scan_flver(mapbnd_path)

    asset_lists = {
        k: next(iter(v)) if len(v) == 1 else list(v)
        for k, v in sorted(shader_stem_uv_counts.items())
    }

    write_json("er_shader_uv_counts_asset_map.json", asset_lists, indent=2)

    # print("\nScanning PARTSBNDs...")
    # for partsbnd_path in (ER_PATH / "parts").glob("*.partsbnd.dcx"):
    #     try:
    #         _flver = FLVER.from_binder_path(partsbnd_path)
    #     except EntryNotFoundError:
    #         print(f"NO FLVER: {partsbnd_path}")
    #         continue
    #     print(partsbnd_path)
    #     scan_flver(_flver, partsbnd_path)



def test_merged_mesh_er():
    from soulstruct.flver.mesh_tools import MergedMesh
    from soulstruct.eldenring.models.shaders import MatDef

    matbinbnd = MATBINBND.from_bundled("ELDEN_RING")

    # c2010 = FLVER.from_binder_path(ER_PATH / "chr/c2030.chrbnd.dcx")
    c2010 = FLVER.from_binder_path(Config.ER_PATH / "map/m10/m10_01_00_00/m10_01_00_00_000009.mapbnd.dcx")

    for mesh in c2010:
        if mesh.material.mat_def_stem == "m10_00_877":
            matbin = matbinbnd.get_matbin(mesh.material.mat_def_name)
            print(mesh.material.mat_def_stem, matbin.shader_stem)
            for va in mesh.vertex_arrays:
                for field in va.field_names:
                    print(f"   {field}", va[field].shape)
                    print(va[field][:10])
                    print(np.min(va[field]))
                    print(np.max(va[field]))
                    print(np.mean(va[field]))
    return

    # Get MatDefs.
    matdefs = [
        MatDef.from_matbin(matbinbnd.get_matbin(mesh.material.mat_def_name))
        for mesh in c2010.meshes
    ]

    for mesh, matdef in zip(c2010.meshes, matdefs):
        print(matdef.name, matdef.shader_stem)
        print(matdef.get_used_uv_layers())

    # merged_mesh = MergedMesh.from_flver(
    #     c2010,
    #     mesh_material_indices=list(range(len(c2010.meshes))),
    #     material_uv_layer_names=[matdef.get_used_uv_layers() for matdef in matdefs],
    # )


def test_plant():
    from soulstruct.eldenring.models.shaders import MatDef

    binder = Binder.from_path(Config.ER_PATH / "map/m10/m10_01_00_00/m10_01_00_00_000033.mapbnd.dcx")
    flver = binder[200].to_binary_file(FLVER)

    matbinbnd = MATBINBND.from_bundled("ELDEN_RING")
    matbin = matbinbnd.get_matbin(flver.meshes[4].material.mat_def_name)
    matdef = MatDef.from_matbin(matbin)


if __name__ == '__main__':
    # analyze_c2010()
    # scan_all_er_flvers()
    # test_merged_mesh_er()
    test_plant()
