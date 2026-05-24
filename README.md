[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/K7bRKtca)

# USD-Based Asset Publishing and Validation Tool for DCC Pipelines

## Overview

This project implements a USD-based asset publishing and validation tool for Digital Content Creation (DCC) workflows, using Autodesk Maya as the primary integration environment.

The system focuses on production-oriented publish workflows including:

- Automated validation
- Version-controlled publishing
- USD and OBJ export
- MongoDB/GridFS asset storage
- Asset retrieval and local cache workflows
- Role-based permissions
- Cross-DCC USD testing in Houdini Solaris

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

# Publishing Workflow

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

# USD Workflow

USD is used as the primary interchange format for asset publishing and cross-DCC testing.

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

Cross-DCC testing was performed by retrieving published USD assets from GridFS and loading them into Houdini Solaris.

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

---

# Roles and Permissions

The system includes role-based authentication with three user roles:

# Roles and Permissions

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
PYTHONPATH=src pytest
```

Run Maya integration tests using `mayapy`:

```bash
PYTHONPATH=src mayapy -m pytest tests/maya
```

Depending on the operating system and Maya installation, the full `mayapy` executable path may need to be specified manually.


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

# Project Scope

The project focuses on asset-level publishing workflows, validation, backend-driven asset management, and USD interoperability between DCC applications.

Full shot assembly workflows and remote production deployment are outside the scope of this implementation.

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

```text
INSTALL.md
```

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
