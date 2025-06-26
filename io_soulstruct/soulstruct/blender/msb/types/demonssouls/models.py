from __future__ import annotations

__all__ = [
    "MSB_MODEL_IMPORTERS",
]

from soulstruct.demonssouls.maps.enums import MSBModelSubtype
from soulstruct.demonssouls.maps.models import *
from soulstruct.demonssouls.constants import CHARACTER_MODELS

from soulstruct.blender.msb.types.base.models import *


MSB_MODEL_IMPORTERS = {
    MSBModelSubtype.MapPieceModel: BlenderMSBMapPieceModelImporter(
        MSBMapPieceModel,
        use_oldest_map_stem=True,
    ),
    MSBModelSubtype.CollisionModel: BlenderMSBCollisionModelImporter(
        MSBCollisionModel,
        use_oldest_map_stem=True,
        uses_loose=True,
    ),
    MSBModelSubtype.NavmeshModel: BlenderMSBNavmeshModelImporter(
        MSBNavmeshModel,
        use_oldest_map_stem=False,
    ),
    MSBModelSubtype.ObjectModel: BlenderMSBObjectModelImporter(
        MSBObjectModel,
    ),
    MSBModelSubtype.CharacterModel: BlenderMSBCharacterModelImporter(
        MSBCharacterModel,
        model_name_dict=CHARACTER_MODELS
    ),
    MSBModelSubtype.PlayerModel: BlenderMSBCharacterModelImporter(
        MSBCharacterModel,
        model_name_dict=CHARACTER_MODELS
    ),
}
