"""Base class for importing MSB Models (for Parts) to Blender objects.

Note that an exporter is not needed, as Blender model export (FLVER creation, etc.) is not coupled with MSB export.
The MSB export operators do have the option to run the model export operators automatically, but that is handled
elsewhere and does not affect MSB export.
"""
from __future__ import annotations

__all__ = [
    "BaseBlenderMSBModelImporter",
    "MODEL_T",
]

import abc
import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.base.maps.msb.models import BaseMSBModel

from io_soulstruct.exceptions import BatchOperationUnsupportedError
from io_soulstruct.utilities.operators import LoggingOperator


MODEL_T = tp.TypeVar("MODEL_T", bound=BaseMSBModel)


@dataclass(slots=True)
class BaseBlenderMSBModelImporter(abc.ABC, tp.Generic[MODEL_T]):
    """Finds and imports the various model files referenced by MSB Model entries (used for Part instances).

    Derived classes must implement the `import_model_mesh` method to import the model mesh from the game's model files.
    This generally involves another wrapped Blender Soulstruct object (FLVER/Collision/Navmesh), but its location will
    depend on the MSB Part subtype and its corresponding MSB Model information. They can also optionally implement the
    batch import method.

    The `model` property of the Blender MSB Part will be set to the imported model mesh object.
    """

    msb_model_class: type[MODEL_T]
    use_oldest_map_stem: bool = False

    @abc.abstractmethod
    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Use other Soulstruct for Blender submodules to import model for this MSB Part."""
        ...

    @abc.abstractmethod
    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
    ) -> None:
        """Import all models for a batch of same-subtype MSB Models, as needed, in parallel as much as possible."""
        ...
