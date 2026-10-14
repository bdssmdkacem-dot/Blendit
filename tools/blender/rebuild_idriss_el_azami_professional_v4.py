"""Independent V4 sculpt-style rebuild for Idriss El Azami El Idrissi.
The reference images are used as design guides, not proof of verified real-person likeness.
Outputs GLB + front, three-quarter and profile renders; approval remains pending human review.
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

def args():
    av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",default="build/idriss-v4")
    p.add_argument("--samples",type=int,default=24)
    return p.parse_known_args(av)[0]

def mat(name, color, rough=.48, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1); b.inputs["Roughness"].default_value=rough
    b.inputs["Metallic"].default_value=metallic
    return m

def smooth(o, name, material):
    o.name=name
    if material: o.data.materials.append(material)
    if o.type=="MESH":
        for p in o.data.polygons: p.use_smooth=True
    return o

def uv(name, loc, scale, material, seg=40, rings=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return smooth(o,name,material)

def cube(name, loc, dims, material, bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=o.modifiers.new("Tailored softened edges","BEVEL"); mod.width=bevel; mod.segments=4
        o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return smooth(o,name,material)

def rod(name, a, b, radius, material, vertices=20):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=(a+b)/2)
    o=bpy.context.object; o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    return smooth(o,name,material)

def line(name, pts, material, width=.018):
    c=bpy.data.curves.new(name,"CURVE"); c.dimensions="3D"; c.resolution_u=16
    c.bevel_depth=width; c.bevel_resolution=4
    s=c.splines.new("BEZIER"); s.bezier_points.add(len(pts)-1)
    for bp, p in zip(s.bezier_points,pts):
        bp.co=p; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    return o

def head_mesh(skin):
    # Continuous lofted head with a tapered jaw and broad cheek/temple transitions.
    # Rings are elliptical cross sections, not a sphere with facial pieces stuck on.
    # Explicit anatomical cross-sections: chin, jaw angle, cheek plane,
    # temple, brow and cranial vault are shaped as one continuous surface.
    rings=[
      (2.075,.155,.160,-.030),(2.105,.245,.208,-.028),
      (2.16,.315,.255,-.023),(2.235,.365,.292,-.015),
      (2.315,.392,.320,.000),(2.405,.425,.337,.008),
      (2.505,.447,.350,.012),(2.615,.458,.356,.014),
      (2.725,.452,.354,.015),(2.825,.430,.346,.018),
      (2.915,.390,.325,.020),(2.985,.330,.285,.020),
      (3.045,.245,.225,.018),(3.085,.145,.145,.015),
      (3.095,.055,.065,.012)]
    n=64; verts=[]; faces=[]
    for ri,(z,rx,ry,yc) in enumerate(rings):
        for j in range(n):
            t=2*math.pi*j/n
            cs=math.cos(t); sn=math.sin(t)
            # Front is -Y. Project the lower face forward at the chin,
            # pull the mouth/jaw back slightly, and flatten the cheek planes.
            front=max(0.0,-sn)
            lower=max(0.0,min(1.0,(2.48-z)/.38))
            chin_push=.055*math.exp(-((z-2.13)/.10)**2)*front
            cheek_flat=.018*math.exp(-((z-2.43)/.16)**2)*front
            jaw_taper=1.0-.035*lower
            x=rx*cs*jaw_taper
            y=yc+ry*sn-chin_push+cheek_flat
            # Slightly narrower mid-face and broader upper temples avoid an egg profile.
            if 2.53<z<2.80:
                x*=1.0+.025*(1.0-front)
            verts.append((x,y,z))
    for i in range(len(rings)-1):
        for j in range(n):
            a=i*n+j; b=i*n+(j+1)%n
            faces.append((a,b,b+n,a+n))
    faces.append(tuple(range(n-1,-1,-1)))
    faces.append(tuple((len(rings)-1)*n+j for j in range(n)))
    mesh=bpy.data.meshes.new("Continuous facial silhouette mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new("V4 | continuous sculpted head",mesh); bpy.context.collection.objects.link(o); o.data.materials.append(skin)
    for p in mesh.polygons:p.use_smooth=True
    sub=o.modifiers.new("Sculpt surface subdivision","SUBSURF"); sub.levels=2; sub.render_levels=2
    return o

def build(out,samples):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    skin=mat("Skin | warm olive",(.48,.29,.19),.57)
    skin_shadow=mat("Skin | subtle warm shadow",(.34,.17,.105),.62)
    hair=mat("Hair | dark espresso",(.045,.028,.021),.72)
    suit=mat("Suit | deep midnight navy",(.025,.045,.095),.34)
    lapel=mat("Lapel | navy satin",(.065,.09,.15),.25)
    shirt=mat("Shirt | warm ivory",(.91,.87,.77),.48)
    tie=mat("Tie | muted burgundy",(.32,.025,.045),.28)
    eye=mat("Eyes | ivory",(.92,.86,.72),.24)
    iris=mat("Eyes | deep brown",(.075,.032,.018),.2)
    black=mat("Mouth and nostrils",(.095,.025,.018),.55)
    gold=mat("Buttons | brushed brass",(.43,.25,.075),.3,.62)
    shoe=mat("Shoes | polished charcoal",(.035,.032,.03),.24)
    # Legs and shoes: tailored silhouettes, deliberately no giant spheres for hands.
    for side in (-1,1):
        cube("V4 | tailored trouser", (side*.205,.015,.64),(.255,.32,.88),suit,.09)
        uv("V4 | shoe",(side*.205,-.115,.17),(.19,.32,.12),shoe)
    # Torso is a shaped low-poly-to-subdivision jacket mesh.
    levels=[(.98,.32,.20),(1.20,.43,.245),(1.56,.53,.29),(1.78,.59,.30),(1.91,.36,.24)]
    verts=[]; faces=[]; n=32
    for z,rx,ry in levels:
        for j in range(n):
            t=2*math.pi*j/n; verts.append((rx*math.cos(t),ry*math.sin(t),z))
    for i in range(len(levels)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
    faces.append(tuple(range(n-1,-1,-1)));faces.append(tuple((len(levels)-1)*n+j for j in range(n)))
    me=bpy.data.meshes.new("Tailored jacket mesh");me.from_pydata(verts,[],faces);me.update()
    body=bpy.data.objects.new("V4 | tailored jacket torso",me);bpy.context.collection.objects.link(body);body.data.materials.append(suit)
    for p in me.polygons:p.use_smooth=True
    sub=body.modifiers.new("Tailoring smooth","SUBSURF");sub.levels=2;sub.render_levels=2
    # Shoulder slope and sleeve segments form continuous visual flow.
    for side in (-1,1):
        shoulder=(side*.47,0,1.73); elbow=(side*.68,-.015,1.39); wrist=(side*.66,-.09,1.13)
        # Tapered sleeve segments avoid exposed spherical shoulder and elbow joints.
        rod("V4 | upper sleeve",shoulder,elbow,.132,suit)
        rod("V4 | forearm sleeve",elbow,wrist,.098,suit)
        # Palm and fingers are joined into a readable hand silhouette with distinct digits.
        hx=wrist[0]; hy=-.13; hz=1.04
        uv("V4 | palm",(hx,hy,hz),(.105,.075,.13),skin,32,20)
        for k in range(4):
            fx=hx+(k-1.5)*.044
            length=[.105,.135,.13,.095][k]
            rod("V4 | finger",(fx,hy-.018,hz-.035),(fx+side*.008,hy-.02,hz-.035-length),.018,skin,12)
        rod("V4 | thumb",(hx-side*.08,hy-.015,hz+.005),(hx-side*.135,hy-.02,hz-.065),.025,skin,12)
    # Neck enters collar; no long exposed neck.
    rod("V4 | neck",(0,.015,1.82),(0,.005,2.19),.135,skin,32)
    # Collar leaves: two shaped tapered panels, instead of a flat rectangular bib.
    line("V4 | left collar",[(-.16,-.255,1.91),(-.105,-.31,1.78),(0,-.32,1.86)],shirt,.035)
    line("V4 | right collar",[(.16,-.255,1.91),(.105,-.31,1.78),(0,-.32,1.86)],shirt,.035)
    cube("V4 | tie knot",(0,-.327,1.84),(.08,.035,.085),tie,.018)
    # tie blade taper
    verts=[(-.04,-.334,1.80),(.04,-.334,1.80),(.075,-.335,1.36),(-.075,-.335,1.36)]
    mesh=bpy.data.meshes.new("Tie blade mesh");mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update()
    o=bpy.data.objects.new("V4 | shaped tie blade",mesh);bpy.context.collection.objects.link(o);o.data.materials.append(tie)
    sol=o.modifiers.new("Tie thickness","SOLIDIFY");sol.thickness=.018
    # Lapels are tapered mesh panels, not boxes.
    for side in (-1,1):
        vs=[(side*.08,-.303,1.91),(side*.30,-.28,1.84),(side*.18,-.32,1.54),(side*.02,-.33,1.76)]
        me=bpy.data.meshes.new("Lapel panel mesh");me.from_pydata(vs,[],[(0,1,2,3)]);me.update()
        o=bpy.data.objects.new("V4 | tailored lapel",me);bpy.context.collection.objects.link(o);o.data.materials.append(lapel)
        so=o.modifiers.new("Lapel thickness","SOLIDIFY");so.thickness=.018
        be=o.modifiers.new("Lapel edge softness","BEVEL");be.width=.012;be.segments=2
        uv("V4 | jacket button",(side*.105,-.315,1.29),(.025,.018,.025),gold,20,12)
    # Facial forms are positioned from the revised skull landmarks, not decorative add-ons.
    head_mesh(skin)
    for side in (-1,1):
        uv("V4 | ear",(side*.425,.005,2.535),(.078,.092,.135),skin)
        uv("V4 | ear inner",(side*.454,-.064,2.535),(.025,.018,.061),skin_shadow,24,16)
        # Mature, narrower eye openings under a pronounced brow ridge; avoid toy-like round eyes.
        x=side*.174
        uv("V4 | eye socket",(x,-.304,2.663),(.112,.022,.052),skin_shadow)
        uv("V4 | eye",(x,-.324,2.663),(.076,.014,.024),eye,36,22)
        uv("V4 | iris",(x-side*.004,-.337,2.663),(.021,.007,.021),iris,24,16)
        uv("V4 | pupil",(x-side*.004,-.344,2.663),(.009,.004,.012),black,16,12)
        line("V4 | upper eyelid",[(x-.103,-.326,2.668),(x-.045,-.342,2.690),(x+.015,-.344,2.691),(x+.103,-.326,2.667)],skin_shadow,.015)
        line("V4 | lower eyelid",[(x-.096,-.326,2.653),(x,-.337,2.646),(x+.096,-.326,2.653)],skin_shadow,.009)
        # Brow has an inner weight and a tapered outer tail, rather than a uniform arch.
        line("V4 | brow",[(x-.118,-.315,2.733),(x-.065,-.338,2.752),(x-.010,-.347,2.754),(x+.055,-.339,2.741),(x+.112,-.315,2.727)],hair,.019)
    # A bridge, alar base and tip with a stronger but shorter profile transition.
    # Compact tapered nose planes reduce the round button-nose silhouette.
    uv("V4 | nose bridge",(0,-.343,2.535),(.043,.066,.128),skin,40,28)
    uv("V4 | nose tip",(0,-.389,2.478),(.058,.052,.043),skin,40,24)
    for side in (-1,1):
        uv("V4 | nose ala",(side*.044,-.372,2.463),(.027,.031,.023),skin,28,18)
    for side in (-1,1):
        uv("V4 | nostril",(side*.043,-.462,2.456),(.021,.012,.014),black,16,10)
        # Cheek volume remains integrated into the continuous head silhouette.
        line("V4 | subtle nasolabial fold",[(side*.105,-.345,2.405),(side*.16,-.347,2.37),(side*.205,-.33,2.395)],skin_shadow,.006)
    # Restrained adult mouth: narrow lip volumes, defined philtrum and subtle asymmetry.
    line("V4 | philtrum left",[(-.025,-.352,2.385),(-.018,-.361,2.357)],skin_shadow,.006)
    line("V4 | philtrum right",[(.025,-.352,2.385),(.018,-.361,2.357)],skin_shadow,.006)
    uv("V4 | upper lip",(0,-.356,2.337),(.082,.014,.014),skin_shadow,36,20)
    line("V4 | mouth line",[(-.087,-.367,2.337),(-.045,-.374,2.333),(0,-.376,2.331),(.047,-.373,2.335),(.087,-.365,2.34)],black,.008)
    uv("V4 | lower lip",(0,-.354,2.315),(.067,.012,.011),skin,36,20)
    # Chin crease gives the lower face a less smooth, toy-like transition.
    line("V4 | chin crease",[(-.052,-.333,2.255),(0,-.345,2.248),(.052,-.333,2.255)],skin_shadow,.006)
    # Hairline follows a flatter, slightly receding adult forehead silhouette.
    uv("V4 | hair cap",(0,.020,2.968),(.425,.326,.172),hair,48,28)
    # Fine swept grooves replace the previous stacked bulb-like hair locks.
    for i in range(5):
        x=-.29+i*.145
        line("V4 | swept hair groove",[(x,-.285,2.985),(x+.035,-.302,3.035),(x+.075,-.27,3.075)],hair,.004)
    # Studio scene and three cameras.
    floor=mat("Studio | warm slate",(.085,.095,.115),.78)
    cube("V4 | studio plinth",(0,0,.045),(1.6,1.2,.09),floor,.04)
    scene=bpy.context.scene; scene.render.engine="CYCLES";scene.cycles.samples=samples;scene.cycles.use_denoising=False  # Ubuntu Blender build lacks OpenImageDenoiser; keep render portable
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG";scene.view_settings.view_transform="AgX"
    scene.world.color=(.12,.12,.12)
    def light(name,loc,power,size,target):
        bpy.ops.object.light_add(type="AREA",location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape="DISK";o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
    light("V4 | key softbox",(4,-5,6),800,4,(0,0,1.8))
    light("V4 | fill softbox",(-4,-4,3.5),500,3,(0,0,1.8))
    light("V4 | rim softbox",(1,3,5),1000,3,(0,0,2))
    target=Vector((0,-.02,1.62))
    cams=[("front",(0,-8,2.05)),("three_quarter",(5,-7,2.5)),("profile",(8,-.05,2.2))]
    renders=[]
    for name,loc in cams:
        bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name="V4 camera | "+name
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.lens=58;scene.camera=cam
        scene.render.filepath=str(out/f"idriss_v4_{name}.png");bpy.ops.render.render(write_still=True);renders.append(f"idriss_v4_{name}.png")
        bpy.data.objects.remove(cam,do_unlink=True)
    # Export only model geometry, not cameras/lights/floor. Include all character pieces.
    model_names=[o for o in scene.objects if o.name.startswith("V4 |") and o.type in {"MESH","CURVE"}]
    bpy.ops.object.select_all(action="DESELECT")
    for o in model_names:o.select_set(True)
    bpy.context.view_layer.objects.active=model_names[0]
    bpy.ops.export_scene.gltf(filepath=str(out/"idriss_el_azami_v4.glb"),export_format="GLB",use_selection=True,export_apply=True)
    manifest={
      "asset_id":"idriss_el_azami_el_idrissi_v4",
      "build_generation":"independent_rebuild_not_patch_of_v1_v2_v3",
      "reference_directory":"source/parliament/references/idriss_el_azami_el_idrissi/",
      "reference_usage":"existing design references; no new user reference uploaded",
      "outputs":{"model":"idriss_el_azami_v4.glb","renders":renders},
      "approval_status":"pending_human_visual_review",
      "likeness_verified":False,
      "reason":"The repository notes that current images are design renders, not verified photographic likeness evidence; visual similarity must be reviewed before approval.",
      "checks":{"render_views":len(renders),"exported_geometry_objects":len(model_names),"render_resolution":"1200x1200"}
    }
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False))
if __name__=="__main__":
    opt=args();out=Path(opt.output_dir).resolve();out.mkdir(parents=True,exist_ok=True);build(out,opt.samples)
