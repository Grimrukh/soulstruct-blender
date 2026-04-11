"""Retrieve and cache game MTDBND/MATBINBND binders."""

__all__ = [
    "get_mtdbnd",
    "get_matbinbnd",
    "get_cached_mtdbnd",
    "get_cached_matbinbnd",
    "clear_cached_matdefs",
]

import bpy

from soulstruct.base.models.matbin import MATBINBND
from soulstruct.base.models.mtd import MTDBND
from soulstruct.games import Game

from ..base.operators import LoggingOperator
from ..exceptions import InternalSoulstructBlenderError
from ..utilities import *


def get_mtdbnd(operator: LoggingOperator, context: bpy.types.Context) -> MTDBND:
    """Load `MTDBND` from custom path, standard location in game directory, or bundled Soulstruct file.

    Should not be called for games that do not use MTDs. Otherwise, always finds a `MTDBND` or we have an error.
    """
    settings = context.scene.soulstruct_settings
    game = settings.game

    if settings.game_config.uses_matbin:
        raise InternalSoulstructBlenderError(f"Active game '{game.name}' does not use MTDs. Should not call this.")

    custom_path = settings.mtdbnd_path
    if is_path_and_file(custom_path):
        return MTDBND.from_path(custom_path)

    # Try to find MTDBND in project or game directory. We know their names from the bundled versions in Soulstruct,
    # but only fall back to those actual bundled files if necessary.
    mtdbnd_names = [
        resource_path.name
        for resource_key, resource_path in game.bundled_resource_paths.items()
        if resource_key.endswith("MTDBND")
    ]

    if settings.prefer_import_from_project:
        labelled_roots = (("project", settings.project_root), ("game", settings.game_root))
    else:
        labelled_roots = (("game", settings.game_root), ("project", settings.project_root))

    mtdbnd = None  # type: MTDBND | None
    for label, root in labelled_roots:
        if not root:
            continue
        for mtdbnd_name in mtdbnd_names:
            dir_mtdbnd_path = root.get_file_path(f"mtd/{mtdbnd_name}")
            if dir_mtdbnd_path.is_file():
                operator.debug(f"Found MTDBND '{dir_mtdbnd_path.name}' in {label} directory: {dir_mtdbnd_path}")
                if mtdbnd is None:
                    mtdbnd = MTDBND.from_path(dir_mtdbnd_path)
                else:
                    mtdbnd |= MTDBND.from_path(dir_mtdbnd_path)
    if mtdbnd is not None:  # found
        return mtdbnd

    operator.info(f"Loading bundled MTDBND for game {game.name}...")
    return MTDBND.from_bundled(game)


def get_matbinbnd(operator: LoggingOperator, context: bpy.types.Context) -> MATBINBND:
    """Load `MATBINBND` from custom path, standard location in game directory, or bundled Soulstruct file.

    Should not be called for games that do not use MATBINs. Otherwise, always finds a `MATBINBND` due to the final
    bundled file fallback, or an error has occurred.
    """

    settings = context.scene.soulstruct_settings
    game = settings.game

    if not settings.game_config.uses_matbin:
        raise InternalSoulstructBlenderError(
            f"Active game '{game.name}' does not use MATBINs. Should not call this."
        )

    custom_path = settings.matbinbnd_path
    if is_path_and_file(custom_path):
        return MATBINBND.from_path(custom_path)

    # Try to find MATBINBND in project or game directory.
    matbinbnd_names = [
        resource_path.name
        for resource_key, resource_path in game.bundled_resource_paths.items()
        if resource_key.endswith("MATBINBND")
    ]

    if settings.prefer_import_from_project:
        labelled_roots = (("project", settings.project_root), ("game", settings.game_root))
    else:
        labelled_roots = (("game", settings.game_root), ("project", settings.project_root))

    matbinbnd = None  # type: MATBINBND | None
    for label, root in labelled_roots:
        if not root:
            continue
        for matbinbnd_name in matbinbnd_names:
            dir_matbinbnd_path = root.get_file_path(f"material/{matbinbnd_name}")
            if dir_matbinbnd_path.is_file():
                operator.info(
                    f"Found MATBINBND '{dir_matbinbnd_path.name}' in {label} directory: {dir_matbinbnd_path}"
                )
                if matbinbnd is None:
                    matbinbnd = MATBINBND.from_path(dir_matbinbnd_path)
                else:
                    matbinbnd |= MATBINBND.from_path(dir_matbinbnd_path)
    if matbinbnd is not None:  # found
        return matbinbnd

    operator.info(f"Loading bundled MATBINBND for game {game.name}...")
    return MATBINBND.from_bundled(game)


# These are cached per-game on first load, which also preserves lazily loaded entries. They can be cleared with
# `clear_cached_matdefs`()`.
_CACHED_MTDBNDS: dict[Game, MTDBND] = {}
_CACHED_MATBINBNDS: dict[Game, MATBINBND] = {}


def get_cached_mtdbnd(operator: LoggingOperator, context: bpy.types.Context) -> MTDBND:
    settings = context.scene.soulstruct_settings
    game = settings.game
    if game not in _CACHED_MTDBNDS:
        _CACHED_MTDBNDS[game] = get_mtdbnd(operator, context)
    return _CACHED_MTDBNDS[game]


def get_cached_matbinbnd(operator: LoggingOperator, context: bpy.types.Context) -> MATBINBND:
    settings = context.scene.soulstruct_settings
    game = settings.game
    if game not in _CACHED_MATBINBNDS:
        _CACHED_MATBINBNDS[game] = get_matbinbnd(operator, context)
    return _CACHED_MATBINBNDS[game]


def clear_cached_matdefs():
    _CACHED_MTDBNDS.clear()
    _CACHED_MATBINBNDS.clear()
