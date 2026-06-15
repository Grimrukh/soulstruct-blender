"""Base class for importing MSB Models (for Parts) to Blender objects.

Note that an exporter is not needed, as Blender model export (FLVER creation, etc.) is not coupled with MSB export.
The MSB export operators do have the option to run the model export operators automatically, but that is handled
elsewhere and does not affect MSB export.
"""
from __future__ import annotations

__all__ = [
    "BaseBlenderMSBModelImporter",
]

import abc
from dataclasses import dataclass

import bpy

from soulstruct.base.maps.msb.models import BaseMSBModel

from .....base.operators import LoggingOperator
from .....types import MeshObject


@dataclass(slots=True)
class BaseBlenderMSBModelImporter(abc.ABC):
    """Finds and imports the various model files referenced by MSB Model entries (used for Part instances).

    Derived classes must implement the `import_model_mesh` method to import the model mesh from the game's model files.
    This generally involves another wrapped Blender Soulstruct object (FLVER/Collision/Navmesh), but its location will
    depend on the MSB Part subtype and its corresponding MSB Model information. They can also optionally implement the
    batch import method.

    The `model` property of the Blender MSB Part will be set to the imported model mesh object.
    """

    use_oldest_map_stem: bool = False

    @abc.abstractmethod
    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
        model_collection: bpy.types.Collection | None = None,
    ) -> MeshObject:
        """Use other Soulstruct for Blender submodules to import model for this MSB Part."""
        ...

    @abc.abstractmethod
    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[BaseMSBModel],
        map_stem: str,
    ) -> None:
        """Import all models for a batch of same-subtype MSB Models, as needed, in parallel as much as possible."""
        ...
