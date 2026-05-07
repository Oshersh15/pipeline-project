# Asset Publish Tool - Installation Guide

## 1. Overview

This project is a Maya-based asset publishing tool developed as part of a Pipeline TD workflow.

Current features include:

- Scene validation
- Naming convention validation
- Automatic naming fixes
- Versioned publishing
- OBJ export
- USD export
- Viewport preview generation
- PySide6/PySide2 UI
- MongoDB backend integration

Published asset metadata is currently stored in MongoDB, while exported files are stored locally.

---

# 2. Requirements

Minimum tested environment:

| Software | Version |
|---|---|
| Python | 3.11+ |
| Autodesk Maya | 2023 |
| MongoDB | 7 |
| Podman |  |

Tested on macOS.

---

# 3. Clone Repository

Clone the repository and move into the project directory:

```bash
git clone git@github.com:NCCA/pipelineproject-Oshersh15.git
cd pipelineproject-Oshersh15
```

---

# 4. Python Environment Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

## macOS/Linux

```bash
source .venv/bin/activate
```

Install required packages:

```bash
pip install pymongo
```

---

# 5. MongoDB Backend Setup

Install Podman using Homebrew:

```bash
brew install podman
```

Start the Podman machine:

```bash
podman machine start
```

Run MongoDB container:

```bash
podman run -d \
--name asset-publish-mongo \
-p 27017:27017 \
mongo:7
```

Check that the container is running:

```bash
podman ps
```

---

# 6. Install PyMongo Into Maya

PyMongo must also be installed inside Maya's embedded Python interpreter (`mayapy`).

Install using:

```bash
/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy -m pip install pymongo
```

Restart Maya after installation.

---

# 7. Configure Maya Python Path

Inside Maya Script Editor (Python tab), run:

```python
import sys

project_src = "/Users/osher/repos/Projects/pipelineproject-Oshersh15/src"

if project_src not in sys.path:
    sys.path.append(project_src)
```

Update the path if the repository is located elsewhere on your machine.

---

# 8. Launching the Tool

Inside Maya Script Editor (Python tab), run:

```python
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

This launches the PySide6/PySide2 publishing interface.

---

# 9. Publishing Workflow

The current publishing workflow performs:

1. Scene validation
2. Naming convention validation
3. Automatic versioning
4. OBJ export (models only)
5. USD export
6. Viewport preview generation
7. Metadata generation
8. MongoDB metadata storage

Published asset metadata is loaded directly from MongoDB into the UI.

---

# 10. MongoDB Integration

MongoDB is currently used as the backend source for published asset metadata.

Connection URI:

```text
mongodb://localhost:27017
```

Database:

```text
asset_publish_tool_db
```

Collection:

```text
assets
```

MongoDB Compass can optionally be used to inspect published asset documents visually.

---

# 11. Current Limitations

Current limitations include:

- Exported asset files are still stored locally
- GridFS asset storage is not yet implemented
- No authentication system yet
- No remote deployment yet

These systems are planned as future extensions of the project.
