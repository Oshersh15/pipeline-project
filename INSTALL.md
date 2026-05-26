# Asset Publish Tool - Installation Guide

# Overview

This project is a Maya-based asset publishing and validation tool developed for pipeline-oriented DCC workflows.

The tool supports:

- Asset validation
- Automatic naming correction
- Version-controlled publishing
- USD and OBJ export
- Preview image generation
- MongoDB/GridFS integration
- Asset retrieval to local cache
- Role-based authentication
- Maya integration using PySide2 / PySide6

Published assets are packaged and stored using MongoDB GridFS, while metadata is stored separately for backend-driven asset browsing and querying.

---

# Requirements

Minimum tested environment:

| Software | Version |
|---|---|
| Python | 3.11+ |
| Autodesk Maya | 2023 |
| MongoDB | 7 |

Tested on macOS and Linux.

---

# Clone Repository

Clone the repository and move into the project directory:

```bash
git clone git@github.com:NCCA/pipelineproject-Oshersh15.git
cd pipelineproject-Oshersh15
```

---

# Python Environment Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment.

## macOS / Linux

```bash
source .venv/bin/activate
```

Install required Python packages:

```bash
pip install pymongo pytest
```

Additional packages or plugins may be required depending on the local Maya and USD installation.

---

# MongoDB Backend Setup

## macOS

Install Podman using Homebrew:

```bash
brew install podman
```

Start the Podman machine:

```bash
podman machine start
```

## Linux

On Linux, Podman usually runs natively, so `podman machine start` is typically not required.

Check whether Podman is available:

```bash
podman ps
```

---

Run MongoDB container:

```bash
podman run -d \
--name asset-publish-mongo \
-p 27017:27017 \
docker.io/library/mongo:7
```

Check that the container is running:

```bash
podman ps
```

This tool expects MongoDB to be available at:

```text
localhost:27017
```

If another MongoDB container is already using this port, stop it before launching the tool.

---

# Install Python Packages Into Maya

Required packages must also be installed inside Maya's embedded Python interpreter (`mayapy`).

Example:

```bash
mayapy -m pip install pymongo pytest
```

Depending on the operating system and Maya installation, the full `mayapy` executable path may need to be specified manually.

Restart Maya after installation.

The `mayaUsdPlugin` plugin must be available and loaded in Maya for USD import and export workflows.

---

# Install the Maya Module

Launch Autodesk Maya.

Drag the following file directly into the Maya viewport:

```text
drag_to_maya.py
```

The installer automatically:

- Creates a Maya `.mod` module file
- Adds the project `src` directory to `PYTHONPATH`
- Registers the project icon path through `XBMLANGPATH`
- Creates an `AssetPublish` shelf
- Adds a launcher shelf button

No manual `sys.path` modification is required.

---

# Launching the Tool

After installation, launch the tool from the Maya shelf:

```text
AssetPublish → Asset Publish Tool
```

This opens the publishing interface.

---

# Database Information

Default MongoDB connection:

```text
mongodb://localhost:27017
```

Database name:

```text
asset_publish_tool_db
```

Collection:

```text
assets
```

MongoDB Compass can optionally be used to inspect stored metadata and GridFS package data.

---

# Testing

Run unit and integration tests:

```bash
PYTHONPATH=src pytest tests/unit tests/integration
```

Run Maya integration tests using `mayapy`:

```bash
PYTHONPATH=src mayapy -m pytest tests/maya
```

Depending on the operating system and Maya installation, the full `mayapy` executable path may need to be specified manually.

Example Linux path:

```bash
PYTHONPATH=src /opt/autodesk/maya/bin/mayapy -m pytest tests/maya
```

---

# Notes

The project focuses primarily on asset-level publishing workflows and USD interoperability between DCC applications.

Cross-DCC testing was validated by retrieving published USD assets from GridFS, extracting them to a local cache, and loading them into Houdini Solaris using a Sublayer workflow.
