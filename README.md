[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/K7bRKtca)

# USD-Based Asset Publishing and Validation Tool for DCC Pipelines

## Initial Design
This project proposes the development of an automated asset publishing and validation tool designed to introduce structured pipeline practices within DCC workflows.

The system will operate within Autodesk Maya and formalise the process of preparing, validating, versioning, and exporting assets into a consistent USD-based structure. The objective is to reduce common production issues such as inconsistent naming, overwritten files, missing dependencies, and unreliable version control.

Rather than building a full asset management system, the project focuses specifically on the publish stage of the pipeline, demonstrating how structured asset management and automation can be implemented in a controlled prototype environment.

## Definition of an Asset

For the purposes of this project, an asset is defined as:

- Geometry or rigged mesh data
- Asset name and category
- Version identifier
- Source DCC application
- Polycount and basic geometry statistics
- Unit and scale metadata
- Export format (USD as primary output)
- Author and publish metadata
- Associated external dependencies (e.g. texture files where applicable)

Material reconstruction will not form part of the core implementation. However, texture dependencies generated from external texturing tools such as Substance Painter will be detected and recorded to ensure portability and validation within the pipeline.

## Asset Management and Version-Controlled Publishing

The system will introduce structured asset management principles by defining where assets are stored, how they are named, and how versions are maintained throughout production.

The publishing process will:

- Enforce consistent naming conventions
- Generate standardised directory structures
- Automatically increment asset versions
- Prevent overwriting of previously published work
- Maintain traceable publish history

This ensures predictable asset locations and reproducible workflows, reflecting common asset management practices used in professional pipelines.

## Validation Framework

Prior to publishing, the tool will perform automated checks to ensure that assets meet defined production criteria. Validation checks will include:

- Naming convention compliance
- Scene unit and scale verification
- Detection of missing references or external file dependencies
- Basic geometry validation (e.g. empty transforms, invalid geometry states)

Validation results will be presented to the user before publishing proceeds. This validation stage functions as an initial internal review mechanism, ensuring assets are production-ready before entering the pipeline.

## USD Asset Packaging and Delivery

Published assets will be exported into a structured USD format using a consistent asset layout strategy. The tool will generate organised USD files suitable for reuse across DCC environments.

The publishing process produces delivery-ready asset packages with consistent naming, structure, and dependency management suitable for downstream consumption. USD is used as a standardised interchange format to promote interoperability and modern pipeline practices.

The implementation will focus on practical asset packaging and referencing workflows rather than advanced custom schema development, ensuring a realistic and achievable scope.

## Cross-DCC Software Connectivity

The system utilises USD as an interchange format to enable reliable asset transfer between DCC applications. By exporting assets into a standardised USD structure, the tool promotes interoperability between software environments while reducing manual conversion steps.

This demonstrates how pipeline tools facilitate communication between departments working across different DCC applications.

## Production Tracking

The system will record publish events and asset status within a structured database, enabling tracking of asset progression throughout production.

Stored metadata will include:
- Asset version history
- Publish timestamps
- Author information
- Validation results
- Publish status

This provides visibility into asset development and allows a clear overview of which assets are current, validated, and production-ready.

## Database and Storage Design

Asset metadata will be stored using a SQLite database. This approach provides:

- Structured querying of asset information
- Local portability
- Minimal deployment complexity
- Compatibility with Python-based DCC integrations

The database schema will include tables for:

- Asset information
- Version history
- File locations
- Publish metadata

This supports asset tracking without requiring server infrastructure.

## DCC Integration

The tool will be implemented as a Python-based plugin integrated into Autodesk Maya using a PySide/Qt graphical interface.

The interface will allow users to:

- Validate assets
- Publish new versions
- Review asset metadata
- Access validation reports

The system architecture will be modular to allow potential future integration with additional DCC applications.

## Known Limitations

Material and shader reconstruction workflows introduce significant complexity and are therefore outside the primary scope of this project.

USD implementation will focus on asset structuring and referencing workflows rather than advanced custom schema development or full production-scale infrastructure.

## Evaluation

The system will be evaluated using representative production assets. Evaluation criteria will include:

- Reduction of manual asset export steps
- Consistency of generated asset structures
- Reliability of version control
- Successful reuse of published USD assets in downstream applications
- Clarity and usefulness of validation and publish reporting

## Expected Outcome

The final deliverable will be a functioning prototype asset publishing system demonstrating:

- Structured asset management
- Pipeline automation
- Cross-DCC software connectivity
- Practical integration of USD within a DCC workflow
- Version tracking and publish history management
- Extension of Maya through Python API development

The project will include technical documentation, database schema design, system architecture description, and demonstration of the working tool.
