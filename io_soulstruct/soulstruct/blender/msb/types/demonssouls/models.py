from __future__ import annotations

__all__ = [
    "MSB_MODEL_IMPORTERS",
]

from soulstruct.demonssouls.maps.enums import MSBModelSubtype
from soulstruct.demonssouls.constants import CHARACTER_MODELS

from ....msb.types.base.models import *


MSB_MODEL_IMPORTERS = {
    MSBModelSubtype.MapPieceModel: BlenderMSBMapPieceModelImporter(
        use_oldest_map_stem=True,
    ),
    MSBModelSubtype.CollisionModel: BlenderMSBCollisionModelImporter(
        use_oldest_map_stem=True,
        uses_loose=True,
    ),
    MSBModelSubtype.NavmeshModel: BlenderMSBNavmeshModelImporter(
        use_oldest_map_stem=False,
    ),
    MSBModelSubtype.ObjectModel: BlenderMSBObjectModelImporter(),
    MSBModelSubtype.CharacterModel: BlenderMSBCharacterModelImporter(
        model_name_dict=CHARACTER_MODELS
    ),
    MSBModelSubtype.PlayerModel: BlenderMSBCharacterModelImporter(
        model_name_dict=CHARACTER_MODELS
    ),
}
