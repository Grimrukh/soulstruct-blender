"""Adds a class that can adapt MSB Entry references between MSBs and Blender.

Includes simple name adapter functions for each Entry subtype (used in multiple places for finding referenced Blender
objects and setting `MSBEntry.name` correctly for the supertype).
"""
from ....types.field_adapters import *
from .groups import MSBPartGroupsAdapter
from .model import MSBPartModelAdapter
from .reference import MSBReferenceFieldAdapter
from .transform import MSBTransformFieldAdapter
from .names import *
