from pathlib import Path
from typing import Optional

from pxr import Gf, Usd, UsdGeom

# Preserves original Maya world placement on exported USD assets.
# Useful for environment reconstruction workflows.
APPLY_WORLD_TRANSFORM = True


def open_usd_stage(usd_file: Path) -> Optional[Usd.Stage]:
    usd_file = Path(usd_file)

    if not usd_file.exists():
        print(f"USD file does not exist: {usd_file}")
        return None

    try:
        stage = Usd.Stage.Open(str(usd_file))
    except Exception as e:
        print(f"Failed to open USD file: {usd_file}")
        print(e)
        return None

    if not stage:
        print(f"USD stage could not be opened: {usd_file}")
        return None

    return stage


def get_first_root_prim(stage: Usd.Stage):
    root_prims = list(stage.GetPseudoRoot().GetChildren())

    if not root_prims:
        return None

    return root_prims[0]


def set_default_prim_if_missing(stage: Usd.Stage):
    current_default = stage.GetDefaultPrim()

    if current_default:
        return current_default

    root_prim = get_first_root_prim(stage)

    if not root_prim:
        print("USD file has no root prims, so defaultPrim could not be set.")
        return None

    stage.SetDefaultPrim(root_prim)
    return root_prim


def maya_matrix_to_gf_matrix(world_matrix: list[float]) -> Gf.Matrix4d:
    matrix = Gf.Matrix4d(1.0)

    matrix.SetRow(0, Gf.Vec4d(*world_matrix[0:4]))
    matrix.SetRow(1, Gf.Vec4d(*world_matrix[4:8]))
    matrix.SetRow(2, Gf.Vec4d(*world_matrix[8:12]))
    matrix.SetRow(3, Gf.Vec4d(*world_matrix[12:16]))

    return matrix


def apply_world_transform(stage: Usd.Stage, world_matrix: list[float]):
    root_prim = stage.GetDefaultPrim()

    if not root_prim:
        print("No defaultPrim found, so world transform was not applied.")
        return

    xformable = UsdGeom.Xformable(root_prim)

    transform_op = xformable.AddTransformOp(opSuffix="publishedWorldTransform")
    transform_op.Set(maya_matrix_to_gf_matrix(world_matrix))


def add_publish_metadata(
    stage: Usd.Stage,
    asset_name: str,
    asset_type: str,
    version: str,
    author: str,
    source_scene: str,
):
    root_prim = stage.GetDefaultPrim()

    if not root_prim:
        print("No defaultPrim found, so metadata was not added.")
        return

    root_prim.SetCustomDataByKey("asset_name", asset_name)
    root_prim.SetCustomDataByKey("asset_type", asset_type)
    root_prim.SetCustomDataByKey("version", version)
    root_prim.SetCustomDataByKey("author", author)
    root_prim.SetCustomDataByKey("source_scene", source_scene)


def process_exported_usd(
    usd_file: Path,
    asset_name: str,
    asset_type: str,
    version: str,
    author: str,
    source_scene: str,
    world_matrix: list[float],
) -> bool:
    stage = open_usd_stage(usd_file)

    if not stage:
        return False

    default_prim = set_default_prim_if_missing(stage)

    if not default_prim:
        return False

    if APPLY_WORLD_TRANSFORM:
        apply_world_transform(stage, world_matrix)
        print("Applied original Maya world transform to USD root.")
    else:
        print("Skipped USD world transform application for debugging.")

    add_publish_metadata(
        stage=stage,
        asset_name=asset_name,
        asset_type=asset_type,
        version=version,
        author=author,
        source_scene=source_scene,
    )

    stage.GetRootLayer().Save()

    print(f"Processed USD file: {usd_file}")
    print(f"Default prim: {default_prim.GetName()}")

    return True
