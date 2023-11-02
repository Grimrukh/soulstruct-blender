# Soulstruct for Blender

This Blender add-on enables you to import and export FromSoftware asset files, including FLVER models (Map Pieces, Characters, and Objects), Havok map collision, and Havok animations for characters and objects.

It's powered by [Soulstruct](https://github.com/Grimrukh/soulstruct), my giant Python library of FromSoftware formats, and Soulstruct Havok, an experimental expansion library.

I developed these tools over the years in parallel with the development of Dark Souls: Nightfall, and finally put aside some time to polish and release them. I hope they serve you well and anticipate whatever mods they enable :)

## Table of Contents

- [Installation](#installation)
- [Game Support](#game-support)
- [Upcoming Features](#upcoming-features)
- [Known Issues](#known-issues)
- [Bug Reporting](#bug-reporting)

## Installation

This is an experimental add-on that is not yet published to Blender. To install the add-on manually, follow these steps:

1. Ensure you have **Blender 3.3 or later**, as Python 3.10 is required.
2. Download the add-on `.zip` file from the GitHub repository (Releases).
2. Unzip the contents into your Blender's `scripts/addons` directory. 
    - Typically, the directory is located at `Blender Foundation/Blender/<version>/scripts/addons/`.
    - That directory may also be in `<User>/AppData/Roaming` on Windows, which may be easier to use than the actual Blender installation.
3. Open Blender and go to `Edit > Preferences > Add-ons`.
4. In the Add-ons tab, find `Import-Export: Soulstruct` and enable it by checking the box next to it.

## Basic Usage

The add-on implements many different operators for importing and exporting supported file types.
These can be accessed in the new `Soulstruct` and `Soulstruct Havok` menus on the right of the 3D View.

Each file type has three basic operators:
- **Import**: Browse to a supported file to import into the current scene.
  - If a supported Binder file (`*bnd` or `*bhd`) is selected, a pop-up will ask you which file entry inside that Binder you want to import.
- **Export Loose**: Export the selected object(s) to the supported file type, as a loose file not inside a Binder.
- **Export Into Binder**: Browse to an existing Binder and export the selected object(s) into it.
  - There are export options for controlling how entries are overwritten and/or created.

In addition, each file type has "quick" Import/Export operators that attempt to make it very easy to import
and export supported files from a supported game installation, using the `General Settings` panel in the 3D View or
the `Scene Properties` tab.
- Set the `Game` setting to your game installation folder (the one containing the executable) by browsing or pasting it.
- Ensure that your game files are unpacked, if relevant -- especially the `chr`, `map`, and `obj` data folders.
- Use the `Map Stem` dropdown setting to choose a `map` subfolder for importing/exporting assets.
- Use the appropriate dropdowns

Finally, map assets (Map Pieces, Collisions, and Navmeshes) can be imported and exported with reference
to part entries in the selected map's `MSB` file rather than the raw model files. When `MSB Import Mode` is
enabled, the quick import dropdowns will show lists of MSB parts of that type, which will in turn be used to find
the model files. When imported this way, the name of the Blender object wil

## Object Structure

The add-on imports FLVER models as Blender objects with particular structures that can later be exported.
If you want to create objects from scratch, I recommend simply inspecting and copying the structure of imported
files. Very briefly, the structures are as follows:
- **FLVER**: An `Armature` parent object with a `Mesh` child and any number of empty `Dummy` children.
  - The `Mesh` object must have a handful of custom properties (look at an imported one).
  - The `Mesh` object must have an `Armature` modifier pointing to the parent `Armature` object.
  - The `Mesh` object must have vertex groups named after the bones in the parent `Armature`.
    - Map piece vertices **must be weighted to exactly one bone** with weight 1 (used as a simple offset, e.g., for plants).
    - Character/object vertices **must be weighted to between one and four bones**.
  - The `Dummy` objects must have custom properties named after the bones in the parent `Armature`.
  - Soulstruct automatically **merges all FLVER submeshes** and **splits them on export** based on face material slot.
    - My splitter also handles the maximum per-submesh bone count for DS1 (38) automatically :)
  - You can export a `Mesh` that does not have an `Armature` parent, in which case the FLVER skeleton will have one eponymous bone to which all vertices are weighted.
    - This is fine for, e.g., most map pieces.
  - Material node trees are automatically generated using the MTD parameters of each FLVER material.
    - Soulstruct will attempt to find the `mtdbnd` Binder inside the selected game's `mtd` folder.
      - You can supply a custom `mtdbnd` path in the `General Settings` panel.
      - If the Binder is not found, Soulstruct will guess as much material information as possible just from the name of the MTD.
    - The **names of the texture nodes** in each material are used on export, e.g. `g_Diffuse`.
    - You can otherwise edit the shader to your heart's content; it will not affect export.
- **HKX Map Collision**: An empty parent object with one or more `h*` (hi-res) submeshes and one or more `l*` (lo-res) submeshes.
  - Aside from the mesh data, the only required data is the `material_index` of each submesh.
  - Basic diffuse materials are created so you can distinguish collisions by res (lo/hi) and material index.
  - The material index enum is largely unmapped. Look at examples (solid, water, metal, etc.) to judge.
  - Select the empty parent object of the submeshes to export.
- **NVM**: A single `Mesh` object with material slots used to represent per-face flags.
  - The flag materials are colored for visual convenience.
- **MCG**: A complicated navigation graph that accompanies the navmeshes for each map.
  - TODO.

## Game Support

Currently, the add-on supports **Dark Souls: Remastered** only.

You can probably get away with importing FLVER files from other games, but the import will not
be complete (mainly because of the lack of `GXList` support) and export may not work.

## Upcoming Features

- Support for other games like **Dark Souls: Prepare to Die Edition**, **Dark Souls III**, and **Elden Ring** is in development.
- More comprehensive documentation and video tutorials are coming soon.

## Known Issues

Given the complexity of this add-on, bugs are likely. We appreciate your patience and encourage you to file bug reports.

## Bug Reporting

If you come across any problems or bugs, please file a Git bug report to help us improve the add-on.
