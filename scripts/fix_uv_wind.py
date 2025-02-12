"""In version 2.3, Soulstruct updated its naming and handling of FLVER UV layers containing wind data.

Formerly, this was confusing, as the Foliage and Ivy layers both have two extra wind data layers, but used them
differently. Foliage always used layer A and was always zero in layer B. Ivy used layer A a little bit (just two points)
and used layer B the same way that Foliage used layer A. So Soulstruct wanted to put Foliage's layer A and Ivy's layer
B in the same UV layer in Blender, as their usage appeared consistent.

I now understand that these layers are just used for wind deformation along different axes, and that the Foliage and Ivy
shaders just want to use these axes differently. So, I have renamed the layers to be more clear:
    `UVData_WindA` (formerly `UVData_WindMain` for Foliage and `UVData_WindIvy` for Ivy)
    `UVData_WindB` (formerly `UVData_WindEmpty` for Foliage and `UVData_WindMain` for Ivy)

This script assist in converting all existing FLVERs in Blender.
"""

import bpy
import bmesh


def copy_uv_layer(src_layer, dst_layer, face):
    """Copy UV data from one layer to another for a specific face."""
    for loop in face.loops:
        src_uv = loop[src_layer].uv
        loop[dst_layer].uv = src_uv


def main(objs: list[bpy.types.Object]):
    # Iterate over each selected mesh object
    for obj in objs:
        if obj.type != "MESH" or obj.soulstruct_type != "FLVER":
            continue

        # noinspection PyTypeChecker
        mesh = obj.data  # type: bpy.types.Mesh

        # Check if 'UVData_WindA' already exists
        if "UVData_WindA" in mesh.uv_layers:
            print(f"Object '{obj.name}' already has 'UVData_WindA'. Skipping.")
            continue

        # Create a BMesh from the object's mesh data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if "UVData_Wind0" in mesh.uv_layers:
            # Fix VERY old UV layer names.
            mesh.uv_layers["UVData_Wind0"].name = "UVData_WindMain"
            mesh.uv_layers["UVData_Wind1"].name = "UVData_WindIvy"

        # Get existing UV layers
        uv_main = bm.loops.layers.uv.get("UVData_WindMain")
        uv_ivy = bm.loops.layers.uv.get("UVData_WindIvy")  # will be None on Foliage-only FLVERs

        if not uv_main:
            # Too common to log this.
            bm.free()
            continue

        # Create new UV layers
        uv_wind_a = bm.loops.layers.uv.new("UVData_WindA")
        uv_wind_b = bm.loops.layers.uv.new("UVData_WindB")

        # Iterate over each face in the mesh
        for face in bm.faces:
            # Get the material assigned to the face
            material_index = face.material_index
            if material_index >= len(obj.material_slots):
                continue  # invalid material index
            material = obj.material_slots[material_index].material
            if not material:
                continue  # no material
            mat_name = material.name

            if "M_2Foliage" in mat_name:
                # Copy UVData_WindMain to UVData_WindA.
                copy_uv_layer(uv_main, uv_wind_a, face)
                # I've confirmed, 100%, that no vanilla Foliage material has any WindB data.
                for loop in face.loops:
                    loop[uv_wind_b].uv = (0.0, 1.0)
            elif "M_3Ivy" in mat_name:
                if not uv_ivy:
                    raise ValueError(f"Object '{obj.name}' has Ivy material but no 'UVData_WindIvy' layer.")
                # Copy UVData_WindMain to UVData_WindB
                copy_uv_layer(uv_main, uv_wind_b, face)
                # Copy UVData_WindIvy to UVData_WindA
                copy_uv_layer(uv_ivy, uv_wind_a, face)
            else:
                # Set UVs to (1, 0) for other materials
                for loop in face.loops:
                    loop[uv_wind_a].uv = (0.0, 1.0)
                    loop[uv_wind_b].uv = (0.0, 1.0)

        # Write the BMesh back to the mesh and free the BMesh
        bm.to_mesh(mesh)
        bm.free()

        # Remove 'UVData_WindMain' and 'UVData_WindIvy' layers (and useless 'UVData_WindEmpty' layer)
        uv_layers_to_remove = ["UVData_WindMain", "UVData_WindIvy", "UVData_WindEmpty"]
        for uv_layer_name in uv_layers_to_remove:
            if uv_layer_name in mesh.uv_layers:
                uv_layer = mesh.uv_layers[uv_layer_name]
                mesh.uv_layers.remove(uv_layer)

        print(f"Processed object '{obj.name}'.")

    print("UV layer processing complete.")


main(list(bpy.data.objects))
