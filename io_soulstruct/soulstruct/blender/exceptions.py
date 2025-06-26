__all__ = [
    "SoulstructBlenderError",
    "InternalSoulstructBlenderError",
    "UnsupportedGameError",
    "UnsupportedGameTypeError",
    "ObjectTypeError",
    "SoulstructTypeError",
    "FLVERError",
    "FLVERImportError",
    "FLVERExportError",
    "MaterialImportError",
    "TextureExportError",
    "MapCollisionImportError",
    "MapCollisionExportError",
    "CutsceneImportError",
    "CutsceneExportError",
    "NVMImportError",
    "NavGraphImportError",
    "NavGraphMissingNavmeshError",
    "NavGraphExportError",
    "MCGEdgeCreationError",
    "NVMHKTImportError",
    "MissingPartModelError",
    "MissingMSBEntryError",
    "MSBPartImportError",
    "MSBPartExportError",
    "MSBRegionImportError",
    "AnimationImportError",
    "AnimationExportError",
    "BatchOperationUnsupportedError",
]

from soulstruct.exceptions import SoulstructError


class SoulstructBlenderError(SoulstructError):
    """Base error for Blender operations."""
    pass


class InternalSoulstructBlenderError(SoulstructBlenderError):
    """Raised when an internal error (author's fault) occurs in the Blender plugin."""
    pass


class UnsupportedGameError(SoulstructBlenderError):
    """Raised when trying to do something not supported for the selected game."""
    pass


class UnsupportedGameTypeError(SoulstructBlenderError):
    """Raised when trying to handle an unsupported Soulstruct type for an otherwise supportede game."""
    pass


class ObjectTypeError(SoulstructBlenderError):
    """Raised when the `type` of a Blender object is not as expected or when object is `None`."""
    pass


class SoulstructTypeError(SoulstructBlenderError):
    """Raised when the `soulstruct_type` of a Blender object is not as expected."""
    pass


class FLVERError(SoulstructBlenderError):
    """Exception raised by a FLVER-based operator error."""


class FLVERImportError(FLVERError):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(FLVERError):
    """Exception raised during FLVER export."""
    pass


class MaterialImportError(SoulstructBlenderError):
    """Error raised during material shader creation. Generally non-fatal, as the critical texture nodes required for
    export are typically easy to create. This just means a more faithful shader couldn't be built."""
    pass


class TextureExportError(SoulstructBlenderError):
    """Raised when there is a problem exporting textures."""


class MapCollisionImportError(SoulstructBlenderError):
    pass


class MapCollisionExportError(SoulstructBlenderError):
    pass


class CutsceneImportError(SoulstructBlenderError):
    """Exception raised during HKX cutscene import."""
    pass


class CutsceneExportError(SoulstructBlenderError):
    """Exception raised during HKX cutscene export."""
    pass


class NVMImportError(SoulstructBlenderError):
    """Exception raised during NVM import."""
    pass


class NVMExportError(SoulstructBlenderError):
    """Exception raised during NVM export."""
    pass


class NavGraphImportError(SoulstructBlenderError):
    """Exception raised during NavGraph import."""
    pass


class NavGraphMissingNavmeshError(NavGraphImportError):
    """Exception raised during NavGraph import when an MSB Navmesh is not found."""
    pass


class NavGraphExportError(SoulstructBlenderError):
    """Exception raised during NavGraph export."""
    pass


class MCGEdgeCreationError(SoulstructBlenderError):
    """Exception raised during MCG edge creation."""
    pass


class NVMHKTImportError(SoulstructBlenderError):
    """Exception raised during NVMHKT import."""
    pass


class MissingPartModelError(SoulstructBlenderError):
    """Raised when the model for an MSB Part is not set (on export) or cannot be found in Blender."""


class MissingMSBEntryError(SoulstructBlenderError):
    """Raised when a reference MSB entry (by name) is missing from the MSB file on entry export."""
    pass


class MSBPartImportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""


class MSBPartExportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""


class MSBRegionImportError(SoulstructBlenderError):
    """Raised by any problem with importing an MSB Region instance."""


class AnimationImportError(SoulstructBlenderError):
    """Exception raised during HKX animation import."""
    pass


class AnimationExportError(SoulstructBlenderError):
    """Exception raised during HKX animation export."""
    pass


class BatchOperationUnsupportedError(SoulstructBlenderError):
    """Raised when a batch operation is not supported for the selected game/file type."""
    pass
