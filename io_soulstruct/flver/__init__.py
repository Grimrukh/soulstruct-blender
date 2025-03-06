from __future__ import annotations

__all__ = [
    # region Materials
    # region Properties
    "MaterialToolSettings",
    "FLVERMaterialProps",
    "FLVERGXItemProps",
    # endregion

    # region Operators
    "SetMaterialTexture0",
    "SetMaterialTexture1",
    "AutoRenameMaterials",
    "MergeFLVERMaterials",
    "AddMaterialGXItem",
    "RemoveMaterialGXItem",
    # endregion

    # region Types
    "BlenderFLVERMaterial",
    # endregion

    # region GUI
    "OBJECT_UL_flver_gx_item",
    "FLVERMaterialPropsPanel",
    "FLVERMaterialToolsPanel",
    # endregion
    # endregion

    # region Models
    # region Operators
    "BakeBonePoseToVertices",
    "ReboneVertices",

    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",

    "ExportLooseFLVER",
    "ExportFLVERIntoBinder",
    "ExportMapPieceFLVERs",
    "ExportCharacterFLVER",
    "ExportObjectFLVER",
    "ExportEquipmentFLVER",

    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportAssetFLVER",
    "ImportEquipmentFLVER",

    "SelectDisplayMaskID",
    "SelectUnweightedVertices",
    "SetSmoothCustomNormals",
    "SetVertexAlpha",
    "InvertVertexAlpha",

    "CopyToNewFLVER",
    "RenameFLVER",
    "SelectMeshChildren",

    "ActivateUVMap",
    "FastUVUnwrap",
    "FastUVUnwrapIslands",
    "RotateUVMapClockwise90",
    "RotateUVMapCounterClockwise90",
    "AddRandomUVTileOffsets",

    "FLVERImportSettings",
    "FLVERExportSettings",

    "BlenderFLVER",
    "BlenderFLVERDummy",

    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
    "FLVERImportPanel",
    "FLVERExportPanel",
    "FLVERModelToolsPanel",
    "FLVERUVMapsPanel",
    # endregion

    # region Properties
    "FLVERProps",
    "FLVERDummyProps",
    "FLVERBoneProps",
    "FLVERImportSettings",
    "FLVERExportSettings",
    # endregion

    # region Types
    "BlenderFLVER",
    "BlenderFLVERDummy",
    "FLVERBoneDataType",
    "FLVERModelType",
    # endregion

    # region GUI
    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
    "FLVERImportPanel",
    "FLVERExportPanel",
    "FLVERModelToolsPanel",
    "FLVERUVMapsPanel",
    # endregion

    # region Draw Handlers
    "draw_dummy_ids",
    # endregion
    # endregion

    # region FLVER Properties
    "FLVERToolSettings",
    # endregion

    # region Images
    # region Properties
    "DDSTextureProps",
    "TextureExportSettings",
    # endregion

    # region Types
    "DDSTexture",
    "DDSTextureCollection",
    # endregion

    # region Operators
    "ImportTextures",
    "FindMissingTexturesInImageCache",
    # "ExportTexturesIntoBinder",
    # endregion

    # region GUI
    "DDSTexturePanel",
    # endregion
    # endregion

    # region Lightmaps
    # region Operators
    "BakeLightmapTextures",
    "BakeLightmapSettings",
    # endregion

    # region GUI
    "FLVERLightmapsPanel",
    # endregion
    # endregion

    # region Utilities
    "get_flvers_from_binder",
    # endregion
]

from .material import *
from .models import *
from .properties import *
from .image import *
from .lightmaps import *
from .utilities import *
