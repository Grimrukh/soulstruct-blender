from __future__ import annotations

__all__ = [
    "BlenderMSBCollisionModelImporter_DSR",
]

from soulstruct.darksouls1r.maps.enums import MSBModelSubtype
from soulstruct.darksouls1r.maps.models import *

from soulstruct.blender.msb.types.base.models import *


class BlenderMSBCollisionModelImporter_DSR(BlenderMSBCollisionModelImporter):

    def _handle_missing_hkx(self, operator, model_name: str, map_stem: str):
        if map_stem == "m12_00_00_00" and model_name == "h0125B0A12":
            # This is the special case of the new model in DSR Darkroot Garden.
            operator.warning(
                f"Ignoring known missing model in vanilla DS1R: h0125B0 in m12_00_00_00. This model file "
                f"(a copy of h0017B0 with new groups) was added by QLOC only to the unused m12_00_00_01 HKXBHDs."
            )
        else:
            super()._handle_missing_hkx(operator, model_name, map_stem)


MSB_MODEL_IMPORTERS = {
    MSBModelSubtype.MapPieceModel: BlenderMSBMapPieceModelImporter(MSBMapPieceModel, use_oldest_map_stem=True),
    MSBModelSubtype.CollisionModel: BlenderMSBCollisionModelImporter_DSR(MSBCollisionModel, use_oldest_map_stem=True),
    MSBModelSubtype.NavmeshModel: BlenderMSBNavmeshModelImporter(MSBNavmeshModel, use_oldest_map_stem=False),
    MSBModelSubtype.ObjectModel: BlenderMSBObjectModelImporter(MSBObjectModel),
    MSBModelSubtype.CharacterModel: BlenderMSBCharacterModelImporter(MSBCharacterModel),
    MSBModelSubtype.PlayerModel: BlenderMSBCharacterModelImporter(MSBCharacterModel),
}
