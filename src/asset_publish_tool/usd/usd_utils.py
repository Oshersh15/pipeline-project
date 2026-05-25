from pathlib import Path
from typing import Optional, Tuple

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

# Preserves original Maya world placement on exported USD assets.
# Useful for environment reconstruction workflows.
APPLY_WORLD_TRANSFORM = True


def open_usd_stage(usd_file: Path) -> Optional[Usd.Stage]:
    """
    Open a USD stage from disk.

    Args:
        usd_file (Path): Path to the USD file.

    Returns:
        Optional[Usd.Stage]: Opened USD stage, or None if the file cannot be opened.
    """
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
    """
    Return the first top-level prim in a USD stage.

    Args:
        stage (Usd.Stage): USD stage to inspect.

    Returns:
        Usd.Prim | None: First root prim, or None if the stage has no root prims.
    """
    root_prims = list(stage.GetPseudoRoot().GetChildren())

    if not root_prims:
        return None

    return root_prims[0]


def set_default_prim_if_missing(stage: Usd.Stage):
    """
    Set the first root prim as the defaultPrim if the stage does not already have one.

    Args:
        stage (Usd.Stage): USD stage to update.

    Returns:
        Usd.Prim | None: Existing or newly assigned default prim, or None if no
        root prim exists.
    """
    current_default = stage.GetDefaultPrim()

    if current_default:
        return current_default

    root_prim = get_first_root_prim(stage)

    if not root_prim:
        print("USD file has no root prims, so defaultPrim could not be set.")
        return None

    stage.SetDefaultPrim(root_prim)

    return root_prim


def validate_exported_usd(stage: Usd.Stage) -> dict:
    """
    Validate the basic structure of an exported USD stage.

    The validation is intentionally lightweight and focuses on requirements
    needed by the publishing workflow, such as root prims and defaultPrim setup.

    Args:
        stage (Usd.Stage): USD stage to validate.

    Returns:
        dict: Dictionary containing lists of warnings and errors.
    """
    results = {
        "warnings": [],
        "errors": [],
    }

    default_prim = stage.GetDefaultPrim()

    if not default_prim:
        results["warnings"].append("USD file has no defaultPrim.")

    root_prim = get_first_root_prim(stage)

    if not root_prim:
        results["errors"].append("USD file contains no root prims.")

    return results


def maya_matrix_to_gf_matrix(world_matrix: list[float]) -> Gf.Matrix4d:
    """
    Convert a Maya world matrix list into a USD Gf.Matrix4d.

    Args:
        world_matrix (list[float]): Flat 16-value matrix returned from Maya.

    Returns:
        Gf.Matrix4d: USD-compatible transformation matrix.
    """
    matrix = Gf.Matrix4d(1.0)

    matrix.SetRow(0, Gf.Vec4d(*world_matrix[0:4]))
    matrix.SetRow(1, Gf.Vec4d(*world_matrix[4:8]))
    matrix.SetRow(2, Gf.Vec4d(*world_matrix[8:12]))
    matrix.SetRow(3, Gf.Vec4d(*world_matrix[12:16]))

    return matrix


def apply_world_transform(stage: Usd.Stage, world_matrix: list[float]):
    """
    Apply the original Maya world transform to the USD defaultPrim.

    Args:
        stage (Usd.Stage): USD stage to modify.
        world_matrix (list[float]): Maya world matrix captured before export.
    """
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
    """
    Add publish metadata to the USD defaultPrim as custom data.

    Args:
        stage (Usd.Stage): USD stage to update.
        asset_name (str): Published asset name.
        asset_type (str): Published asset type/category.
        version (str): Published version string.
        author (str): Username of the publishing user.
        source_scene (str): Source Maya scene path.
    """
    root_prim = stage.GetDefaultPrim()

    if not root_prim:
        print("No defaultPrim found, so metadata was not added.")
        return

    root_prim.SetCustomDataByKey("asset_name", asset_name)
    root_prim.SetCustomDataByKey("asset_type", asset_type)
    root_prim.SetCustomDataByKey("version", version)
    root_prim.SetCustomDataByKey("author", author)
    root_prim.SetCustomDataByKey("source_scene", source_scene)


def add_fallback_preview_material(stage: Usd.Stage, color: tuple[float, float, float]):
    root_prim = stage.GetDefaultPrim()

    if not root_prim:
        print("No defaultPrim found, so fallback material was not added.")
        return

    binding_api = UsdShade.MaterialBindingAPI(root_prim)
    existing_binding = binding_api.GetDirectBinding().GetMaterial()

    if existing_binding:
        return

    material_path = root_prim.GetPath().AppendPath("Looks/fallback_preview_material")
    shader_path = material_path.AppendPath("PreviewSurface")

    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, shader_path)

    shader.CreateIdAttr("UsdPreviewSurface")

    shader.CreateInput(
        "diffuseColor",
        Sdf.ValueTypeNames.Color3f,
    ).Set(Gf.Vec3f(*color))

    shader.CreateInput(
        "roughness",
        Sdf.ValueTypeNames.Float,
    ).Set(0.5)

    shader.CreateOutput(
        "surface",
        Sdf.ValueTypeNames.Token,
    )

    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(),
        "surface",
    )

    UsdShade.MaterialBindingAPI.Apply(root_prim).Bind(material)

    print("Added fallback USD preview material.")


def process_exported_usd(
    usd_file: Path,
    asset_name: str,
    asset_type: str,
    version: str,
    author: str,
    source_scene: str,
    world_matrix: list[float],
    material_color: Optional[Tuple[float, float, float]] = None,
) -> dict:
    """
    Post-process and validate a USD file exported from Maya.

    This function opens the exported USD, assigns a defaultPrim if required,
    optionally applies the original Maya world transform, embeds publish
    metadata, validates the stage, and saves the updated root layer.

    Args:
        usd_file (Path): Path to the exported USD file.
        asset_name (str): Published asset name.
        asset_type (str): Published asset type/category.
        version (str): Published version string.
        author (str): Username of the publishing user.
        source_scene (str): Source Maya scene path.
        world_matrix (list[float]): Maya world matrix captured before export.

    Returns:
        dict: Result dictionary containing success state, warnings, and errors.
    """
    stage = open_usd_stage(usd_file)

    if not stage:
        return {
            "success": False,
            "warnings": [],
            "errors": ["USD stage could not be opened."],
        }

    default_prim = set_default_prim_if_missing(stage)

    if not default_prim:
        return {
            "success": False,
            "warnings": [],
            "errors": ["USD file has no valid defaultPrim."],
        }

    if APPLY_WORLD_TRANSFORM:
        apply_world_transform(
            stage,
            world_matrix,
        )
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

    if material_color:
        add_fallback_preview_material(
            stage,
            material_color,
        )

    validation_results = validate_exported_usd(stage)

    if validation_results["errors"]:
        print("USD validation failed:")

        for error in validation_results["errors"]:
            print(f" - {error}")

        return {
            "success": False,
            "warnings": validation_results["warnings"],
            "errors": validation_results["errors"],
        }

    if validation_results["warnings"]:
        print("USD validation warnings:")

        for warning in validation_results["warnings"]:
            print(f" - {warning}")

    stage.GetRootLayer().Save()

    print(f"Processed USD file: {usd_file}")
    print(f"Default prim: {default_prim.GetName()}")

    return {
        "success": True,
        "warnings": validation_results["warnings"],
        "errors": [],
    }
