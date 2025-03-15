from __future__ import annotations

__all__ = [
    "MSB_MODEL_IMPORTERS",
]

from soulstruct.demonssouls.maps.enums import MSBModelSubtype
from soulstruct.demonssouls.maps.models import *

from io_soulstruct.msb.types.base.models import *


MSB_MODEL_IMPORTERS = {
    MSBModelSubtype.MapPieceModel: BlenderMSBMapPieceModelImporter(MSBMapPieceModel),
    MSBModelSubtype.CollisionModel: BlenderMSBCollisionModelImporter(MSBCollisionModel),
    MSBModelSubtype.NavmeshModel: BlenderMSBNavmeshModelImporter(MSBNavmeshModel),
    MSBModelSubtype.ObjectModel: BlenderMSBObjectModelImporter(MSBObjectModel),
    MSBModelSubtype.CharacterModel: BlenderMSBCharacterModelImporter(MSBCharacterModel),
    MSBModelSubtype.PlayerModel: BlenderMSBCharacterModelImporter(MSBCharacterModel),
}
