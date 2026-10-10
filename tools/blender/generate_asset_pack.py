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
    # Corner straps make the silhouette read as a reinforced, game-ready prop.
    for dx in (-0.44, 0.44):
        parts.append(cube(
            "Crate | corner reinforcement",
            (x + dx, y - 0.526, z + 0.48),
            (0.065, 0.035, 0.82), trim, 0.012
        ))
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


def create_carriage_prop(origin, wood, mahogany, brass, velvet, dark_metal):
    x, y, z = origin
    parts = [
        cube("Carriage | mahogany cabin", (x, y, z + 0.82), (1.75, 1.05, 1.1), wood, 0.1),
        cube("Carriage | crimson velvet panel", (x, y - 0.535, z + 0.78), (0.95, 0.035, 0.55), velvet, 0.025),
        cube("Carriage | brass roof", (x, y, z + 1.42), (1.95, 1.2, 0.12), brass, 0.045),
        cube("Carriage | lower chassis", (x, y, z + 0.18), (2.0, 1.15, 0.22), brass, 0.035),
    ]
    for dx in (-0.62, 0.62):
        for dy in (-0.58, 0.58):
            wheel_center = (x + dx, y + dy, z + 0.22)
            parts.append(cylinder(
                "Carriage | wooden wheel core", wheel_center, 0.28, 0.11,
                wood, vertices=16, rotation=(radians(90), 0, 0)
            ))
            # A raised brass rim and a visible axle cap add depth from side views.
            outer_y = y + dy + (0.067 if dy > 0 else -0.067)
            bpy.ops.mesh.primitive_torus_add(
                major_segments=16, minor_segments=6, location=(x + dx, outer_y, z + 0.22),
                major_radius=0.235, minor_radius=0.035,
                rotation=(radians(90), 0, 0)
            )
            rim = bpy.context.object
            rim.name = "Carriage | brass wheel rim"
            assign(rim, brass)
            parts.append(rim)
            # Eight visible wooden spokes make the wheels read as crafted
            # wagon wheels instead of plain discs when viewed from the side.
            for spoke_index in range(8):
                angle = spoke_index * (2.0 * 3.141592653589793 / 8.0)
                # Keep spokes on the visible outer face of each wheel rather
                # than buried inside the thick wheel core.
                spoke_face_y = y + dy + (0.073 if dy > 0 else -0.073)
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=(
                        x + dx + 0.125 * __import__("math").sin(angle),
                        spoke_face_y,
                        z + 0.22 + 0.125 * __import__("math").cos(angle),
                    ),
                )
                spoke = bpy.context.object
                spoke.name = "Carriage | wooden wheel spoke"
                spoke.dimensions = (0.045, 0.035, 0.27)
                spoke.rotation_euler[1] = angle
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                assign(spoke, mahogany)
                bevel(spoke, 0.008, 1)
                parts.append(spoke)
            parts.append(cylinder(
                "Carriage | axle hub", (x + dx, y + dy, z + 0.22),
                0.085, 0.16, brass, vertices=12, rotation=(radians(90), 0, 0)
            ))
    for dx in (-0.62, 0.62):
        # Recessed dark glass and a four-sided brass frame give each side
        # window depth and a more legible silhouette in game lighting.
        parts.append(cube("Carriage | dark window glass", (x + dx, y - 0.548, z + 0.95), (0.235, 0.025, 0.255), dark_metal, 0.012))
        for frame_z in (-0.145, 0.145):
            parts.append(cube("Carriage | window frame", (x + dx, y - 0.568, z + 0.95 + frame_z), (0.32, 0.035, 0.035), brass, 0.008))
        for frame_x in (-0.145, 0.145):
            parts.append(cube("Carriage | window frame", (x + dx + frame_x, y - 0.568, z + 0.95), (0.035, 0.035, 0.29), brass, 0.008))
    # Decorative lower pinstripe and corner fittings break up the large flat body.
    parts.append(cube("Carriage | lower brass pinstripe", (x, y - 0.545, z + 0.39), (1.45, 0.028, 0.045), brass, 0.01))
    for dx in (-0.78, 0.78):
        parts.append(cube("Carriage | corner fitting", (x + dx, y - 0.55, z + 0.52), (0.07, 0.035, 0.12), brass, 0.012))

    # Make the carriage read as a usable vehicle, not a decorated box:
    # a centered crest, a visible door latch, a boarding step, and twin shafts.
    parts.append(cylinder(
        "Carriage | brass door crest", (x, y - 0.566, z + 1.03),
        0.105, 0.035, brass, vertices=12, rotation=(radians(90), 0, 0)
    ))
    parts.append(sphere(
        "Carriage | crimson crest inset", (x, y - 0.589, z + 1.03),
        (0.052, 0.018, 0.052), velvet
    ))
    parts.append(cube(
        "Carriage | brass door latch", (x + 0.39, y - 0.568, z + 0.70),
        (0.045, 0.035, 0.13), brass, 0.012
    ))
    parts.append(cube(
        "Carriage | boarding step", (x, y - 0.69, z + 0.29),
        (0.62, 0.42, 0.09), mahogany, 0.025
    ))
    parts.append(cube(
        "Carriage | step brass edge", (x, y - 0.705, z + 0.335),
        (0.62, 0.035, 0.025), brass, 0.008
    ))
    for dx in (-0.53, 0.53):
        parts.append(cube(
            "Carriage | forward shaft", (x + dx, y - 1.45, z + 0.25),
            (0.09, 1.75, 0.09), mahogany, 0.018
        ))
        parts.append(cube(
            "Carriage | shaft brass tip", (x + dx, y - 2.31, z + 0.25),
            (0.11, 0.10, 0.11), brass, 0.015
        ))
    return parts



def create_rock_cluster(origin, stone, highlight):
    x, y, z = origin
    parts = []
    for dx, dy, dz, sx, sy, sz in [
        (-0.28, 0.0, 0.26, 0.48, 0.42, 0.46),
        (0.18, -0.04, 0.20, 0.40, 0.36, 0.34),
        (0.02, 0.12, 0.49, 0.34, 0.32, 0.48),
    ]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=(x + dx, y + dy, z + dz))
        obj = bpy.context.object
        obj.name = "Rock cluster | low-poly stone"
        obj.scale = (sx, sy, sz)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(obj, stone if dz < 0.4 else highlight)
        parts.append(obj)
    return parts


def create_pine_tree(origin, bark, foliage):
    x, y, z = origin
    parts = [cylinder("Pine tree | trunk", (x, y, z + 0.62), 0.13, 1.24, bark, vertices=8)]
    for height, radius in ((0.72, 0.62), (1.18, 0.49), (1.58, 0.34)):
        bpy.ops.mesh.primitive_cone_add(
            vertices=8, radius1=radius, radius2=0.035, depth=0.9,
            location=(x, y, z + height)
        )
        crown = bpy.context.object
        crown.name = "Pine tree | evergreen crown"
        assign(crown, foliage)
        parts.append(crown)
    return parts


def create_stone_wall(origin, stone, trim):
    x, y, z = origin
    parts = []
    for row in range(2):
        for column in range(3):
            offset = 0.38 if row % 2 else 0.0
            parts.append(cube(
                "Stone wall | block",
                (x + (column - 1) * 0.76 + offset, y, z + 0.34 + row * 0.68),
                (0.72, 0.42, 0.62), stone, 0.045
            ))
    parts.append(cube("Stone wall | capstone", (x + 0.38, y, z + 1.42), (2.45, 0.5, 0.16), trim, 0.035))
    return parts


def create_bridge_segment(origin, wood, trim):
    x, y, z = origin
    parts = []
    for index in range(5):
        parts.append(cube(
            "Bridge | deck plank",
            (x, y + (index - 2) * 0.34, z + 0.18),
            (2.2, 0.31, 0.16), wood, 0.025
        ))
    for side in (-1, 1):
        parts.append(cube("Bridge | side beam", (x, y + side * 0.83, z + 0.30), (2.35, 0.12, 0.18), trim, 0.025))
        for post_x in (-0.95, 0.0, 0.95):
            parts.append(cube(
                "Bridge | railing post",
                (x + post_x, y + side * 0.83, z + 0.68),
                (0.11, 0.11, 0.72), trim, 0.02
            ))
        parts.append(cube("Bridge | handrail", (x, y + side * 0.83, z + 1.05), (2.35, 0.14, 0.12), wood, 0.025))
    return parts

def setup_camera_and_lights():
    bpy.ops.object.camera_add(location=(9.5, -15.5, 10.5))
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
        if handle.read(8) != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
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
    stone = material("Stone | blue-grey", (0.20, 0.27, 0.32), roughness=0.88)
    stone_highlight = material("Stone | cool highlight", (0.34, 0.41, 0.44), roughness=0.82)
    pine_bark = material("Wood | pine bark", (0.20, 0.085, 0.035), roughness=0.9)
    pine_foliage = material("Foliage | deep evergreen", (0.035, 0.22, 0.13), roughness=0.86)
    glow.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.12, 0.015, 1.0)
    glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

    groups = [
        ("Crate", (-3.0, 0.0, 0.0), lambda p: create_crate(p, wood, brass)),
        ("Lantern", (-1.0, 0.0, 0.0), lambda p: create_lantern(p, brass, dark_metal, glow)),
        ("Crystal", (1.0, 0.0, 0.0), lambda p: create_crystal(p, crystal_mat, dark_metal)),
        ("Barrel", (3.0, 0.0, 0.0), lambda p: create_barrel(p, wood, brass)),
        ("Carriage", (0.0, 2.2, 0.0), lambda p: create_carriage_prop(p, wood, mahogany, brass, velvet, dark_metal)),
        ("Rock_Cluster", (-4.8, 2.4, 0.0), lambda p: create_rock_cluster(p, stone, stone_highlight)),
        ("Pine_Tree", (-2.3, 3.4, 0.0), lambda p: create_pine_tree(p, pine_bark, pine_foliage)),
        ("Stone_Wall", (2.5, 3.0, 0.0), lambda p: create_stone_wall(p, stone, stone_highlight)),
        ("Bridge_Segment", (5.0, 2.8, 0.0), lambda p: create_bridge_segment(p, wood, brass)),
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
    cube("Studio floor", (0.0, 0.8, -0.12), (15.5, 10.0, 0.18), floor_mat, 0.02)
    setup_camera_and_lights()

    scene = bpy.context.scene
    engine_items = scene.render.bl_rna.properties["engine"].enum_items
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_items else "BLENDER_EEVEE"
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output / "preview.png")
    scene.world.color = (0.025, 0.025, 0.025)
    scene.view_settings.view_transform = "AgX"

    blend_path = output / "blendit_asset_pack.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    # Export the complete pack and each named asset collection as standalone GLB files.
    glb_path = output / "blendit_asset_pack.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path), export_format="GLB", use_selection=False,
        export_draco_mesh_compression_enable=False,
    )
    individual_outputs = []
    for asset in manifest_assets:
        collection = bpy.data.collections.get(asset["collection"])
        bpy.ops.object.select_all(action="DESELECT")
        selected_objects = list(collection.objects)
        for obj in selected_objects:
            obj.select_set(True)
        if selected_objects:
            bpy.context.view_layer.objects.active = selected_objects[0]

        # Standalone GLBs must be centered around the asset origin, not retain
        # the staging position used to compose the combined preview scene.
        origin = asset["origin"]
        original_locations = {obj: obj.location.copy() for obj in selected_objects}
        try:
            for obj in selected_objects:
                obj.location.x -= origin[0]
                obj.location.y -= origin[1]
                obj.location.z -= origin[2]
            filename = asset["name"].lower() + ".glb"
            bpy.ops.export_scene.gltf(
                filepath=str(output / filename),
                export_format="GLB",
                use_selection=True,
                export_draco_mesh_compression_enable=False,
            )
        finally:
            for obj, location in original_locations.items():
                obj.location = location

        if not (output / filename).is_file() or (output / filename).stat().st_size == 0:
            raise RuntimeError("Individual asset export failed: " + filename)
        asset["glb_file"] = filename
        asset["export_origin"] = [0.0, 0.0, 0.0]
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
