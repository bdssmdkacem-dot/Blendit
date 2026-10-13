"""Generate a Moroccan Parliament-inspired exterior and domed plenary interior asset pack.

Run:
  blender --background --factory-startup --python tools/blender/generate_parliament_pack.py -- --output-dir build/parliament

This is a reference-led architectural interpretation, not a survey-accurate reconstruction.
Use official/current photographs and on-site measurements for exact reconstruction.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="build/parliament")
    parser.add_argument("--samples", type=int, default=32)
    return parser.parse_args(argv)


def mat(name, color, metallic=0.0, roughness=0.55):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return m


def assign(obj, material):
    if material and obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    return obj


def cube(name, loc, dims, material, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    if bevel:
        b = o.modifiers.new("Architectural softened edges", "BEVEL")
        b.width = bevel
        b.segments = 3
        o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return o


def cylinder(name, loc, radius, depth, material, vertices=32, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=loc, rotation=rotation or (0, 0, 0))
    o = bpy.context.object
    o.name = name
    assign(o, material)
    bevel = o.modifiers.new("Edge highlights", "BEVEL")
    bevel.width = min(0.035, radius * 0.08)
    bevel.segments = 2
    o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return o


def sphere(name, loc, scale, material, segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def mesh_object(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def arch_curve(name, center, width, height, depth, material, bevel=0.045, segments=24):
    # A continuous rounded arch profile in the X/Z plane, placed on the front facade.
    x, y, z = center
    r = width / 2
    straight_h = max(0.05, height - r)
    points = [(-r, 0, 0), (-r, 0, straight_h)]
    for i in range(segments + 1):
        a = math.pi - math.pi * i / segments
        points.append((r * math.cos(a), 0, straight_h + r * math.sin(a)))
    points.append((r, 0, 0))
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (co[0], co[1], co[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, z)
    assign(obj, material)
    return obj


def hemisphere(name, center, radius, material, rings=14, segments=48):
    # Closed hemispherical dome with a shallow circular base.
    cx, cy, cz = center
    verts = [(cx, cy, cz + radius)]
    for ri in range(1, rings + 1):
        theta = (math.pi / 2) * ri / rings
        for si in range(segments):
            phi = 2 * math.pi * si / segments
            verts.append((cx + radius * math.sin(theta) * math.cos(phi),
                          cy + radius * math.sin(theta) * math.sin(phi),
                          cz + radius * math.cos(theta)))
    faces = []
    for si in range(segments):
        faces.append((0, 1 + si, 1 + (si + 1) % segments))
    for ri in range(rings - 1):
        start1 = 1 + ri * segments
        start2 = start1 + segments
        for si in range(segments):
            sn = (si + 1) % segments
            faces.append((start1 + si, start2 + si, start2 + sn, start1 + sn))
    base = 1 + (rings - 1) * segments
    faces.append(tuple(base + i for i in range(segments)))
    return mesh_object(name, verts, faces, material)


def dome_rib(name, center, radius, material, count=24):
    cx, cy, cz = center
    for i in range(count):
        phi = 2 * math.pi * i / count
        pts = []
        for j in range(33):
            theta = (math.pi / 2) * j / 32
            pts.append((cx + (radius + 0.012) * math.sin(theta) * math.cos(phi),
                        cy + (radius + 0.012) * math.sin(theta) * math.sin(phi),
                        cz + (radius + 0.012) * math.cos(theta)))
        c = bpy.data.curves.new(name + " %02d" % i, "CURVE")
        c.dimensions = "3D"
        c.bevel_depth = 0.022
        c.bevel_resolution = 2
        sp = c.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts):
            p.co = (*co, 1)
        o = bpy.data.objects.new(name + " %02d" % i, c)
        bpy.context.collection.objects.link(o)
        assign(o, material)


def area_light(name, loc, energy, size, target):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.energy = energy
    o.data.shape = "DISK"
    o.data.size = size
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
    return o


def camera(name, loc, target, lens=45):
    bpy.ops.object.camera_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.data.lens = lens
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
    return o


def build_exterior(m):
    start = set(bpy.context.scene.objects)
    # Broad institutional massing and plinth.
    cube("Exterior | limestone plinth", (0, 0, 0.35), (25, 13, 0.7), m["stone"], 0.14)
    cube("Exterior | main central block", (0, 0, 3.15), (15.5, 8.2, 5.5), m["ivory"], 0.12)
    cube("Exterior | left wing", (-9.1, 0.2, 2.55), (5.2, 7.4, 4.3), m["stone"], 0.12)
    cube("Exterior | right wing", (9.1, 0.2, 2.55), (5.2, 7.4, 4.3), m["stone"], 0.12)
    cube("Exterior | cornice central", (0, -4.18, 5.95), (16.0, 0.28, 0.35), m["sandstone"], 0.04)
    cube("Exterior | upper cornice", (0, 0, 6.05), (16.0, 8.5, 0.24), m["sandstone"], 0.04)
    # Repeated tall window bays with deep reveals and arch surrounds.
    for x in [-6.1, -4.1, -2.05, 0, 2.05, 4.1, 6.1]:
        cube("Exterior | recessed window", (x, -4.13, 3.45), (1.05, 0.12, 2.25), m["glass"], 0.025)
        arch_curve("Exterior | carved window arch", (x, -4.25, 2.35), 1.3, 2.65, 0.1, m["zellige"], 0.055)
        cube("Exterior | window mullion", (x, -4.25, 3.45), (0.045, 0.08, 2.1), m["brass"], 0.008)
    for wing_x in [-9.1, 9.1]:
        for z in [2.0, 3.55]:
            for dx in [-1.45, 0, 1.45]:
                cube("Exterior | wing window", (wing_x + dx, -3.56, z), (0.68, 0.1, 0.85), m["glass"], 0.025)
                arch_curve("Exterior | wing arch surround", (wing_x + dx, -3.64, z - 0.4), 0.82, 1.0, 0.1, m["zellige"], 0.035, 18)
    # Central entrance, steps, paired columns, and Moroccan horseshoe-like arch motif.
    cube("Exterior | entrance shadow", (0, -4.23, 1.95), (3.1, 0.14, 3.2), m["dark"], 0.02)
    cube("Exterior | entrance door", (0, -4.34, 1.7), (2.1, 0.1, 2.65), m["wood"], 0.025)
    arch_curve("Exterior | monumental entrance arch", (0, -4.43, 0.55), 3.7, 3.5, 0.1, m["zellige"], 0.12, 36)
    for x in [-2.25, 2.25]:
        cylinder("Exterior | entry column", (x, -4.35, 2.4), 0.22, 3.8, m["ivory"], 24)
        cylinder("Exterior | column capital", (x, -4.35, 4.35), 0.34, 0.25, m["zellige"], 24)
    for i in range(5):
        cube("Exterior | entrance stair %02d" % i, (0, -5.0 - i * 0.38, 0.42 - i * 0.055),
             (5.2 - i * 0.28, 0.55, 0.16), m["stone"], 0.035)
    # Flat roofline with subtle geometric parapet detail; no invented oversized dome on facade.
    for x in [i * 0.55 for i in range(-13, 14)]:
        cube("Exterior | parapet tooth", (x, -4.18, 6.35), (0.22, 0.22, 0.24), m["sandstone"], 0.025)
    # Courtyard ground and low planters.
    cube("Exterior | forecourt", (0, -9.5, -0.05), (38, 14, 0.2), m["paving"], 0.02)
    for x in [-13, 13]:
        cube("Exterior | planter", (x, -8.7, 0.32), (2.1, 4.5, 0.65), m["stone"], 0.08)
        for dx in [-0.55, 0, 0.55]:
            cylinder("Exterior | cypress trunk", (x + dx, -8.7, 1.3), 0.07, 1.8, m["wood"], 10)
            sphere("Exterior | cypress foliage", (x + dx, -8.7, 2.25), (0.48, 0.48, 1.25), m["green"])
    # Moroccan flags represented as neutral flagpoles and red cloth planes with green star omitted
    # unless an approved, accurate emblem asset is supplied.
    for x in [-4.8, 4.8]:
        cylinder("Exterior | flagpole", (x, -6.0, 4.3), 0.045, 7.8, m["brass"], 16)
        cube("Exterior | flag cloth", (x + 0.72, -6.0, 6.2), (1.4, 0.055, 0.85), m["flag_red"], 0.015)
    return [o for o in bpy.context.scene.objects if o not in start]


def build_interior(m):
    start = set(bpy.context.scene.objects)
    # Interior uses a separate local origin so it can be used as a standalone module.
    cylinder("Interior | circular foundation", (0, 0, 0.15), 10.7, 0.3, m["stone"], 96)
    cylinder("Interior | marble floor", (0, 0, 0.34), 10.2, 0.12, m["marble"], 96)
    cylinder("Interior | outer wall", (0, 0, 4.0), 10.0, 7.2, m["ivory"], 96)
    # Inner decorative rings and panels.
    for z, radius, depth, material in [(1.0, 10.03, 0.14, m["zellige"]), (6.9, 10.03, 0.18, m["sandstone"]), (7.25, 9.7, 0.12, m["brass"])]:
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth, major_segments=96, minor_segments=8, location=(0, 0, z))
        assign(bpy.context.object, material)
        bpy.context.object.name = "Interior | continuous decorative ring"
    # High windows and inset panels around the perimeter.
    for i in range(24):
        a = 2 * math.pi * i / 24
        x, y = 9.65 * math.cos(a), 9.65 * math.sin(a)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 5.0))
        o = bpy.context.object
        o.name = "Interior | clerestory window %02d" % i
        o.dimensions = (0.75, 0.16, 1.65)
        o.rotation_euler[2] = a + math.pi / 2
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(o, m["glass"])
        # Decorative wall pilaster
        cylinder("Interior | pilaster %02d" % i, (9.72 * math.cos(a), 9.72 * math.sin(a), 3.8),
                 0.13, 5.8, m["sandstone"], 16)
    # Dome and its radial ribs.
    hemisphere("Interior | great domed ceiling", (0, 0, 7.35), 9.65, m["dome"], 18, 72)
    dome_rib("Interior | dome radial rib", (0, 0, 7.35), 9.65, m["brass"], 24)
    cylinder("Interior | oculus ring", (0, 0, 16.92), 0.78, 0.16, m["brass"], 64)
    sphere("Interior | oculus glass", (0, 0, 16.97), (0.62, 0.62, 0.12), m["glass"], 32, 12)
    # Circular, stepped seating rows facing the dais at negative Y.
    for row in range(5):
        radius = 4.0 + row * 1.0
        seat_z = 0.68 + row * 0.38
        count = 20 + row * 8
        for i in range(count):
            a = math.radians(205) + math.radians(130) * i / max(1, count - 1)
            x, y = radius * math.cos(a), radius * math.sin(a)
            seat = cube("Interior | representative seat r%02d n%02d" % (row, i),
                        (x, y, seat_z), (0.48, 0.55, 0.42), m["seat"], 0.08)
            seat.rotation_euler[2] = a + math.pi / 2
            back = cube("Interior | seat back r%02d n%02d" % (row, i),
                        (x + 0.12 * math.cos(a), y + 0.12 * math.sin(a), seat_z + 0.38),
                        (0.48, 0.12, 0.5), m["seat_back"], 0.06)
            back.rotation_euler[2] = a + math.pi / 2
            desk = cube("Interior | desk r%02d n%02d" % (row, i),
                        (x - 0.25 * math.cos(a), y - 0.25 * math.sin(a), seat_z + 0.18),
                        (0.62, 0.3, 0.09), m["wood"], 0.025)
            desk.rotation_euler[2] = a + math.pi / 2
            cylinder("Interior | microphone r%02d n%02d" % (row, i),
                     (x - 0.25 * math.cos(a), y - 0.25 * math.sin(a), seat_z + 0.31),
                     0.025, 0.24, m["brass"], 8)
    # Presiding dais, central lectern, and front stage.
    cube("Interior | speaker dais", (0, -7.1, 0.78), (7.0, 2.2, 0.8), m["wood"], 0.12)
    cube("Interior | speaker desk", (0, -7.35, 1.45), (4.5, 0.95, 0.7), m["wood"], 0.1)
    cube("Interior | desk front inlay", (0, -7.85, 1.45), (3.8, 0.035, 0.32), m["zellige"], 0.02)
    cube("Interior | lectern pedestal", (0, -5.65, 1.0), (0.75, 0.65, 1.25), m["wood"], 0.07)
    cube("Interior | lectern top", (0, -5.65, 1.67), (1.2, 0.8, 0.12), m["wood"], 0.05)
    # Hanging circular lighting ring.
    bpy.ops.mesh.primitive_torus_add(major_radius=2.1, minor_radius=0.075, major_segments=64, minor_segments=12, location=(0, 0, 11.0))
    assign(bpy.context.object, m["brass"])
    bpy.context.object.name = "Interior | suspended chandelier ring"
    for i in range(16):
        a = 2 * math.pi * i / 16
        sphere("Interior | chandelier lamp %02d" % i, (2.1 * math.cos(a), 2.1 * math.sin(a), 10.85),
               (0.16, 0.16, 0.24), m["lamp"], 16, 8)
    return [o for o in bpy.context.scene.objects if o not in start]


def setup_render(out, samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.16, 0.16, 0.16)
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    area_light("Studio | key", (4, -10, 16), 2400, 9, (0, 0, 4))
    area_light("Studio | fill", (-12, -2, 10), 1500, 8, (0, 0, 5))
    area_light("Studio | rim", (3, 8, 15), 2600, 7, (0, 0, 7))
    scene.render.filepath = str(out / "preview_exterior.png")
    scene.camera = camera("Camera | exterior hero", (24, -32, 18), (0, -2, 3.0), 48)


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        if o and o.name in bpy.context.scene.objects:
            o.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def export_glb(path, objects):
    select_only(objects)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)


def main():
    opt = args()
    out = Path(opt.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)

    m = {
        "stone": mat("Architecture | warm cut limestone", (0.53, 0.43, 0.32), roughness=0.78),
        "ivory": mat("Architecture | ivory plaster", (0.78, 0.69, 0.54), roughness=0.82),
        "sandstone": mat("Architecture | carved sandstone", (0.42, 0.27, 0.15), roughness=0.75),
        "zellige": mat("Moroccan craft | deep green zellige", (0.035, 0.22, 0.15), roughness=0.34),
        "glass": mat("Glazing | blue smoke glass", (0.07, 0.17, 0.22), metallic=0.25, roughness=0.2),
        "dark": mat("Shadow | entrance recess", (0.035, 0.028, 0.023), roughness=0.9),
        "wood": mat("Interior | dark walnut", (0.19, 0.075, 0.035), roughness=0.36),
        "brass": mat("Metal | brushed brass", (0.48, 0.28, 0.08), metallic=0.72, roughness=0.28),
        "marble": mat("Floor | cream marble", (0.78, 0.72, 0.6), roughness=0.24),
        "paving": mat("Forecourt | pale stone paving", (0.62, 0.57, 0.48), roughness=0.86),
        "green": mat("Landscape | deep cypress green", (0.035, 0.18, 0.09), roughness=0.9),
        "flag_red": mat("Flag | red cloth", (0.55, 0.025, 0.035), roughness=0.88),
        "dome": mat("Interior | painted dome plaster", (0.83, 0.77, 0.65), roughness=0.78),
        "seat": mat("Seating | dark leather", (0.12, 0.045, 0.035), roughness=0.44),
        "seat_back": mat("Seating | upholstered back", (0.22, 0.055, 0.04), roughness=0.52),
        "lamp": mat("Lighting | warm opal glass", (0.95, 0.67, 0.28), roughness=0.22),
    }

    exterior = build_exterior(m)
    interior = build_interior(m)
    setup_render(out, opt.samples)
    scene = bpy.context.scene
    # Render exterior beauty preview.
    scene.camera = bpy.data.objects.get("Camera | exterior hero")
    scene.render.filepath = str(out / "preview_exterior.png")
    bpy.ops.render.render(write_still=True)
    # Render the interior from a low central position toward the dais and dome.
    scene.camera = camera("Camera | interior hero", (0, 5.0, 3.2), (0, -4.2, 9.0), 25)
    scene.render.filepath = str(out / "preview_interior.png")
    bpy.ops.render.render(write_still=True)

    # Export each architectural set independently, excluding studio cameras/lights.
    export_glb(out / "parliament_exterior.glb", exterior)
    export_glb(out / "parliament_domed_chamber.glb", interior)
    # Save editable combined source, with both asset groups and preview cameras/lights.
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "moroccan_parliament_master.blend"))

    outputs = [
        "moroccan_parliament_master.blend",
        "parliament_exterior.glb",
        "parliament_domed_chamber.glb",
        "preview_exterior.png",
        "preview_interior.png",
    ]
    manifest = {
        "pack": "Moroccan Parliament Architecture",
        "version": 1,
        "reference_note": "Reference-led procedural interpretation; not a survey-accurate reconstruction.",
        "units": "meters (approximate)",
        "outputs": outputs,
        "assets": [
            {"id": "parliament_exterior", "file": "parliament_exterior.glb", "preview": "preview_exterior.png", "status": "generated_pending_visual_review"},
            {"id": "parliament_domed_chamber", "file": "parliament_domed_chamber.glb", "preview": "preview_interior.png", "status": "generated_pending_visual_review"},
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PARLIAMENT_PACK_OUTPUT=" + str(out))
    print("PARLIAMENT_PACK_ASSETS=" + ", ".join(outputs))


if __name__ == "__main__":
    main()
