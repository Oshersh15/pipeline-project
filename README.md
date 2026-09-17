# Asset and Shot Publishing Tool for DCC Pipelines

## Overview

This project implements an asset and shot publishing tool for Digital Content Creation (DCC) workflows, using Autodesk Maya as the current authoring integration. It began as an MSc USD asset-publishing project and is being extended into a cross-DCC production pipeline.

The system focuses on production-oriented publish workflows including:

- Automated validation
- Version-controlled publishing
- USD and OBJ asset export
- Versioned Alembic shot-animation publishing
- MongoDB/GridFS asset storage
- Asset retrieval and local cache workflows
- Role-based permissions
- Cross-DCC USD asset testing in Houdini Solaris

The project demonstrates a modular pipeline-oriented architecture designed around structured asset publishing and backend-driven asset management.

---

# Features

The tool includes:

- Automated asset validation
- JSON-configurable validation rules
- Automatic naming correction
- Frozen transform validation
- Structured version-controlled publishing
- USD export and post-processing
- OBJ export
- Baked Alembic animation cache export
- Shot- and department-aware versioning
- Automatic or custom animation frame ranges
- Maya shot-animation publishing dialog
- Preview image generation
- MongoDB metadata storage
- GridFS asset package storage
- Retrieval of published assets to local cache
- Role-based authentication
- Maya integration using PySide2 / PySide6
- Published asset browsing UI
- Cross-DCC USD testing in Houdini Solaris
- Unit, integration, and Maya tests

---

# Validation

Before publishing, assets are validated against configurable production rules.

Validation checks include:

- Naming convention validation
- Lowercase naming enforcement
- Object-type validation
- Frozen transform validation
- Empty transform detection
- Export eligibility checks

Validation rules are stored externally using JSON configuration files, allowing rule behaviour to be modified without changing the publishing logic.

Validation results are displayed directly inside the Maya interface before publishing proceeds.

---

# Static Asset Publishing Workflow

The publishing workflow performs the following stages:

1. Asset validation
2. Optional automatic name correction
3. Version generation
4. USD and OBJ export
5. Preview image generation
6. Metadata generation
7. USD post-processing
8. Asset package creation
9. GridFS storage
10. Temporary publish cleanup

Published assets are packaged into versioned archives and stored within MongoDB GridFS.

Temporary local publish folders are removed after packaging and storage.

---

# Shot Animation Publishing Workflow

Maya artists can publish selected animation roots as baked Alembic caches from the main tool interface.

The workflow performs the following stages:

1. Require an authenticated user and Maya selection
2. Format the supplied shot number, such as `10` to `shot010`
3. Use the Maya playback range or a validated custom frame range
4. Calculate the next version for the shot, asset, and department
5. Export the selected roots as an Ogawa Alembic cache
6. Verify that Maya created the expected file
7. Write shot and animation metadata
8. Package the cache and metadata as a ZIP archive
9. Store the package in GridFS
10. Save searchable publish metadata in MongoDB

Example local publish structure:

```text
tmp_publish_cache/
    shots/
        shot010/
            animation/
                heroCharacter/
                    v001/
                        shot010_heroCharacter_anim.abc
                        metadata.json
```

Shot metadata includes the department, frame range, source and target DCCs, publish format, and the currently required Maya-to-Houdini scale factor.

---

# USD Workflow

USD is currently used for static asset publishing and cross-DCC asset testing. Shot animation is currently delivered as Alembic. A future Houdini/Solaris phase will introduce those publishes into composed USD shot stages.

The USD workflow includes:

- Maya USD export
- USD post-processing using Pixar `pxr`
- Automatic `defaultPrim` assignment
- Root prim validation
- Embedded metadata
- World transform preservation
- Validation in Houdini Solaris

Embedded USD metadata includes:

- Asset name
- Asset type
- Author
- Version
- Source scene path

Cross-DCC testing was performed by retrieving published USD assets from GridFS and loading them into Houdini Solaris. USD shot composition, departmental shot layers, and automated Houdini loading are planned work rather than current functionality.

---

# Asset Storage and Retrieval

MongoDB is used for metadata tracking and GridFS is used for asset package storage.

Stored metadata includes:

- Asset names
- Asset types
- Versions
- Publish timestamps
- Export paths
- Package identifiers
- Author information

Published packages can be retrieved into a structured local cache:

```text
asset_cache/
    model/
        asset_name/
            v001/
```

This allows published assets to be opened in external DCC applications such as Houdini.

Shot-animation retrieval paths use their shot context:

```text
asset_cache/
    shots/
        shot010/
            animation/
                heroCharacter/
                    v001/
```

The repository layer supports this shot-aware retrieval structure. A dedicated Houdini-facing browser and loader have not yet been implemented.

---

# Roles and Permissions

The system includes role-based authentication with three user roles:

| Permission | Admin | Artist | Viewer |
|---|---|---|---|
| Validate assets | ✓ | ✓ | ✗ |
| Publish assets | ✓ | ✓ | ✗ |
| Modify validation rules | ✓ | ✗ | ✗ |
| Delete published assets | ✓ | ✗ | ✗ |
| Browse published assets | ✓ | ✓ | ✓ |
| Import assets into Maya | ✓ | ✓ | ✓ |
| Retrieve assets to cache | ✓ | ✓ | ✓ |

---

# Maya Integration

The tool is implemented as a Python-based Maya integration using PySide.

The interface supports:

- Validation
- Publishing
- Shot-animation publishing
- Maya playback or custom animation frame ranges
- Asset browsing
- Version viewing
- Preview viewing
- Import into Maya
- Retrieval to cache
- Backend-driven asset queries

The UI supports both PySide2 and PySide6 depending on the available Maya environment.

---

# Testing

The project includes:

- Unit tests
- Integration tests
- Maya integration tests using `mayapy`
- Validation workflow tests
- Asset retrieval tests
- USD workflow verification

Run unit and integration tests:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit tests/integration
```

Run Maya integration tests using `mayapy`:

```bash
PYTHONPATH=src mayapy -m pytest tests/maya
```

Depending on the operating system and Maya installation, the full `mayapy` executable path may need to be specified manually.

The shot-animation workflow has also been manually verified by publishing animated Maya geometry through the UI and re-importing the resulting Alembic cache into a clean Maya scene.


---

# Technologies Used

- Autodesk Maya
- Houdini Solaris
- Python
- PySide2 / PySide6
- USD (`pxr`)
- MongoDB
- GridFS
- PyMongo
- Pytest

---

# Current Scope and Limitations

The implemented scope currently includes:

- Maya static asset validation and publishing
- USD and OBJ asset interchange
- Maya baked Alembic shot-animation publishing
- Backend-driven versioning, package storage, and retrieval
- Maya UI workflows and role-based access
- Asset-level USD interoperability testing in Houdini Solaris

Current limitations are documented deliberately:

- There is not yet a dedicated Houdini-facing publish browser or loader.
- Alembic animation publishes are not yet composed into USD shot stages.
- `scale_to_target=0.01` records the known Maya-to-Houdini conversion but does not yet apply that conversion automatically.
- Shot asset names are required but are not yet managed by a controlled production asset catalogue.
- Publish metadata currently contains local filesystem paths.

Planned development will focus on Houdini retrieval, explicit scale handling, and USD-native asset and shot composition using layers and references.

---

# Project Evolution

The original MSc submission is preserved by the Git tag:

```text
v1.0-asset-publish-tool
```

Development continues in the same repository so its progression from an asset publisher into a broader cross-DCC pipeline remains visible. Feature branches and commits are used for incremental development. Milestone tags are created only for coherent, user-facing versions.

---

# Installation

The tool is installed inside Autodesk Maya using a drag-and-drop installer workflow.

## Installation Steps

1. Open Autodesk Maya
2. Drag `drag_to_maya.py` into the Maya viewport

The installer automatically:

- Creates a Maya `.mod` file
- Adds the project `src` directory to `PYTHONPATH`
- Registers the project icon path
- Creates an `AssetPublish` shelf
- Adds a launcher button for opening the UI

After installation, the tool can be launched directly from the Maya shelf.

Detailed setup instructions are available in:

[`INSTALL.md`](INSTALL.md)

---

# Resources and References

The project was developed using a combination of original implementation work, lecturer guidance, technical documentation, and external development resources.

Resources referenced during development include:

- Autodesk Maya Python documentation
- Pixar USD documentation
- MongoDB and GridFS documentation
- PySide documentation
- Stack Overflow technical discussions
- Lecturer-provided reference snippets and debugging guidance for Maya workflows and preview generation systems
