# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

### Added
- `blender_manifest.toml` added — add-on is now a proper Blender Extension package.
- Added this Changelog (with rough collected history).
- Prepare and build scripts for packaging and publishing the extension.
- Experimental Blender type stubs for IDE support.
- Operator registration decorator machinery replacing manual class registration lists.
- Vertex alpha editing tool for the active material.
- **Test suite** for automated operator/import/export testing.
- Cutscene import/export work in progress.
- Mesh generator operators (rocks, bricks, etc.).
- Improved MCG navigation graph generation.
- Significantly improved Elden Ring material shaders.
- On-screen operator progress indicators (cursor percentage).
- Import Equipment FLVER option to parent to existing c0000 armature (armor only).

### Changed
- Blender 5.1 is the minimum supported version (with Python 3.13).
- `soulstruct` 2.4.0 and `soulstruct-havok` 1.3.0 used.
- `Firelink` 0.2.0 used.
- `soulstruct` is now fetched from PyPI rather than bundled.
- All internal imports converted to relative imports.
- Removed `sys.path` manipulation.
- Streamlined FLVER import pipeline.
- Migrated type annotations to `pyrelink`-compatible style; removed `__init__.__all__` boilerplate.
- Degenerate zero-area FLVER faces are now removed on import.
- Stop adding extra suffix to secondary FLVERs in BNDs.

### Fixed
- Fixed animation export bone change-of-basis (CoB) calculation.
- Fixed MSB event name handling.
- Fixed various UI argument and map stem typing bugs.
- Fixed empty FLVER edge case.
- Registered class list errors.
- Fixed animation root motion detection bug for export.
- Animation quaternions coerced to match FromSoft quaternions more.
- Fixed import of large collisions (16-bit → 32-bit combined face indices).
- Fixed cutscene import with bone change-of-basis (compatible with/without CoB).

### Removed
- Support for Blender < 5.1 (Python < 3.13) removed.

---

## [2.6.0] - 2026-03-22

### Added
- "Regenerate FLVER Materials" operator to update shaders to the latest version without re-importing.

### Changed
- FLVER mesh `is_bind_pose` renamed to `is_dynamic` to match SoulsFormats naming.
- FLVER mesh properties (`is_dynamic`, `default_bone_index`, etc.) moved from Blender materials to FLVER
  Mesh properties.
  - Support for a global default and per-mesh overrides.
  - This allows FLVER materials to be shared and merged more easily across opened models.
- Removed "Blender Autocomplete 4.1" IDE folder.
  - Developers should use `fake-bpy-module` from PyPI with the bundled scripts for adding Soulstruct types.

### Fixed
- Import error on add-on installation for some users.
- SciPy version pinned to 1.16.3 to avoid a "read-only array" bug in newer SciPy.
- DSR snow material layouts and shaders.
- Demon's Souls (PS3) navmeshes now export as big-endian.

## [2.5.2] - 2026-03-06

### Added
- Imported FLVERs can now automatically replace Placeholder models and update MSB Part users.

### Fixed
- MSB rotation values (degrees were incorrectly being converted to radians).
- RGBA mix node field name.

## [2.5.1] - 2026-02-27

**First release to officially support Blender 5.0.**

> **Installation note:** Since 2.5.0, third-party dependencies (numpy, SciPy) are no longer bundled.
> They are automatically pip-installed into `addons/modules` on first run.

### Fixed
- Exported vertex layouts for non-Map Piece FLVERs that do not use `is_bind_pose`.
- Elden Ring game map selection and filtering with DLC map filters.
- Deprecated separate/combine color node names updated for Blender 5.0.
- `Bake Bone Pose to Vertices` operator.

## [2.5.0] - 2026-02-16

### Added
- Experimental add-ons for tracking map development progress.
- FLVER bones now form a proper connected skeleton rather than unconnected oriented stubs.
  - **Note:** models imported with older versions will not export correctly; re-import required.

### Changed
- Simplified Blender installation: third-party dependencies are now downloaded automatically rather
  than being bundled in the release zip.
- Huge internal refactoring of MSB handling in Blender.

### Fixed
- Improved material shaders (thanks @thegreatgramcracker).
- Non-Map-Piece FLVERs that do not use bone weights handled correctly (thanks @thegreatgramcracker).
- Map Piece bone hierarchies that are not flat (rare but valid).

## [2.4.0] - 2025-03-19

### Added
- DS1R shader node groups packed as a Blend file and loaded on demand (thanks @thegreatgramcracker).
- All imported models placed in a `Models` root collection; all imported MSBs in an `MSBs` root collection.
- MSB Events now use sub-collections rather than being mixed with MSB Regions.
  - Events parented to a Part/Region still appear as children in the Regions collection.
  - Event names have ` <E>` appended to avoid clashes with identically named Regions (tag stripped on export).
- Detail bumpmap and other "common" textures are now found for all applicable FLVERs.
- Console logger now includes module information for each message.
- `Misc. Soulstruct` operator tab with toggles for visibility of all Model and MSB types.

### Fixed
- PTDE Collisions were incorrectly trying to load DS1R HKXBHD binders.
- DX normal map texture handling.

## [2.3.1-Alpha] - 2025-03-18

> Superseded by [2.4.0]. Included for historical record.

### Added
- Miscellaneous Outliner operators under a new `Misc. Soulstruct` tab.
- User control over whether FLVER Armatures are duplicated to MSB Parts (useful for statically posed Map Pieces).
- Object FLVERs from OBJBNDs now search the appropriate map texture folder for textures.
- General setting to enable/disable debug-level logging in the Blender console.
- Streamlined Animation import operators.
- New operators:
  - Generate map Collision models from Map Piece FLVERs, with textures mapped to collision materials.
  - Generate Navmesh models from Collision models (horizontal face island detection + dissolve/triangulate).
  - Scan and merge identical materials across all selected FLVER models.
  - Batch manipulation of MSB Part draw/display/navmesh groups.

## [2.2.3] - 2025-02-04

### Added
- Auto-export c0000 animations (DS1R) into the correct `c0000_*.anibnd`, or `c0000_dlc.anibnd` if new.
- Improved console log formatting.

### Fixed
- Lookup of initial Binders for partial entry export.

## [2.2.2] - 2025-01-16

### Added
- Support for secondary object FLVER export (e.g. `o1234_1`).
- More accurate Demon's Souls FLVER texture path resolution.

### Fixed
- Demon's Souls MSB collision import.

## [2.2.1] - 2025-01-15

### Added
- FLVER support for Demon's Souls character c2005 (`Cs_Ghost_Param_Wander` material).

### Fixed
- Broken FLVER0 export for Demon's Souls models.

## [2.2.0] - 2025-01-14

### Added
- **Demon's Souls animation import/export** via a new two-way converter for wavelet-compressed animation files.
- Character model name preview when importing a character FLVER.
- Dummy RGBA color property used to color floating dummy IDs in the viewport.
- Dummy IDs shown when any FLVER dummy is selected (not just the Mesh/Armature).
- Warning logged for known missing collision model `h0125B0` in Darkroot Garden.
- Operator to create MSB Regions (cubes) at the 3D cursor location.

### Fixed
- Animation operators working correctly again for DSR and DeS.
- MSB Map Offset, Spawner, and Message event fields.
- MSB Environment events now correctly post-attached to MSB Collisions (fixes m16_00_00_00 New Londo Ruins).

## [2.1.9] - 2024-11-11

### Added
- Support for automatic export of Demon's Souls debug files (non-DCX BNDs, loose FLVERs).
- Import support for ancient Demon's Souls map collisions from m07_01_00_00.

## [2.1.8] - 2024-11-09

### Fixed
- Demon's Souls rigged FLVER export (CHRBND TPF corruption and incorrect FLVER data).
- Demon's Souls Map Piece FLVER export (incorrect array layouts causing wrong textures).
- Demon's Souls NVM import/export.

## [2.1.7] - 2024-10-15

### Fixed
- DCX decompression bug affecting Demon's Souls CHRBND read/write.
- FLVER local bone bounding boxes for Characters/Objects/Parts.

## [2.1.6] - 2024-10-14

### Fixed
- Demon's Souls CHRBND export and other Binder exports.
- "Export into Binder" operators no longer force-add or remove DCX from the selected Binder.
- DSR snow shader bug (was corrupting on import and causing export problems).
- DSR animation export (prevents DSR crashes with exported animations).
- FLVER materials with a missing "wet" tag no longer error.

## [2.1.5] - 2024-10-01

### Fixed
- PTDE animation import/export (hotfix for remaining bug in 2.1.4).

## [2.1.4] - 2024-10-01

> **Superseded by 2.1.5** due to a remaining PTDE animation bug.

### Fixed
- FLVER import bug causing characters with certain cloth materials to be posed incorrectly.
- Animation import and export for PTDE/DSR.

## [2.1.3] - 2024-09-29

### Fixed
- Typo causing "internal error setting the array" for various FLVERs.

## [2.1.2] - 2024-09-27

### Fixed
- Major breaking regressions for all non-Demon's Souls games introduced in 2.1.0.

## [2.1.1] - 2024-09-27

> **Superseded by 2.1.2** — this release added Demon's Souls support but broke other games.

### Fixed
- Numerous Demon's Souls bugs; added support for older FLVER models (e.g. m07_00_00_00).

## [2.1.0] - 2024-09-26

### Added
- **Demon's Souls support**: FLVER, NVM navmesh, HKX map collision, and MSB import/export.
  (Animations not yet included; some FLVER material shaders may be inaccurate.)

## [2.0.1] - 2024-09-09

### Added
- Hugely improved Bloodborne FLVER and material support.
- FLVER material GX Items can be viewed and edited.
- MSB JSON export to a Soulstruct GUI project.

### Fixed
- FLVER vertex merging crash.
- Texture case sensitivity (all textures now normalized to lower case).
- Bug with polling map retrieval.

## [2.0.0] - 2024-09-05

> Requires Blender 4.1 or later.

### Added
- **Fully-functional MSB editor for Dark Souls 1** (both PTDE and DSR).
- New Soulstruct Blender object subtype system for clear representation of FromSoftware formats.
- Full updated README with screenshots.
- Many new convenient operators.

### Changed
- Major performance and visual improvements.

### Fixed
- Mirrored UV handling.
- Tangent map computation.

## [1.9.3] - 2024-06-19

### Added
- `Refresh MCG Names` operator: renames all MCG nodes to reference their connected navmesh models
  (e.g. `Node [20 | 31]`), with instance suffixes for duplicates.

### Fixed
- FLVER tangent and bitangent export (parallax occlusion for `g_Height` shaders now displays correctly).
- Character FLVER import detects more textures automatically.
- Removed redundant scipy copy from release zip.

## [1.9.2] - 2024-06-03

### Fixed
- Blender 4.1 support: `scipy` now bundled for both Python 3.10 and 3.11 so the correct version is
  used automatically without requiring two separate downloads.

## [1.9.1] - 2024-06-02

### Fixed
- Import bug in Soulstruct Havok accidentally left in 1.9.0.

## [1.9.0] - 2024-05-31

### Added
- **Blender 4.1 support** (custom face corner normal handling updated).
- Operators for easy import of Elden Ring Asset models and animations (from `geombnd` binders).
- Elden Ring navmesh import (no export).

### Fixed
- "Import All Animations" option for batch importing HKX animations from a Binder.
- Sharp low-poly edges (e.g. blades) preserved correctly on import/export in Blender 4.1.

## [1.8.0] - 2024-03-15

### Added
- New FLVER/texture convenience operators.
- Foundation for FLVER game conversion workflow.

## [1.7.1] - 2024-03-12

### Fixed
- FLVER vertex count inflation on export: vertices with very similar (but non-identical) normal/tangent
  vectors are now merged. Default dot-product threshold is 0.999 (configurable).

## [1.7.0] - 2024-03-11

### Changed
- Restored split-submesh method for importing/exporting HKX map collisions as default.
  Enable `Merge Submeshes` on import to merge them; materials indicate submesh membership.

## [1.6.0] - 2024-03-01

### Added
- Tentative FLVER import support for Bloodborne and Elden Ring (export not yet supported).

### Fixed
- UV layer names across submeshes better handled and consistently named
  (`UVTexture0`, `UVTexture1`, `UVLightmap`, etc.).
- Disabled broken part of the automatic FLVER mesh triangulation code.
- Fixed `colorama` issue causing endless stdout wrapping.

## [1.5.2] - 2024-02-21

### Fixed
- Regression bugs with HKX collision export.
- Conflicting MCG triangle faces now allowed with a warning (first occurrence taken).

## [1.5.1] - 2024-02-21

### Fixed
- Missing bone pose data for MSB Map Piece part instances.

## [1.5.0] - 2024-02-08

### Added
- All MSB-related operators consolidated into a new `Soulstruct MSB` tab.
- MSB Region importing with draw options in the `MSB Tools` dropdown. (Export not yet supported.)

### Fixed
- CHRBND export for Character FLVERs.
- FLVER custom split normal export (was causing blocky shading).

## [1.4.1] - 2024-02-05

### Fixed
- New exported files not replacing existing ones in Binders.
- Animation export glitches caused by quaternion sign flips.

## [1.4.0] - 2024-02-02

### Added
- Colored map collisions in the viewport.

### Fixed
- Many critical file export bugs.

## [1.3.5] - 2024-01-13

### Fixed
- Enum dropdown lists for entries/parts/maps.
- Importing MSB parts and batch-importing all MSB parts.

## [1.3.4] - 2023-12-22

### Fixed
- Corrupt "exploded" meshes when exporting larger FLVER models (32-bit face set indices).

## [1.3.3] - 2023-12-21

### Added
- **Blender 4.0 support**: specular textures now linked to `Specular IOR Level` input in
  Principled BSDF (renamed in Blender 4.0).

## [1.3.2] - 2023-12-19

### Fixed
- Bug when importing multiple animations simultaneously.
- Leftover root motion bug from 1.3.1.

## [1.3.1] - 2023-12-19

### Fixed
- Root motion rotation data in animations now imported/exported correctly.

## [1.3.0] - 2023-12-19

### Added
- **PTDE support** for FLVERs and other selected file types.
- Dual `Game`/`Project` directory system with `Prefer Import from Project` and `Also Export to Game` options.
- Partial Binder and MSB modification support (only changed entries are written back).

### Fixed
- FLVER bone flags bug that was causing animation glitches.

## [1.2.5] - 2023-11-12

### Fixed
- Critical UV export issues for FLVERs.

## [1.2.4] - 2023-11-11

### Fixed
- Character FLVER bone handling causing export problems.

## [1.2.3] - 2023-11-11

### Fixed
- Critical bugs with exporting character FLVERs.

## [1.2.2] - 2023-11-09

### Added
- MSB Part exporters update the MSB model name and FLVER file stem from the `Model File Stem`
  Blender property, enabling model redirection and duplication without renaming files manually.

### Fixed
- Cross-map texture search bug.

## [1.2.1] - 2023-11-08

### Added
- Bundled MTDBNDs as fallback for standalone usage.

### Fixed
- Unshaded/transparent FLVER materials now exported correctly (e.g. Firelink mist `m6000B2A10`).
- Improved detection and repair of broken QLOC FLVER vertex data layouts.

## [1.2.0] - 2023-11-08

### Added
- **Texture export**: enable `Export Textures` in the FLVER export menu to write DDS textures back
  into the game's TPF/Binder. Only recommended when actually changing textures.
- FLVER importers use a file browser rather than a large dropdown menu.
- MSB transform import/export and part model operators split into separate buttons.

## [1.1.0] - 2023-11-05

### Added
- Support for quick import/export of equipment FLVERs (PARTSBND).
  Equipment is now treated like any other FLVER and can be animated with c0000 animations.

### Removed
- Old specialised "Import Equipment" operator that attempted to parent equipment to c0000.
- Stored bone relationship and usage flag fields no longer needed.

### Fixed
- Import of c0000 (player) FLVER.
- Import of Map Pieces with QLOC-destroyed submeshes (e.g. `m0302B0A14` in Blighttown).
- Export for FLVERs with unused material slots (now ignored).

## [1.0.2] - 2023-11-03

### Fixed
- Regression breaking some FLVER imports introduced in 1.0.1.

## [1.0.1] - 2023-11-03

### Fixed
- Material UV handling bug affecting some Map Piece FLVERs.
- Map Piece FLVERs now search other maps for missing textures (e.g. `m10_*` textures in Darkroot Garden).
- Better error reporting for missing textures.

## [1.0.0] - 2023-11-02

### Added
- Initial release of **Soulstruct for Blender**.
- Dark Souls Remastered FLVER import/export.
- HKX map collision import/export.
- NVM navmesh import/export.
- Animation (HKX) import/export.
- Basic MSB part placement import/export.

