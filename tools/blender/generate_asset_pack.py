"""Generate a starter stylized fantasy asset pack using Blender's bpy API.

Run:
  blender --background --factory-startup --python tools/blender/generate_asset_pack.py -- --output-dir build/assets
"""
import argparse
import json
import sys
import struct
from math import radians
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="build/assets")
    return parser.parse_args(argv)


def material(name, color, metallic=0.0, roughness=0.55):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    return obj


def bevel(obj, amount=0.06, segments=2):
    if obj.type == "MESH":
        mod = obj.modifiers.new("Soft crafted edges", "BEVEL")
        mod.width = amount
        mod.segments = segments
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cube(name, location, scale, mat, bevel_amount=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    return bevel(obj, bevel_amount)


def cylinder(name, location, radius, depth, mat, vertices=16, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location,
        rotation=rotation or (0, 0, 0)
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    return bevel(obj, 0.025, 2)


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    bpy.ops.object.shade_smooth()
    return obj


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def create_crate(origin, wood, trim):
    x, y, z = origin
    parts = [cube("Crate | body", (x, y, z + 0.48), (1.0, 1.0, 0.9), wood)]
    for dz in (0.12, 0.82):
        parts.append(cube("Crate | brass band", (x, y - 0.506, z + dz), (0.94, 0.035, 0.07), trim, 0.015))
    parts.append(cube("Crate | front slat", (x, y - 0.515, z + 0.47), (0.84, 0.035, 0.11), trim, 0.015))
    return parts


def create_lantern(origin, brass, dark, glow):
    x, y, z = origin
    parts = [
        cube("Lantern | base", (x, y, z + 0.08), (0.48, 0.42, 0.14), dark),
        cube("Lantern | roof", (x, y, z + 0.82), (0.5, 0.44, 0.12), brass),
        sphere("Lantern | warm glass", (x, y, z + 0.47), (0.16, 0.14, 0.25), glow),
    ]
    for dx in (-0.2, 0.2):
        for dy in (-0.17, 0.17):
            parts.append(cube("Lantern | frame", (x + dx, y + dy, z + 0.46), (0.045, 0.045, 0.65), brass, 0.01))
    parts.append(cylinder("Lantern | handle", (x, y, z + 0.98), 0.13, 0.035, brass, rotation=(radians(90), 0, 0)))
    return parts


def create_crystal(origin, crystal_mat, dark):
    x, y, z = origin
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.34, radius2=0.02, depth=1.1, location=(x, y, z + 0.65))
    obj = bpy.context.object
    obj.name = "Crystal | faceted shard"
    assign(obj, crystal_mat)
    bevel(obj, 0.015, 1)
    cylinder("Crystal | stone base", (x, y, z + 0.08), 0.4, 0.16, dark, vertices=8)
    return [obj]


def create_barrel(origin, wood, trim):
    x, y, z = origin
    parts = [cylinder("Barrel | body", (x, y, z + 0.48), 0.42, 0.9, wood, vertices=12)]
    for dz, radius in ((0.18, 0.39), (0.48, 0.43), (0.78, 0.39)):
        parts.append(cylinder("Barrel | metal hoop", (x, y, z + dz), radius, 0.07, trim, vertices=12))
    parts.append(cylinder("Barrel | lid", (x, y, z + 0.94), 0.38, 0.06, wood, vertices=12))
    return parts


def create_carriage_prop(origin, wood, brass, velvet):
    x, y, z = origin
    parts = [
        cube("Carriage | mahogany cabin", (x, y, z + 0.82), (1.75, 1.05, 1.1), wood, 0.1),
        cube("Carriage | crimson velvet panel", (x, y - 0.535, z + 0.78), (0.95, 0.035, 0.55), velvet, 0.025),
        cube("Carriage | brass roof", (x, y, z + 1.42), (1.95, 1.2, 0.12), brass, 0.045),
        cube("Carriage | lower chassis", (x, y, z + 0.18), (2.0, 1.15, 0.22), brass, 0.035),
    ]
    for dx in (-0.62, 0.62):
        for dy in (-0.58, 0.58):
            parts.append(cylinder("Carriage | wheel", (x + dx, y + dy, z + 0.22), 0.28, 0.11, brass, vertices=16, rotation=(radians(90), 0, 0)))
    for dx in (-0.62, 0.62):
        parts.append(cube("Carriage | window", (x + dx, y - 0.54, z + 0.95), (0.3, 0.045, 0.32), brass, 0.025))
    return parts


def setup_camera_and_lights():
    bpy.ops.object.camera_add(location=(6.8, -10.5, 7.2))
    camera = bpy.context.object
    camera.name = "Preview Camera"
    direction = -camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 52
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(1.5, -5.0, 8.0))
    key = bpy.context.object
    key.name = "Large soft key"
    key.data.energy = 1150
    key.data.shape = "DISK"
    key.data.size = 7.0
    key.rotation_euler = (radians(25), 0, radians(12))

    bpy.ops.object.light_add(type="AREA", location=(-5.0, 2.0, 5.0))
    fill = bpy.context.object
    fill.name = "Warm rim light"
    fill.data.energy = 850
    fill.data.color = (1.0, 0.48, 0.2)
    fill.data.size = 5.0
    fill.rotation_euler = (radians(25), 0, radians(-35))


def validate_outputs(output, manifest):
    required = [
        "blendit_asset_pack.blend",
        "blendit_asset_pack.glb",
        "preview.png",
        "manifest.json",
        *[asset["glb_file"] for asset in manifest["assets"]],
    ]
    for filename in required:
        path = output / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Required output is missing or empty: " + filename)

    glb_path = output / "blendit_asset_pack.glb"
    with glb_path.open("rb") as handle:
        header = handle.read(12)
    if len(header) != 12:
        raise RuntimeError("Combined GLB header is truncated")
    magic, version, declared_length = struct.unpack("<4sII", header)
    if magic != b"glTF" or version != 2 or declared_length != glb_path.stat().st_size:
        raise RuntimeError("Combined GLB header or declared length is invalid")

    preview_path = output / "preview.png"
    with preview_path.open("rb") as handle:
        if handle.read(8) != b"\\x89PNG\\r\\n\\x1a\\n":
            raise RuntimeError("Preview is not a valid PNG file signature")

    for asset in manifest["assets"]:
        asset_path = output / asset["glb_file"]
        with asset_path.open("rb") as handle:
            asset_header = handle.read(12)
        if len(asset_header) != 12:
            raise RuntimeError("Truncated GLB for asset: " + asset["name"])
        asset_magic, asset_version, asset_length = struct.unpack("<4sII", asset_header)
        if (asset_magic != b"glTF" or asset_version != 2
                or asset_length != asset_path.stat().st_size):
            raise RuntimeError("Invalid GLB export for asset: " + asset["name"])

    manifest_path = output / "manifest.json"
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(loaded.get("assets", [])) != len(manifest["assets"]):
        raise RuntimeError("Manifest asset count does not match generated assets")
    for filename in loaded.get("outputs", []):
        path = output / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Manifest output is missing or empty: " + filename)


def main():
    args = parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    clear_scene()

    mahogany = material("Wood | dark mahogany", (0.19, 0.055, 0.028), roughness=0.32)
    wood = material("Wood | warm oak", (0.38, 0.17, 0.065), roughness=0.58)
    brass = material("Metal | aged brass", (0.58, 0.32, 0.09), metallic=0.72, roughness=0.28)
    dark_metal = material("Metal | blackened iron", (0.055, 0.065, 0.07), metallic=0.55, roughness=0.4)
    velvet = material("Fabric | crimson velvet", (0.32, 0.012, 0.035), roughness=0.82)
    crystal_mat = material("Magic | turquoise crystal", (0.025, 0.48, 0.62), metallic=0.18, roughness=0.22)
    glow = material("Light | amber glass", (1.0, 0.34, 0.055), roughness=0.2)
    glow.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.12, 0.015, 1.0)
    glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

    groups = [
        ("Crate", (-3.0, 0.0, 0.0), lambda p: create_crate(p, wood, brass)),
        ("Lantern", (-1.0, 0.0, 0.0), lambda p: create_lantern(p, brass, dark_metal, glow)),
        ("Crystal", (1.0, 0.0, 0.0), lambda p: create_crystal(p, crystal_mat, dark_metal)),
        ("Barrel", (3.0, 0.0, 0.0), lambda p: create_barrel(p, wood, brass)),
        ("Carriage", (0.0, 2.2, 0.0), lambda p: create_carriage_prop(p, mahogany, brass, velvet)),
    ]
    manifest_assets = []
    for name, origin, builder in groups:
        before = set(bpy.context.scene.objects)
        builder(origin)
        created = [obj for obj in bpy.context.scene.objects if obj not in before]
        collection = bpy.data.collections.new("ASSET | " + name)
        bpy.context.scene.collection.children.link(collection)
        for obj in created:
            for old_collection in list(obj.users_collection):
                old_collection.objects.unlink(obj)
            collection.objects.link(obj)
        manifest_assets.append({
            "name": name,
            "object_count": len(created),
            "collection": collection.name,
            "origin": list(origin),
            "format": ["blend", "glb"],
        })

    # A simple neutral floor makes the preview useful but is excluded from the asset collections.
    floor_mat = material("Studio | midnight blue", (0.025, 0.04, 0.065), roughness=0.8)
    cube("Studio floor", (0.0, 0.8, -0.12), (10.5, 7.0, 0.18), floor_mat, 0.02)
    setup_camera_and_lights()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(scene, "eevee") is False else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output / "preview.png")
    scene.world.color = (0.025, 0.025, 0.025)
    scene.view_settings.view_transform = "AgX"

    blend_path = output / "blendit_asset_pack.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    # Export the complete pack and each named asset collection as standalone GLB files.
    glb_path = output / "blendit_asset_pack.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=False)
    individual_outputs = []
    for asset in manifest_assets:
        collection = bpy.data.collections.get(asset["collection"])
        bpy.ops.object.select_all(action="DESELECT")
        for obj in collection.objects:
            obj.select_set(True)
        if collection.objects:
            bpy.context.view_layer.objects.active = collection.objects[0]
        filename = asset["name"].lower() + ".glb"
        bpy.ops.export_scene.gltf(
            filepath=str(output / filename),
            export_format="GLB",
            use_selection=True,
        )
        if not (output / filename).is_file() or (output / filename).stat().st_size == 0:
            raise RuntimeError("Individual asset export failed: " + filename)
        asset["glb_file"] = filename
        individual_outputs.append(filename)
    bpy.ops.object.select_all(action="DESELECT")

    bpy.ops.render.render(write_still=True)
    if not (output / "preview.png").is_file() or (output / "preview.png").stat().st_size == 0:
        raise RuntimeError("Preview render did not produce a valid PNG file")

    manifest = {
        "generator": "Blendit Blender Asset Workshop",
        "schema_version": 1,
        "blender_version": bpy.app.version_string,
        "assets": manifest_assets,
        "outputs": ["blendit_asset_pack.blend", "blendit_asset_pack.glb", *individual_outputs, "preview.png"],
        "notes": "Procedural starter pack; inspect assets and performance before production use.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    validate_outputs(output, manifest)
    print("BLENDIT_GENERATION_OK")
    print("Output directory:", output)
    print("Assets generated:", len(manifest_assets))


if __name__ == "__main__":
    main()
