"""Generate a small, fictional 3D character cast for satirical parliament videos.

These are deliberately anonymous archetypes, not likenesses of real politicians.
Run:
  blender --background --factory-startup --python tools/blender/generate_parliament_satire_characters.py -- --output-dir build/parliament-characters
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    # Blender versions/build wrappers differ in whether the "--" separator is
    # preserved in sys.argv. Prefer the script arguments after it when present;
    # otherwise parse known options and ignore Blender's own CLI flags.
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", default="build/parliament-characters")
    p.add_argument("--samples", type=int, default=16)
    args, _unknown = p.parse_known_args(argv)
    return args


def material(name, color, roughness=0.55, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return m


def finish(obj, name, mat, smooth=False, bevel=0.0):
    obj.name = name
    if mat and obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    if smooth and obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    if bevel and obj.type == "MESH":
        mod = obj.modifiers.new("Soft cartoon edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def ellipsoid(name, loc, scale, mat, seg=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, mat, True)


def box(name, loc, scale, mat, bevel=0.08, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = scale
    if rotation:
        o.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, mat, False, bevel)


def rod(name, a, b, radius, mat, vertices=16):
    a, b = Vector(a), Vector(b)
    d = b - a
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=mid)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return finish(o, name, mat, True)


def curve_line(name, points, mat, thickness=0.025):
    c = bpy.data.curves.new(name, "CURVE")
    c.dimensions = "3D"
    c.resolution_u = 2
    c.bevel_depth = thickness
    c.bevel_resolution = 3
    sp = c.splines.new("POLY")
    sp.points.add(len(points)-1)
    for p, v in zip(sp.points, points):
        p.co = (*v, 1)
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def make_character(spec, mats):
    start = set(bpy.context.scene.objects)
    name = spec["id"]
    skin = mats[spec.get("skin", "skin_warm")]
    suit = mats[spec["suit"]]
    shirt = mats["shirt"]
    tie = mats[spec["tie"]]
    hair = mats[spec["hair"]]
    accent = mats[spec.get("accent", "gold")]
    head_w = spec.get("head_w", 0.46)
    head_h = spec.get("head_h", 0.54)
    # Body silhouette: slightly exaggerated torso and large head for readable satire.
    ellipsoid(name+" | torso", (0, 0, 1.42), (0.57, 0.34, 0.68), suit)
    box(name+" | shirt bib", (0, -0.304, 1.68), (0.29, 0.035, 0.52), shirt, 0.035)
    # Tie with two distinct shapes, kept separate for future animation/material edits.
    ellipsoid(name+" | tie knot", (0, -0.34, 1.88), (0.075, 0.045, 0.09), tie, 16, 10)
    box(name+" | tie blade", (0, -0.345, 1.65), (0.105, 0.045, 0.35), tie, 0.025)
    # Neck and oversized expressive head.
    rod(name+" | neck", (0, 0, 1.9), (0, 0, 2.12), 0.16, skin)
    ellipsoid(name+" | head", (0, -0.005, 2.43), (head_w, 0.39, head_h), skin, 32, 20)
    # Ears
    for side in (-1, 1):
        ellipsoid(name+" | ear", (side*(head_w+0.015), -0.005, 2.43), (0.095, 0.10, 0.15), skin, 16, 10)
    # Nose, cheeks, eyes, pupils, eyebrows, and mouth create a legible face at medium shots.
    ellipsoid(name+" | nose", (0, -0.39, 2.39), (0.105, 0.11, 0.16), skin, 20, 12)
    for side in (-1, 1):
        x = side * head_w * 0.43
        ellipsoid(name+" | eye white", (x, -0.351, 2.53), (0.115, 0.052, 0.09), mats["eye_white"], 20, 12)
        ellipsoid(name+" | pupil", (x, -0.402, 2.525), (0.044, 0.027, 0.052), mats["eye_dark"], 16, 10)
        curve_line(name+" | eyebrow", [(x-0.11, -0.405, 2.65+spec.get("brow_lift",0)),
                                      (x, -0.42, 2.69+spec.get("brow_lift",0)),
                                      (x+0.11, -0.405, 2.65+spec.get("brow_lift",0))], hair, 0.035)
    mouth_z = 2.25
    if spec["expression"] == "smug":
        pts = [(-0.15,-0.377,mouth_z-0.015),(0,-0.397,mouth_z+0.015),(0.16,-0.37,mouth_z+0.065)]
    elif spec["expression"] == "sleepy":
        pts = [(-0.15,-0.38,mouth_z),(0,-0.4,mouth_z-0.015),(0.15,-0.38,mouth_z)]
    elif spec["expression"] == "shout":
        ellipsoid(name+" | open mouth", (0, -0.391, mouth_z), (0.105, 0.035, 0.12), mats["mouth"], 20, 12)
        pts = [(-0.13,-0.38,mouth_z+0.12),(0,-0.4,mouth_z+0.14),(0.13,-0.38,mouth_z+0.12)]
    else:
        pts = [(-0.14,-0.38,mouth_z),(0,-0.4,mouth_z-0.025),(0.14,-0.38,mouth_z)]
    curve_line(name+" | mouth line", pts, mats["mouth_line"], 0.025)
    # Hair cap and signature hair detail.
    ellipsoid(name+" | hair cap", (0, 0.01, 2.78), (head_w*1.02, 0.36, 0.22), hair, 24, 12)
    if spec.get("hair_style") == "side":
        ellipsoid(name+" | side swept hair", (0.15, -0.12, 2.82), (0.24, 0.27, 0.12), hair, 20, 10)
    elif spec.get("hair_style") == "tuft":
        for i in range(3):
            ellipsoid(name+" | hair tuft", (-0.12+i*0.12, -0.02, 2.96+(i%2)*0.035), (0.12,0.16,0.13), hair, 16, 10)
    elif spec.get("hair_style") == "bald":
        # The cap is replaced by a very small side fringe for a distinctive bald silhouette.
        bpy.data.objects.get(name+" | hair cap").hide_render = True
        ellipsoid(name+" | side fringe", (-head_w*0.72, 0.02, 2.68), (0.13,0.32,0.12), hair, 16, 10)
    # Arms use separated shoulder/upper-arm/forearm pieces, so a later rigging pass can replace pivots.
    pose = spec["pose"]
    for side in (-1, 1):
        shoulder = (side*0.48, 0, 1.77)
        if pose == "orator" and side == 1:
            elbow, wrist = (side*0.78,-0.02,1.58),(side*0.95,-0.06,2.02)
            hand = (side*1.0,-0.08,2.12)
        elif pose == "phone" and side == -1:
            elbow, wrist = (side*0.65,-0.05,1.4),(side*0.48,-0.22,1.63)
            hand = (side*0.44,-0.25,1.72)
        elif pose == "shrug":
            elbow, wrist = (side*0.78,0,1.95),(side*0.98,-0.03,2.08)
            hand = (side*1.08,-0.04,2.12)
        elif pose == "sleepy":
            elbow, wrist = (side*0.65,0.0,1.45),(side*0.48,-0.15,1.2)
            hand = (side*0.42,-0.18,1.16)
        else:
            elbow, wrist = (side*0.72,-0.02,1.45),(side*0.76,-0.14,1.2)
            hand = (side*0.76,-0.19,1.13)
        rod(name+" | upper arm", shoulder, elbow, 0.16, suit)
        ellipsoid(name+" | elbow", elbow, (0.16,0.15,0.16), suit, 16, 10)
        rod(name+" | forearm", elbow, wrist, 0.12, suit)
        ellipsoid(name+" | hand", hand, (0.13,0.10,0.12), skin, 16, 10)
        # Thumb and three simplified fingers add silhouette detail without noisy geometry.
        for finger in range(3):
            fx = hand[0] + (finger-1)*0.055
            rod(name+" | finger", (fx,hand[1]-0.04,hand[2]-0.01), (fx+(side*0.012),hand[1]-0.05,hand[2]-0.105), 0.025, skin, 8)
    # Jacket lapels and pocket square.
    for side in (-1, 1):
        lapel = box(name+" | lapel", (side*0.19,-0.332,1.79), (0.18,0.045,0.40), accent, 0.025,
                    (0, side*math.radians(14), side*math.radians(8)))
        ellipsoid(name+" | pocket square", (side*0.38,-0.35,1.87), (0.07,0.025,0.045), mats["pocket"], 12, 8)
    # Legs/feet: neutral standing base, suitable for blocking and camera staging.
    for side in (-1,1):
        box(name+" | trouser leg", (side*0.23,0,0.64), (0.28,0.33,0.85), mats["trouser"], 0.07)
        ellipsoid(name+" | shoe", (side*0.23,-0.12,0.16), (0.20,0.34,0.13), mats["shoe"], 16, 10)
    # Prop assigned per archetype.
    if pose == "phone":
        box(name+" | smartphone", (-0.44,-0.34,1.84), (0.16,0.045,0.26), mats["phone"], 0.025)
        box(name+" | phone screen", (-0.44,-0.367,1.84), (0.12,0.012,0.20), mats["screen"], 0.01)
    if pose == "papers":
        box(name+" | document folder", (0.42,-0.37,1.24), (0.42,0.055,0.32), mats["paper"], 0.025)
        for j in range(2):
            box(name+" | paper sheet", (0.42,-0.408,1.25+j*0.015), (0.34,0.012,0.25), mats["shirt"], 0.006)
    return [o for o in bpy.context.scene.objects if o not in start]


def render_setup(out, samples):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = samples
    # Ubuntu repository Blender may be built without OpenImageDenoiser.
    # Disable denoising explicitly so headless renders remain portable.
    s.cycles.use_denoising = False
    s.render.resolution_x, s.render.resolution_y = 1600, 1000
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.view_settings.view_transform = "AgX"
    s.world.color = (0.12,0.12,0.12)
    def light(name, loc, power, size, target):
        bpy.ops.object.light_add(type="AREA", location=loc)
        o=bpy.context.object; o.name=name; o.data.energy=power; o.data.shape="DISK"; o.data.size=size
        o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
    light("Cast | key", (4,-7,8), 1100, 6, (0,0,1.5))
    light("Cast | fill", (-5,-3,5), 850, 5, (0,0,1.6))
    light("Cast | rim", (1,4,6), 1200, 4, (0,0,1.8))
    bpy.ops.object.camera_add(location=(5,-10,4.3))
    cam=bpy.context.object; cam.name="Cast | preview camera"
    cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens=58
    s.camera=cam


def main():
    opt=parse_args()
    out=Path(opt.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    mats={
      "skin_warm":material("Skin | warm medium", (0.53,0.30,0.20),0.62),
      "skin_olive":material("Skin | olive", (0.40,0.29,0.18),0.62),
      "skin_deep":material("Skin | deep brown", (0.25,0.12,0.075),0.62),
      "eye_white":material("Face | eye ivory",(0.93,0.88,0.75),0.28),
      "eye_dark":material("Face | pupil",(0.025,0.018,0.014),0.22),
      "mouth":material("Face | mouth interior",(0.13,0.015,0.025),0.6),
      "mouth_line":material("Face | mouth line",(0.19,0.055,0.035),0.6),
      "navy":material("Suit | midnight navy",(0.035,0.07,0.15),0.52),
      "teal":material("Suit | deep teal",(0.025,0.22,0.20),0.52),
      "burgundy":material("Suit | burgundy",(0.25,0.035,0.07),0.52),
      "charcoal":material("Suit | charcoal",(0.10,0.11,0.13),0.52),
      "shirt":material("Shirt | warm white",(0.92,0.87,0.76),0.6),
      "red_tie":material("Tie | red",(0.55,0.035,0.045),0.38),
      "blue_tie":material("Tie | cobalt",(0.035,0.13,0.42),0.38),
      "green_tie":material("Tie | green",(0.025,0.26,0.13),0.38),
      "hair_dark":material("Hair | dark",(0.035,0.025,0.022),0.75),
      "hair_grey":material("Hair | grey",(0.34,0.32,0.28),0.75),
      "gold":material("Accent | muted brass",(0.62,0.36,0.08),0.35,0.45),
      "pocket":material("Pocket square",(0.76,0.055,0.07),0.4),
      "trouser":material("Trouser | dark charcoal",(0.055,0.06,0.075),0.65),
      "shoe":material("Shoes | polished leather",(0.035,0.025,0.02),0.28),
      "phone":material("Phone | graphite",(0.055,0.065,0.08),0.24,0.25),
      "screen":material("Phone | lit screen",(0.08,0.38,0.55),0.2),
      "paper":material("Folder | red leather",(0.45,0.035,0.045),0.5),
    }
    specs=[
      {"id":"char_orator","suit":"navy","tie":"red_tie","hair":"hair_dark","hair_style":"side","expression":"shout","pose":"orator","skin":"skin_warm","brow_lift":0.02},
      {"id":"char_phone_scroller","suit":"teal","tie":"blue_tie","hair":"hair_dark","hair_style":"bald","expression":"smug","pose":"phone","skin":"skin_olive","head_w":0.48},
      {"id":"char_sleepy_member","suit":"charcoal","tie":"green_tie","hair":"hair_grey","hair_style":"side","expression":"sleepy","pose":"sleepy","skin":"skin_deep","head_h":0.56},
      {"id":"char_paper_shuffler","suit":"burgundy","tie":"blue_tie","hair":"hair_dark","hair_style":"tuft","expression":"neutral","pose":"papers","skin":"skin_warm","head_w":0.43},
      {"id":"char_defensive_member","suit":"navy","tie":"green_tie","hair":"hair_grey","hair_style":"bald","expression":"smug","pose":"shrug","skin":"skin_deep","head_w":0.50,"brow_lift":0.03},
      {"id":"char_opposition_speaker","suit":"charcoal","tie":"red_tie","hair":"hair_dark","hair_style":"tuft","expression":"shout","pose":"orator","skin":"skin_olive","head_h":0.58},
    ]
    render_setup(out,opt.samples)
    s=bpy.context.scene
    manifest={"pack":"Fictional Satirical Parliament Character Cast","version":1,
      "usage_note":"Anonymous fictional caricatures for political satire; not likenesses of real people.",
      "rigging_note":"Parts are separate named objects for future rigging. This first pass is pose-ready but not yet armature-rigged.",
      "characters":[]}
    for spec in specs:
        # Each character is authored at origin and exported independently for scene placement.
        objs=make_character(spec,mats)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0]
        glb=out/(spec["id"]+".glb")
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,export_apply=True)
        # Render a per-character evidence image before removing the model.
        s.camera.data.lens=58
        s.render.filepath=str(out/(spec["id"]+"_preview.png"))
        bpy.ops.render.render(write_still=True)
        manifest["characters"].append({"id":spec["id"],"file":glb.name,"preview":spec["id"]+"_preview.png",
                                       "expression":spec["expression"],"pose":spec["pose"],
                                       "status":"generated_pending_visual_review"})
        bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("PARLIAMENT_CHARACTER_PACK="+str(out))
    print("CHARACTERS="+", ".join(x["id"] for x in specs))


if __name__=="__main__":
    main()
