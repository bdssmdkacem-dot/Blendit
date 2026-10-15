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
      (2.075,.115,.125,-.030),(2.105,.205,.185,-.028),
      (2.16,.285,.238,-.023),(2.235,.342,.278,-.015),
      (2.315,.378,.309,.000),(2.405,.420,.332,.008),
      (2.505,.444,.350,.012),(2.615,.452,.356,.014),
      (2.725,.440,.350,.015),(2.825,.412,.337,.018),
      (2.915,.365,.310,.020),(2.985,.300,.266,.020),
      (3.045,.220,.210,.018),(3.085,.125,.132,.015),
      (3.095,.035,.045,.012)]
    n=64; verts=[]; faces=[]
    for ri,(z,rx,ry,yc) in enumerate(rings):
        for j in range(n):
            t=2*math.pi*j/n
            cs=math.cos(t); sn=math.sin(t)
            # Front is -Y. Project the lower face forward at the chin,
            # pull the mouth/jaw back slightly, and flatten the cheek planes.
            front=max(0.0,-sn)
            lower=max(0.0,min(1.0,(2.48-z)/.38))
            chin_push=.095*math.exp(-((z-2.14)/.115)**2)*front
            cheek_flat=.045*math.exp(-((z-2.43)/.145)**2)*front
            jaw_taper=1.0-.035*lower
            x=rx*cs*jaw_taper
            y=yc+ry*sn-chin_push+cheek_flat
            # Sculpt facial planes directly into the continuous skull surface.
            # Positive displacement recesses the orbit; negative displacement brings
            # brow, cheekbone and muzzle planes forward without attaching extra spheres.
            frontal=max(0.0,-sn)**4
            def bump(cx,cz,sx,sz,depth):
                return depth*math.exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
            orbit=0.0
            for side in (-1,1):
                orbit += bump(side*.17,2.665,.115,.067,.025)
                orbit += bump(side*.205,2.465,.145,.120,-.040)
                orbit += bump(side*.285,2.565,.115,.155,-.020)
            brow_plane=0.0
            for side in (-1,1):
                brow_plane += bump(side*.17,2.715,.145,.052,-.030)
            muzzle=bump(0.0,2.365,.155,.090,-.016)
            y += frontal*(orbit+brow_plane+muzzle)
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
    # Face rebuild pass: landmarks are sunk into the head surface wherever possible.
    # The nose is a single lofted anatomical form, not stacked spheres.
    head_mesh(skin)
    for side in (-1,1):
        uv("V4 | integrated ear",(side*.397,.006,2.535),(.048,.052,.103),skin,40,28)
        line("V4 | ear antihelix",[(side*.397,-.041,2.578),(side*.386,-.045,2.55),(side*.397,-.041,2.515)],skin_shadow,.005)
        x=side*.169
        uv("V4 | orbital shadow",(x,-.323,2.665),(.090,.010,.034),skin_shadow,40,24)
        uv("V4 | eye",(x,-.337,2.665),(.057,.012,.019),eye,40,24)
        uv("V4 | iris",(x-side*.003,-.349,2.665),(.015,.006,.015),iris,28,18)
        uv("V4 | pupil",(x-side*.003,-.354,2.665),(.007,.004,.009),black,20,12)
        line("V4 | upper eyelid",[(x-.078,-.318,2.669),(x-.040,-.330,2.680),(x+.006,-.332,2.681),(x+.078,-.318,2.665)],skin,.010)
        line("V4 | lower eyelid",[(x-.075,-.318,2.658),(x-.025,-.328,2.653),(x+.035,-.328,2.654),(x+.075,-.318,2.658)],skin_shadow,.005)
        uv("V4 | brow ridge",(x,-.309,2.714),(.100,.010,.022),skin,40,24)
        line("V4 | brow",[(x-.108,-.319,2.735),(x-.061,-.329,2.748),(x-.012,-.332,2.747),(x+.045,-.327,2.737),(x+.103,-.315,2.727)],hair,.012)
    nose_rings=[
        (2.603,.012,.010,-.329),(2.575,.023,.020,-.342),
        (2.535,.030,.030,-.356),(2.495,.038,.036,-.369),
        (2.474,.040,.032,-.375),(2.457,.029,.022,-.371),
        (2.449,.014,.014,-.360)]
    nv=[]; nf=[]; nn=32
    for z,rx,ry,cy in nose_rings:
        for j in range(nn):
            t=2*math.pi*j/nn
            nv.append((rx*math.cos(t),cy+ry*math.sin(t),z))
    for i in range(len(nose_rings)-1):
        for j in range(nn):
            aa=i*nn+j; bb=i*nn+(j+1)%nn
            nf.append((aa,bb,bb+nn,aa+nn))
    nf.extend([tuple(range(nn-1,-1,-1)),tuple((len(nose_rings)-1)*nn+j for j in range(nn))])
    nm=bpy.data.meshes.new("Integrated tapered nose mesh"); nm.from_pydata(nv,[],nf); nm.update()
    no=bpy.data.objects.new("V4 | integrated nose bridge and tip",nm); bpy.context.collection.objects.link(no); no.data.materials.append(skin)
    for p in nm.polygons:p.use_smooth=True
    ns=no.modifiers.new("Nose surface refinement","SUBSURF"); ns.levels=2; ns.render_levels=2
    for side in (-1,1):
        uv("V4 | alar wing",(side*.030,-.366,2.461),(.015,.012,.011),skin,32,20)
        uv("V4 | nostril",(side*.027,-.382,2.454),(.006,.003,.0035),black,20,12)
    # Restrained adult mouth: narrow lip volumes, defined philtrum and subtle asymmetry.
    line("V4 | philtrum left",[(-.020,-.327,2.385),(-.016,-.333,2.357)],skin_shadow,.003)
    line("V4 | philtrum right",[(.020,-.327,2.385),(.016,-.333,2.357)],skin_shadow,.003)
    uv("V4 | upper lip",(0,-.333,2.337),(.067,.009,.011),skin_shadow,36,20)
    line("V4 | mouth line",[(-.070,-.339,2.337),(-.036,-.342,2.333),(0,-.343,2.331),(.040,-.342,2.335),(.070,-.338,2.34)],black,.004)
    uv("V4 | lower lip",(0,-.333,2.315),(.056,.009,.010),skin,36,20)
    # Chin crease gives the lower face a less smooth, toy-like transition.
    line("V4 | chin crease",[(-.045,-.315,2.255),(0,-.321,2.248),(.045,-.315,2.255)],skin_shadow,.003)
    # Hairline follows a flatter, slightly receding adult forehead silhouette.
    uv("V4 | hair cap",(0,.020,2.968),(.425,.326,.172),hair,48,28)
    # Fine swept grooves replace the previous stacked bulb-like hair locks.
    for i in range(5):
        x=-.29+i*.145
        line("V4 | swept hair groove",[(x,-.275,2.975),(x+.035,-.285,3.010),(x+.075,-.245,3.040)],hair,.003)
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
    face_review_renders=[]
    for name,loc in cams:
        bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name="V4 camera | "+name
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.lens=58;scene.camera=cam
        scene.render.filepath=str(out/f"idriss_v4_{name}.png");bpy.ops.render.render(write_still=True);face_review_renders.append(f"idriss_v4_{name}.png")
        bpy.data.objects.remove(cam,do_unlink=True)
    # Additional face-review renders: the full-body views are too small to judge
    # eyelid contact, nose-to-cheek transitions, mouth placement and the skull
    # silhouette reliably. Keep these as independent close-ups, not replacements.
    head_target=Vector((0,-.02,2.665))
    head_cams=[
        ("head_front",(0,-3.8,2.68)),
        ("head_three_quarter",(2.55,-3.65,2.72)),
        ("head_profile",(4.2,-.02,2.68)),
    ]
    for name,loc in head_cams:
        bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name="V4 face-review camera | "+name
        cam.rotation_euler=(head_target-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.lens=72;scene.camera=cam
        scene.render.filepath=str(out/f"idriss_v4_{name}.png")
        bpy.ops.render.render(write_still=True);renders.append(f"idriss_v4_{name}.png")
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
      "reference_usage":"includes newly added Idriss reference JPG; compare proportions against it during human review",
      "outputs":{"model":"idriss_el_azami_v4.glb","renders":[f"idriss_v4_{name}.png" for name,loc in cams]},
      "face_review_renders":face_review_renders,
      "approval_status":"pending_human_visual_review",
      "likeness_verified":False,
      "reason":"The repository notes that current images are design renders, not verified photographic likeness evidence; visual similarity must be reviewed before approval.",
      "checks":{"render_views":len(renders),"exported_geometry_objects":len(model_names),"render_resolution":"1200x1200"}
    }
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False))
if __name__=="__main__":
    opt=args();out=Path(opt.output_dir).resolve();out.mkdir(parents=True,exist_ok=True);build(out,opt.samples)
