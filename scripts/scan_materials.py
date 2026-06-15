from pathlib import Path

from soulstruct.base.models.mtd import MTDBND
from soulstruct.darksouls1r.models.shaders import MatDef
from soulstruct.flver import FLVER
from soulstruct.flver.vertex_array_layout import *
from soulstruct.config import Config

"""
THE FACTS:
- Every character FLVER material/submesh has 1+ UVs.
- Every object FLVER material/submesh has 1+ UVs.
- 'is_dynamic' just inserts VertexBoneWeights at layout index 2 (after compulsory VertexBoneIndices).
- Some character/object MatDefs have no Tangent data (but all DO have DSB 0 Normal sampler):
    Ps_Hair[DS]
    C[D]
    C5250_Fire[D]_Add
    P[D]
    S[NL]
"""

NON_DYNAMIC_LAYOUT = VertexArrayLayout(
    VertexPosition(VertexDataFormatEnum.Float3, 0),
    VertexBoneIndices(VertexDataFormatEnum.FourBytesB, 0),
    VertexNormal(VertexDataFormatEnum.FourBytesC, 0),
    VertexTangent(VertexDataFormatEnum.FourBytesC, 0),
    VertexColor(VertexDataFormatEnum.FourBytesC, 0),
)


def scan_characters():
    mtdbnd = MTDBND.from_bundled("DARK_SOULS_DSR")
    # for binder in (DSR_PATH / "chr").glob("*.chrbnd.dcx"):
    for binder in (Config.DSR_PATH / "obj").glob("*.objbnd.dcx"):
        flver = FLVER.from_binder_path(binder, f"{binder.stem.split('.')[0]}.flver")
        for submesh in flver.meshes:

            mtd = mtdbnd.get_mtd(submesh.material.mat_def_name)
            matdef = MatDef.from_mtd(mtd)
            has_bitangent = submesh.layout.has_vertex_data_type("bitangent")
            has_dsb_normal_1 = bool(matdef.get_sampler_with_alias("DSB 1 Normal"))

            # Print cases where bitangent is used but DSB 1 Normal is not, or vice versa.
            if has_bitangent and not has_dsb_normal_1:
                print()
                print(f"{binder.stem}: {submesh.material.mat_def_name} uses bitangent but has no DSB 1 Normal sampler.")
                print(matdef)
                print(submesh.layout)
            elif not has_bitangent and has_dsb_normal_1:
                print()
                print(f"{binder.stem}: {submesh.material.mat_def_name} has DSB 1 Normal sampler but does not use bitangent.")
                print(matdef)
                print(submesh.layout)

def check_snow_mp():
    mtdbnd = MTDBND.from_bundled("DARK_SOULS_DSR")
    # flver = FLVER.from_path(Config.DSR_PATH / "map/m11_00_00_00/m2000B0A11.flver.dcx")
    flver = FLVER.from_path(Config.DSR_PATH / "map/m11_00_00_00/m1020B0A11.flver.dcx")

    for submesh in flver.meshes:
        mtd = mtdbnd.get_mtd(submesh.material.mat_def_name)
        matdef = MatDef.from_mtd(mtd)
        if matdef.stem == "A11_Snow":
            print(matdef)
            for sampler in matdef.samplers:
                print(sampler.name, sampler.uv_layer_name)
            # Create a visualization of each UV layer in the mesh.
            print(submesh.vertices.dtype)
            uv_0 = submesh.vertices["uv_0"]
            uv_1 = submesh.vertices["uv_1"]
            import matplotlib.pyplot as plt
            _, axes = plt.subplots(1, 2, figsize=(10, 5))
            axes[0].scatter(uv_0[:, 0], uv_0[:, 1], label="UV 0")
            axes[1].scatter(uv_1[:, 0], uv_1[:, 1], label="UV 1")
            plt.legend()
            plt.title(f"{submesh.material.mat_def_name} UV Layout")
            plt.show()


def scan_map_pieces():
    """
    TODO:
        - A11_Snow* shaders have their weird extra Normal samplers, but no bitangents (ever).
            - Checking for DSB 1 Albedo == bitangent is a safer bet. Only fails for weird A99 7Metal shaders.

    """
    mtdbnd = MTDBND.from_bundled("DARK_SOULS_DSR")
    for map_piece_path in (Config.DSR_PATH / "map").rglob("*.flver.dcx"):
        flver = FLVER.from_path(map_piece_path)
        for submesh in flver.meshes:

            mtd = mtdbnd.get_mtd(submesh.material.mat_def_name)
            matdef = MatDef.from_mtd(mtd)
            has_bitangent = submesh.layout.has_vertex_data_type("bitangent")
            has_dsb_normal_1 = bool(matdef.get_sampler_with_alias("DSB 1 Normal"))
            has_dsb_albedo_1 = bool(matdef.get_sampler_with_alias("DSB 1 Albedo"))

            # Print cases where bitangent is used but DSB 1 Normal is not, or vice versa.
            if has_bitangent and not has_dsb_albedo_1:
                print()
                print(f"{map_piece_path.stem}: {submesh.material.mat_def_name} uses bitangent but has no DSB 1 Normal sampler.")
                print(matdef)
                print(submesh.layout)
            elif not has_bitangent and has_dsb_albedo_1:
                print()
                print(f"{map_piece_path.stem}: {submesh.material.mat_def_name} has DSB 1 Normal sampler but does not use bitangent.")
                print(matdef)
                print(submesh.layout)


def main():

    mtdbnd = MTDBND.from_bundled("DARK_SOULS_DSR")
    mtdbnd.load_all_mtds()

    c2670 = FLVER.from_binder_path(Config.DSR_PATH / "chr/c2670.chrbnd.dcx", "c2670.flver")

    for submesh in c2670.meshes:
        print(submesh.material.name, submesh.material.mat_def_name)
        print(submesh.layout)
    return

    for name, mtd in mtdbnd.mtds.items():
        matdef = MatDef.from_mtd(mtd)

        has_normal_0 = bool(matdef.get_sampler_with_alias("DSB 0 Normal"))
        has_normal_1 = bool(matdef.get_sampler_with_alias("DSB 1 Normal"))
        uv_count = len(matdef.get_used_uv_layers())
        is_character = name.startswith("C")

        # PREDICTION: All Character materials

if __name__ == "__main__":
    # scan_characters()
    scan_map_pieces()
    # check_snow_mp()
    # main()
