"""Build an independent, reference-led stylized 3D character asset for Idriss El Azami.
This is an art-direction prototype, NOT a verified likeness of the real person.
Requires Blender 3.6+; writes .blend, .glb, front/three-quarter/profile renders and manifest.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

def args():
    av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out="build/idriss-el-azami"
    if "--output-dir" in av: out=av[av.index("--output-dir")+1]
    refs=Path("source/parliament/references/idriss_el_azami_el_idrissi")
    return Path(out), refs

def mat(n,c,rough=.48,metal=0):
    m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*c,1); p.inputs["Roughness"].default_value=rough
    p.inputs["Metallic"].default_value=metal
    return m

def finish(o,n,m,smooth=True):
    o.name=n
    if m and hasattr(o.data,"materials"): o.data.materials.append(m)
    if smooth and o.type=="MESH":
        for f in o.data.polygons: f.use_smooth=True
    return o

def ball(n,loc,scale,m,seg=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,n,m)

def cube(n,loc,dim,m,bevel=.06,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.dimensions=dim
    if rot:o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new("Tailored soft edges","BEVEL"); b.width=bevel; b.segments=3
        o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return finish(o,n,m,False)

def rod(n,a,b,r,m,verts=16):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d.length,location=(a+b)/2)
    o=bpy.context.object; o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    return finish(o,n,m)

def line(n,pts,m,r=.018):
    c=bpy.data.curves.new(n,"CURVE"); c.dimensions="3D"; c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new("POLY");s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts):p.co=(*v,1)
    o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

def build(args_value):
    out, refs = args_value
    reference_files = [refs / n for n in ("idriss_el_azami_el_idrissi_front.jpg", "idriss_el_azami_el_idrissi_three_quarter.jpg", "idriss_el_azami_el_idrissi_profile.jpg", "idriss_el_azami_front.jpg")]
    available_refs = [p for p in reference_files if p.is_file() and p.stat().st_size > 1000]
    if not available_refs:
        raise RuntimeError(f"No repository character design references found in {refs}")
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    # Load repository design sheets as hidden, non-rendering references in the .blend.
    # Do not copy these images into output; they remain source-controlled files.
    ref_collection = bpy.data.collections.new("REFERENCE SHEETS | repository only")
    bpy.context.scene.collection.children.link(ref_collection)
    for ref_path in available_refs:
        img = bpy.data.images.load(str(ref_path.resolve()), check_existing=True)
        obj = bpy.data.objects.new("REFERENCE | " + ref_path.name, None)
        obj.empty_display_type = "IMAGE"
        obj.data = img
        obj.hide_render = True
        obj.hide_viewport = True
        obj["source_path"] = ref_path.as_posix()
        obj["reference_role"] = "stylized design and wardrobe guide; not photographic identity proof"
        ref_collection.objects.link(obj)
    # restrained, production-friendly palette based on the supplied design sheets
    skin=mat("Skin | warm olive beige",(0.53,.34,.23),.58)
    skin_hi=mat("Skin | warm highlights",(.66,.45,.32),.62)
    hair=mat("Hair | bald scalp shadow",(.53,.34,.23),.78)
    hair_hi=mat("Skin | scalp highlight",(.66,.45,.32),.72)
    suit=mat("Suit | deep midnight navy",(.025,.055,.105),.36)
    lapel=mat("Lapel | navy satin",(.055,.09,.15),.28)
    shirt=mat("Shirt | ivory",(.86,.84,.77),.42)
    green=mat("Tie | cobalt blue matching approved portrait",(.035,.12,.48),.3)
    gold=mat("Pin | brushed gold",(.68,.39,.08),.25,.72)
    black=mat("Shoes | polished oxblood black",(.055,.025,.023),.25)
    glasses=mat("Glasses | dark tortoiseshell",(.045,.03,.025),.22,.15)
    white=mat("Eyes | warm ivory",(.92,.86,.73),.3)
    iris=mat("Eyes | dark hazel",(.13,.075,.035),.25)
    pupil=mat("Eyes | pupil",(.012,.009,.008),.2)
    mouth=mat("Mouth | dark muted rose",(.19,.065,.055),.6)
    stubble=mat("Facial hair | charcoal grey",(.16,.15,.14),.85)
    # Load repository design sheets as hidden, non-rendering references in the .blend.
    # Do not pack or copy them into generated outputs; they remain source-controlled files.
    ref_collection = bpy.data.collections.new("REFERENCE SHEETS | repository only")
    bpy.context.scene.collection.children.link(ref_collection)
    for ref_path in available_refs:
        img = bpy.data.images.load(str(ref_path.resolve()), check_existing=True)
        obj = bpy.data.objects.new("REFERENCE | " + ref_path.name, None)
        obj.empty_display_type = "IMAGE"
        obj.data = img
        obj.hide_render = True
        obj.hide_viewport = True
        obj["source_path"] = ref_path.as_posix()
        obj["reference_role"] = "stylized design and wardrobe guide; not photographic identity proof"
        ref_collection.objects.link(obj)
    # feet, trouser silhouette and bespoke suit torso
    for s in (-1,1):
        x=s*.235
        cube("Trousers | tailored leg", (x,.005,.66),(.30,.37,.88),suit,.075)
        ball("Shoes | sculpted toe",(x,-.14,.17),(.205,.34,.13),black)
        cube("Shoes | sole",(x,-.13,.095),(.39,.51,.055),black,.025)
        # cuffs and subtle seams
        line("Trousers | pressed crease",[(x,-.19,.32),(x,-.19,.82),(x,-.19,1.04)],lapel,.006)
    # torso has shaped shoulder line, waist taper, layered shirt
    ball("Jacket | sculpted torso",(0,.015,1.43),(.57,.34,.68),suit)
    ball("Jacket | shoulder left",(-.39,.005,1.79),(.30,.32,.22),suit)
    ball("Jacket | shoulder right",(.39,.005,1.79),(.30,.32,.22),suit)
    cube("Shirt | front placket",(0,-.313,1.67),(.30,.055,.49),shirt,.035)
    # collar triangles as small tailored panels
    cube("Shirt | collar left",(-.095,-.352,1.88),(.13,.035,.20),shirt,.018,(0,-.22,-.12))
    cube("Shirt | collar right",(.095,-.352,1.88),(.13,.035,.20),shirt,.018,(0,.22,.12))
    ball("Tie | knot",(0,-.378,1.83),(.083,.045,.085),green)
    # tie blade tapered polygon
    mesh=bpy.data.meshes.new("Tie blade mesh")
    verts=[(-.055,-.38,1.78),(.055,-.38,1.78),(.105,-.38,1.36),(0,-.38,1.29),(-.105,-.38,1.36)]
    faces=[(0,1,2,3,4)];mesh.from_pydata(verts,[],faces);mesh.materials.append(green)
    ob=bpy.data.objects.new("Tie | tapered cobalt-blue blade",mesh);bpy.context.collection.objects.link(ob)
    sol=ob.modifiers.new("Tie thickness","SOLIDIFY");sol.thickness=.025
    # jacket fronts, lapels, buttons and pocket
    for s in (-1,1):
        cube("Jacket | tailored lapel",(s*.17,-.353,1.72),(.16,.045,.38),lapel,.018,(0,s*.19,s*.12))
        for z in (1.52,1.65,1.78):
            ball("Jacket | brass button",(s*.095,-.385,z),(.022,.014,.022),gold,16,10)
        cube("Jacket | pocket welt",(s*.37,-.348,1.69),(.13,.018,.025),lapel,.008)
    # neck and custom head proportions, cheeks/jaw, ears
    rod("Neck",(0,0,1.88),(0,0,2.18),.155,skin)
    ball("Head | cranial volume",(0,0,2.49),(.405,.365,.50),skin,48,32)
    ball("Head | lower jaw",(0,-.018,2.29),(.33,.34,.27),skin,40,28)
    for s in (-1,1):
        ball("Ears | outer",(s*.405,-.005,2.47),(.082,.09,.13),skin,24,16)
        ball("Ears | inner",(s*.431,-.071,2.47),(.035,.025,.075),skin_hi,20,12)
        ball("Cheeks | subtle volume",(s*.22,-.276,2.39),(.14,.085,.13),skin_hi,24,16)
    # brow ridge and eyes set into face
    for s in (-1,1):
        x=s*.155
        ball("Eyes | socket",(x,-.328,2.55),(.12,.046,.085),skin_hi,24,16)
        ball("Eyes | sclera",(x,-.365,2.55),(.083,.028,.052),white,24,16)
        ball("Eyes | iris",(x+.008,-.389,2.548),(.033,.014,.036),iris,20,12)
        ball("Eyes | pupil",(x+.009,-.401,2.548),(.015,.009,.02),pupil,16,10)
        ball("Eyes | catchlight",(x+.016,-.409,2.563),(.007,.005,.008),white,12,8)
        line("Brows | expressive silver charcoal",[(x-.10,-.372,2.645),(x,-.394,2.672),(x+.09,-.37,2.65)],hair,.025)
    # long, distinct nose bridge and tip
    ball("Nose | bridge",(0,-.369,2.43),(.067,.08,.14),skin_hi,28,18)
    ball("Nose | tip",(0,-.427,2.385),(.075,.065,.055),skin,24,16)
    for s in (-1,1):ball("Nose | nostril",(s*.037,-.475,2.365),(.016,.009,.012),stubble,12,8)
    # mouth, philtrum, mustache and neat stubble: graphic but not photographic claims
    line("Mouth | upper lip",[(-.105,-.375,2.285),(-.045,-.397,2.292),(0,-.401,2.28),(.045,-.397,2.292),(.105,-.375,2.285)],mouth,.012)
    line("Mouth | lower lip",[(-.075,-.382,2.265),(0,-.399,2.258),(.075,-.382,2.265)],skin_hi,.01)
    for s in (-1,1):
        ball("Mustache | shaped lobe",(s*.064,-.388,2.31),(.075,.035,.028),stubble,24,12)
        # controlled stubble patches along jawline, intentionally individual and subtle
        for i in range(7):
            xx=s*(.17+i*.022)
            zz=2.22+(i%3)*.026
            ball("Stubble | jaw fleck",(xx,-.326+(i%2)*-.01,zz),(.009,.008,.012),stubble,10,8)
    # Bald head matching the official campaign portrait; do not invent a silver hairstyle.
    ball("Scalp | clean bald crown",(0,.015,2.84),(.382,.335,.115),skin,40,24)
    # subtle grey stubble follows the lower jaw
    for i in range(17):
        x=-.24+i*.03
        for z in (2.22,2.245):
            ball("Stubble | jawline detail",(x,-.30,z),(.008,.006,.009),stubble,10,8)
    # rectangular glasses with rims, bridge, temples; front faces -Y
    for s in (-1,1):
        x=s*.153
        # four bars make rectangular frame, with slightly rounded optical corners
        z0,z1=2.49,2.615; xl,xr=x-.105,x+.105
        line("Glasses | lens frame",[(xl,-.413,z0),(xl,-.413,z1),(xr,-.413,z1),(xr,-.413,z0),(xl,-.413,z0)],glasses,.012)
        rod("Glasses | temple",(s*.255,-.405,2.59),(s*.39,-.12,2.59),.012,glasses,10)
    rod("Glasses | bridge",(-.048,-.416,2.585),(.048,-.416,2.585),.012,gold,12)
    # arms, sleeves, cuffs and fully separated hands with thumb + four fingers
    for s in (-1,1):
        shoulder=(s*.46,0,1.78); elbow=(s*.68,-.015,1.48); wrist=(s*.72,-.13,1.23)
        rod("Sleeves | upper arm",shoulder,elbow,.145,suit)
        ball("Sleeves | elbow",elbow,(.145,.14,.15),suit)
        rod("Sleeves | forearm",elbow,wrist,.112,suit)
        rod("Cuffs | ivory edge",(s*.72,-.13,1.28),(s*.72,-.13,1.22),.116,shirt)
        palm=(s*.72,-.16,1.13)
        ball("Hands | palm",palm,(.095,.07,.115),skin,24,16)
        # fingers fan naturally downwards and slightly outward; thumb angles toward body
        for j in range(4):
            fx=palm[0]+(j-1.5)*.043
            top=(fx,palm[1]-.012,palm[2]-.035)
            end=(fx+s*(j-1.5)*.009,palm[1]-.025,palm[2]-.135-(.012 if j in (1,2) else 0))
            rod("Hands | finger",top,end,.018,skin,12)
            ball("Hands | fingertip",end,(.019,.019,.021),skin,12,8)
        rod("Hands | thumb",(palm[0]-s*.07,palm[1],palm[2]+.005),(palm[0]-s*.12,palm[1]-.025,palm[2]-.055),.026,skin,12)
    # signature lapel pin and emerald tie detail
    ball("Lapel pin | gold rim",(.39,-.378,1.83),(.052,.018,.052),gold,24,16)
    line("Tie | subtle woven stripe",[(-.045,-.397,1.55),(0,-.397,1.51),(.045,-.397,1.47)],lapel,.006)
    # studio ground, world, lighting
    floor=mat("Studio | warm neutral",(.19,.205,.22),.82)
    cube("Studio | ground",(0,0,-.035),(200,200,.06),floor,.0)
    world=bpy.context.scene.world or bpy.data.worlds.new("Studio world");bpy.context.scene.world=world
    world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.24,.27,.31,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.45
    def area(name,loc,power,size,color):
        bpy.ops.object.light_add(type="AREA",location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape="DISK";o.data.size=size;o.data.color=color
        o.rotation_euler=(Vector((0,0,1.6))-o.location).to_track_quat("-Z","Y").to_euler()
    area("Key | large softbox",(-4,-5,6),650,4.5,(1,.82,.68))
    area("Fill | cool softbox",(4,-3,3.8),480,3.5,(.72,.83,1))
    area("Rim | hair separation",(1,2,4.8),800,3,(1,.78,.52))
    scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE_NEXT" if hasattr(bpy.types,"BLENDER_EEVEE_NEXT") else "BLENDER_EEVEE"
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG";scene.render.film_transparent=False
    scene.view_settings.view_transform="AgX"
    # Keep the official photo as a non-rendering viewport reference only.
    # It is never copied to output or committed to the repository.
    ref_obj = bpy.data.objects.new("REFERENCE ONLY | official campaign portrait", None)
    ref_obj.empty_display_type = "IMAGE"
    ref_obj.hide_render = True
    ref_obj.hide_viewport = True
    ref_obj["source_url"] = "https://elazami.com/assets/hero-azami.png"
    ref_obj["reuse_rights_verified"] = False
    ref_obj.data = bpy.data.images.load(str(ref_image), check_existing=True)
    ref_obj.data.pack()
    bpy.context.collection.objects.link(ref_obj)
    # orthographic turntable views with a consistent portrait framing
    bpy.ops.object.camera_add(location=(4,-8,3.0));cam=bpy.context.object;cam.name="Studio camera"
    cam.data.type="ORTHO";cam.data.ortho_scale=3.65
    target=Vector((0,0,1.52))
    def look(loc):
        cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler();scene.camera=cam
    scene.camera.data.lens=55
    out.mkdir(parents=True,exist_ok=True)
    previews=[]
    for label,loc in [("front",(0,-8,2.45)),("three_quarter",(4,-8,2.7)),("profile",(8,-.2,2.55))]:
        look(loc);scene.render.filepath=str(out/f"{label}.png");bpy.ops.render.render(write_still=True);previews.append(f"{label}.png")
    # Save native project and export the character mesh only (exclude studio, cameras and lights)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"idriss_el_azami_reference_led.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type in {"MESH","CURVE"} and not o.name.startswith("Studio |"):
            o.select_set(True)
    bpy.context.view_layer.objects.active=next((o for o in bpy.context.scene.objects if o.select_get()),None)
    bpy.ops.export_scene.gltf(filepath=str(out/"idriss_el_azami_reference_led.glb"),export_format="GLB",use_selection=True,export_apply=True)
    manifest={"asset_id":"idriss_el_azami_el_idrissi_reference_led_v1","status":"prototype_needs_human_review_and_verified_photo_for_likeness","reference_art_direction":"Repository front, three-quarter, profile and multi-angle stylized design sheets.","repository_reference_files":[p.name for p in available_refs],"reference_files_copied_to_output":False,"real_person_likeness_verified":False,"visual_reference":"user-supplied portrait in current conversation; intentionally not copied into repository","photo_source_verified":False,"approval_status":"ready_for_visual_review_not_approved","files":["idriss_el_azami_reference_led.blend","idriss_el_azami_reference_led.glb",*previews],"checks":{"separate_hands_and_fingers":True,"glasses_frames_and_temples":True,"bald_head_reference_alignment":True,"layered_suit_shirt_tie_lapel_pin":True,"front_three_quarter_profile_renders":True},"notes":["Procedural model guided by repository front, three-quarter, profile and multi-angle stylized design references; these do not prove real-person likeness.","Repository images are stylized character/design renders. They guide shape and wardrobe but do not prove real-person likeness; photographic-source and reuse rights remain separately unverified.","Visual quality must be reviewed from the rendered PNGs before acceptance."]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("ASSET_MANIFEST="+json.dumps(manifest))
if __name__=="__main__":build(args())
