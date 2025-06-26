from __future__ import annotations

__all__ = [
    "MSBPartModelAdapter",
]

import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.blender.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb import MSB as BaseMSB
    from soulstruct.base.maps.msb.models import BaseMSBModel
    from soulstruct.base.maps.msb.parts import BaseMSBPart


@dataclass(slots=True)
class MSBPartModelAdapter:
    """Adapter for MSB Part models.

    Does NOT inherit from `SoulstructFieldAdapter` because it is much more complicated: the model needs to be found
    BEFORE we create the Part object, so we can assign it as the (shared) Mesh data-block.

    These models are imported from the MSB first and this class just resolves them between MSB Model references (in
    the `model` field of each Part) and Blender objects of the right `SoulstructType` (FLVER/Collision/Navmesh).

    If a model name is missing, a placeholder model object (`MSB_MODEL_PLACEHOLDER`) is created in Blender.
    """
    bl_model_type: tp.Literal[SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH]
    msb_model_class: type[BaseMSBModel]

    def get_blender_model(
        self,
        context: bpy.types.Context,
        model_name: str,
    ) -> bpy.types.MeshObject:
        """Find or create actual Blender model mesh. Not necessarily a FLVER mesh!"""
        model = find_obj(model_name, ObjectType.MESH, self.bl_model_type, bl_name_func=get_model_name)

        if not model:
            # Search for existing `MSB_MODEL_PLACEHOLDER` Mesh object.
            model = find_obj(
                model_name,
                object_type=ObjectType.MESH,
                soulstruct_type=SoulstructType.MSB_MODEL_PLACEHOLDER,
                bl_name_func=get_model_name,
            )

        if not model:
            # Create placeholder object.
            return self._create_placeholder_model_obj(context, model_name)

        return model

    def set_msb_model(
        self,
        operator: LoggingOperator,
        model: bpy.types.MeshObject,
        part: BaseMSBPart,
        msb: BaseMSB,
        map_stem: str,
    ) -> None:
        """Detect `model` name and call `msb.auto_model()` to find or create the MSB model entry of matching subtype.

        This doesn't strictly fit the Adapter pattern, as it relies on an `MSB` method that already knows how to find
        or create the appropriate Model entry for a given Part entry. Model is assigned to `part` automatically and is
        not returned here.
        """
        if not model:
            # Warnable offense.
            operator.warning(f"MSB Part '{part.name}' has no model set in Blender.")
            return

        # We use the `MSBModel` subclass method to resolve the MSB model name (usually shorter than file name).
        model_stem = get_model_name(model.name)
        msb_model_name = self.msb_model_class.model_file_stem_to_model_name(model_stem)
        msb.auto_model(part, msb_model_name, map_stem)

    def _create_placeholder_model_obj(self, context: bpy.types.Context, model_name: str) -> bpy.types.MeshObject:

        # Create placeholder icosphere.
        mesh = bpy.data.meshes.new(model_name)
        self._build_placeholder_mesh_pyramid_arrow(mesh)
        model = new_mesh_object(model_name, mesh, SoulstructType.MSB_MODEL_PLACEHOLDER)
        model.show_axis = True  # hard to tell orientation of placeholder icosphere otherwise
        placeholder_model_collection = find_or_create_collection(
            context.scene.collection, "Models", "Placeholder Models"
        )
        placeholder_model_collection.objects.link(model)
        return model

    @staticmethod
    def _build_placeholder_mesh_pyramid_arrow(mesh: bpy.types.Mesh):
        verts = [
            (-0.2500, -0.2500, 0.0000),
            (0.2500, -0.2500, 0.0000),
            (0.2500, 0.2500, 0.0000),
            (-0.2500, 0.2500, 0.0000),
            (0.0000, 0.0000, 1.0000),
            (0.1526, 0.3000, 0.7718),
            (0.0000, 0.5000, 0.7718),
            (-0.1525, 0.3000, 0.7718),
            (0.1526, 0.3000, 0.6718),
            (0.0000, 0.5000, 0.6718),
            (-0.1525, 0.3000, 0.6718),
            (-0.0510, -0.0000, 0.7718),
            (-0.0510, 0.3000, 0.7718),
            (0.0510, 0.0000, 0.7718),
            (0.0510, 0.3000, 0.7718),
            (-0.0510, -0.0000, 0.6718),
            (-0.0510, 0.3000, 0.6718),
            (0.0510, 0.0000, 0.6718),
            (0.0510, 0.3000, 0.6718),
        ]

        faces = [
            (0, 1, 2, 3),
            (0, 1, 4),
            (1, 2, 4),
            (2, 3, 4),
            (3, 0, 4),
            (10, 8, 9),
            (5, 6, 9, 8),
            (6, 7, 10, 9),
            (17, 13, 11, 15),
            (12, 16, 15, 11),
            (14, 13, 17, 18),
            (7, 10, 16, 12),
            (8, 5, 14, 18),
            (12, 11, 13, 14),
            (7, 6, 5),
            (18, 17, 15, 16),
        ]

        mesh.clear_geometry()
        mesh.from_pydata(verts, [], faces)
        mesh.update()

    @staticmethod
    def _build_placeholder_mesh_icosphere(mesh: bpy.types.Mesh):
        """Used as a dummy mesh for non-imported Part models.

        TODO: Doesn't convey orientation as well as I'd like (without axes visible).
        """
        verts = [
            (0.0000, 0.0000, -1.0000),
            (0.7236, -0.5257, -0.4472),
            (-0.2764, -0.8506, -0.4472),
            (-0.8944, 0.0000, -0.4472),
            (-0.2764, 0.8506, -0.4472),
            (0.7236, 0.5257, -0.4472),
            (0.2764, -0.8506, 0.4472),
            (-0.7236, -0.5257, 0.4472),
            (-0.7236, 0.5257, 0.4472),
            (0.2764, 0.8506, 0.4472),
            (0.8944, 0.0000, 0.4472),
            (0.0000, 0.0000, 1.0000),
        ]
        faces = [
            (0, 1, 2),
            (1, 0, 5),
            (0, 2, 3),
            (0, 3, 4),
            (0, 4, 5),
            (1, 5, 10),
            (2, 1, 6),
            (3, 2, 7),
            (4, 3, 8),
            (5, 4, 9),
            (1, 10, 6),
            (2, 6, 7),
            (3, 7, 8),
            (4, 8, 9),
            (5, 9, 10),
            (6, 10, 11),
            (7, 6, 11),
            (8, 7, 11),
            (9, 8, 11),
            (10, 9, 11),
        ]
        mesh.clear_geometry()
        mesh.from_pydata(verts, [], faces)
        mesh.update()
