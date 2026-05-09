[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/K7bRKtca)

# USD-Based Asset Publishing and Validation Tool for DCC Pipelines

## Initial Design

This project proposes the development of an automated asset publishing and validation tool for DCC workflows, with Autodesk Maya used as the initial test environment.

The overall aim is to build towards a USD-based publishing pipeline, while focusing on practical publish-stage workflows including validation, structured publishing, metadata tracking, and backend-driven asset management.

The current implementation focuses on:

- Storing validation rules in an external configuration file
- Enforcing validation checks inside Maya
- Creating structured versioned publish outputs
- Recording publish metadata
- Backend-driven metadata storage using MongoDB
- Testing the workflow inside Maya

The project currently demonstrates an early-stage pipeline architecture built around modular publishing systems, repository-based backend integration, and structured asset management workflows.

---

# Definition of an Asset

For the purposes of this project, an asset is defined as:

- Geometry or rigged mesh data
- Asset name and category
- Version identifier
- Source DCC application
- Export format
- Author and publish metadata
- Generated preview imagery
- Associated publish metadata and file locations

Material reconstruction workflows are currently outside the primary project scope.

---

# Asset Management and Version-Controlled Publishing

The system introduces structured asset management principles by defining:

- Where assets are stored
- How assets are named
- How versions are generated
- How publish history is recorded

The publishing process currently:

- Enforces naming conventions
- Generates standardised publish directory structures
- Automatically increments versions
- Prevents overwriting previous publishes
- Records publish metadata
- Stores publish metadata inside MongoDB

This creates predictable asset organisation and reproducible publishing workflows similar to those used in production pipelines.

---

# Current Development Focus

The current implementation focuses primarily on the publish stage of the pipeline rather than a complete production asset management system.

The prototype currently investigates:

- Validation workflows inside Maya
- Structured asset publishing
- Automated version management
- Backend-driven metadata tracking
- Modular repository-based architecture
- USD-based publishing workflows

Validation rules are stored externally using JSON configuration files, allowing rules to be extended without modifying the core publishing logic.

Published asset metadata is currently stored both locally and within MongoDB to support backend-driven asset querying and UI integration.

---

# Validation Framework

Prior to publishing, the tool performs automated validation checks to ensure that assets meet defined production requirements.

Current validation includes:

- Naming convention validation
- Detection of invalid or empty transforms
- Basic object-type validation
- Export eligibility checks

Validation results are presented to the user before publishing proceeds.

This validation stage functions as an initial review process to ensure assets are suitable for publishing.

---

# USD Asset Packaging and Delivery

Published assets are exported into a structured USD-based workflow using a standardised publish layout.

The current implementation supports:

- USD export
- OBJ export for geometry assets
- Structured versioned publish directories
- Generated preview images
- Metadata recording

The project focuses on practical publishing workflows and pipeline structure rather than advanced custom USD schema development.

---

# Production Tracking

The current implementation integrates MongoDB for backend-driven metadata storage and publish tracking.

Stored metadata currently includes:

- Asset names
- Asset types
- Publish versions
- Publish paths
- Export file locations
- Author information
- Publish timestamps

Published asset metadata is queried directly from MongoDB through a repository-based backend architecture.

This allows the UI to load published assets from the backend rather than relying solely on local metadata file scanning.

---

# Storage and History Design

The project uses a staged approach to storage and asset history tracking.

The current implementation stores:

- Published asset exports locally
- Publish metadata within MongoDB
- Structured version folders for asset history

The backend architecture currently focuses on metadata storage and querying workflows.

Future development will investigate:

- GridFS-based asset package storage
- Remote backend deployment
- Authentication systems
- Extended production tracking workflows

---

# DCC Integration

The tool is implemented as a Python-based Maya integration using a PySide6 graphical interface.

The interface currently allows users to:

- Validate assets
- Publish versioned assets
- Review published assets
- Access backend-driven asset metadata

The architecture is designed modularly to support future extension into additional DCC environments.

---

# Current Technologies

The current prototype uses:

- Autodesk Maya
- Python
- PySide6
- USD
- MongoDB
- Podman
- PyMongo

---

# Known Limitations

Current limitations include:

- Exported asset files are still stored locally
- GridFS-based asset package storage is not yet implemented
- No authentication or user permission system yet
- No remote deployment yet

These systems are planned as future extensions of the project.

---

# Evaluation

The system is evaluated using representative production assets inside Maya.

Evaluation criteria include:

- Reduction of manual publishing steps
- Consistency of generated asset structures
- Reliability of automated versioning
- Successful metadata tracking
- Backend-driven asset querying
- Clarity of validation and publish reporting

---

# Expected Outcome

The final deliverable is a functioning prototype asset publishing system demonstrating:

- Structured asset management
- Automated publishing workflows
- Backend-driven metadata storage
- Version-controlled publishing
- USD-based publishing workflows
- Pipeline-oriented software architecture
- Extension of Maya through Python API development

The project includes:

- Technical documentation
- Installation documentation
- Repository-based backend architecture
- MongoDB integration
- Working publishing and validation workflows

---

# Usage (Prototype)

The tool is currently executed inside Autodesk Maya via the Script Editor.

To run the tool, ensure the project `src` directory is available in Python’s path, then launch the UI:

```python
import sys

# Add project src directory
sys.path.append("/path/to/pipelineproject-Oshersh15/src")

import importlib

import asset_publish_tool.database.connection as connection
import asset_publish_tool.database.asset_repository as asset_repository
import asset_publish_tool.maya.publisher as publisher
import asset_publish_tool.ui.maya_pyside_ui as ui

importlib.reload(connection)
importlib.reload(asset_repository)
importlib.reload(publisher)
importlib.reload(ui)

ui.show_ui()
```

---

# Installation

Detailed installation and setup instructions can be found in:

```text
INSTALL.md
```
