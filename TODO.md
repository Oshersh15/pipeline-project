# TODO

## Core Validation System
- [x] JSON-based validation configuration
- [x] Regex-based naming validation
- [x] Object type detection (model, camera, light)
- [x] Validation workflow inside Maya

## Scene Processing
- [x] Selection handling from Maya
- [x] Support for hierarchical scenes (groups within groups)
- [x] Automatic naming correction based on object type

## Publishing System
- [x] Versioned folder structure
- [x] Automatic version incrementing
- [x] Metadata generation per asset
- [x] Basic publish workflow

## Export System (USD Pipeline)
- [ ] Implement USD export for a single asset (replace OBJ)
- [ ] Define what data is included in the USD (geometry / transforms / hierarchy)
- [ ] Extend export to support multiple object types (not only models)
- [ ] Test exporting a simple scene (more than one object)

## Validation
- [ ] Add scale check (basic unit validation)
- [ ] Add check for empty transforms

## Metadata
- [ ] Add timestamp to metadata
- [ ] Store validation result in metadata

## Users / Author Tracking
- [ ] Decide whether a user system is needed
- [ ] Replace hardcoded author value
- [ ] Decide how author is defined (system username vs manual input)
- [ ] Store author information consistently in metadata

## UI
- [ ] Improve validation messages (clearer reasons)
- [ ] Allow fixing selected objects only
