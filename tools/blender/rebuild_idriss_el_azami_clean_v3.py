"""Clean-room V3 character build. No V1/V2 mesh or script is imported.
The target is a polished, stylized caricature guided by every committed reference view.
Visual likeness remains unapproved until renders are reviewed by a human.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return Path(tail[tail.index("--output-dir")+1]) if "--output-dir" in tail else Path("build/idriss-v3")

def mat(n,c,r=.45,metal=0):
    m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*c,1); p.inputs["Roughness"].default_value=r; p.inputs["Metallic"].default_value=metal
    return m

def ell(n,loc,scale,m,rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, location=loc)
    o=bpy.context.object; o.name=n; o.scale=scale
    if rot: o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    return o

def curve(n,pts,rad,m,cyclic=False):
    c=bpy.data.curves.new(n,"CURVE"); c.dimensions="3D"; c.resolution_u=20; c.bevel_depth=rad; c.bevel_resolution=5
    s=c.splines.new("BEZIER"); s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts): p.co=co; p.handle_left_type="AUTO"; p.handle_right_type="AUTO"
    s.use_cyclic_u=cyclic
    o=bpy.data.objects.new(n,c); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def loft(n, rings, m, seg=64, sub=2):
    # (z, half width, front depth, back depth, center y)
    v=[]; f=[]
    for z,w,fd,bd,cy in rings:
        for j in range(seg):
            a=2*math.pi*j/seg; x=math.sin(a)*w; q=math.cos(a)
            y=cy-fd*q if q>=0 else cy+bd*(-q)
            v.append((x,y,z))
    for i in range(len(rings)-1):
        for j in range(seg):
            a=i*seg+j; b=i*seg+(j+1)%seg
            f.append((a,b,b+seg,a+seg))
    f += [tuple(range(seg-1,-1,-1)),tuple((len(rings)-1)*seg+j for j in range(seg))]
    me=bpy.data.meshes.new(n+" mesh"); me.from_pydata(v,[],f); me.materials.append(m); me.update()
    o=bpy.data.objects.new(n,me); bpy.context.collection.objects.link(o)
    for p in me.polygons:p.use_smooth=True
    if sub:
        mod=o.modifiers.new("Sculpt surface","SUBSURF"); mod.levels=sub; mod.render_levels=sub
    return o

def build(out):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    out.mkdir(parents=True,exist_ok=True)
    root=Path("source/parliament/references/idriss_el_azami_el_idrissi")
    refs=sorted(p.name for p in root.iterdir() if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"} and p.stat().st_size>1000)
    if len(refs)<3: raise RuntimeError("Expected the committed front, three-quarter and profile reference set")
    skin=mat("Skin | warm olive",(.47,.29,.20),.54); skin_hi=mat("Skin | soft highlights",(.53,.34,.25),.5)
    hair=mat("Hair | deep charcoal",(.085,.075,.066),.76); beard=mat("Moustache | charcoal grey",(.16,.145,.13),.85)
    suit=mat("Suit | midnight navy wool",(.018,.032,.061),.72); lapel=mat("Lapel | navy satin",(.045,.065,.10),.33)
    shirt=mat("Shirt | warm ivory",(.84,.81,.73),.47); tie=mat("Tie | muted royal blue",(.025,.07,.26),.33)
    frame=mat("Glasses | dark metal",(.09,.065,.035),.25,.65); white=mat("Eyes | ivory",(.86,.82,.73),.3)
    iris=mat("Eyes | deep brown",(.12,.055,.023),.25); black=mat("Pupils",(.008,.006,.005),.2)
    lip=mat("Mouth | natural muted rose",(.27,.12,.10),.56); gold=mat("Pin | aged gold",(.56,.34,.10),.3,.65)
    shoe=mat("Shoes | polished oxblood",(.045,.019,.018),.24)
    # Whole figure: adult proportions, restrained caricature (head 0.76 m / body 1.75 m).
    loft("Torso | tailored jacket",[(.79,.20,.17,.17,0),(.88,.27,.20,.21,0),(1.06,.30,.22,.23,0),(1.29,.34,.24,.25,0),(1.48,.39,.25,.25,0),(1.60,.43,.23,.24,0),(1.68,.38,.20,.21,0),(1.73,.22,.15,.16,0)],suit,64,2)
    for s in (-1,1):
        # shoulder centres are explicitly offset left/right, not duplicated at world origin
        ell("Shoulder | tailored cap "+str(s),(s*.355,-.005,1.59),(.205,.22,.17),suit,(0,s*-.16,0))
        curve("Sleeve | upper "+str(s),[(s*.39,0,1.59),(s*.48,-.018,1.43),(s*.51,-.04,1.28)],.093,suit)
        curve("Sleeve | forearm "+str(s),[(s*.51,-.04,1.28),(s*.535,-.075,1.14),(s*.535,-.09,1.07)],.072,suit)
        ell("Hand | palm "+str(s),(s*.535,-.105,1.015),(.062,.048,.083),skin)
        for k in range(4):
            xx=s*.535+(k-1.5)*.025
            ln=(.09,.112,.106,.082)[k]
            curve("Finger %d %d"%(s,k),[(xx,-.13,.98),(xx+s*(k-1.5)*.004,-.14,.98-ln)],.010,skin)
        curve("Thumb "+str(s),[(s*.49,-.11,1.035),(s*.46,-.135,1.005),(s*.46,-.14,.97)],.014,skin)
        # legs have separate real offsets and controlled taper
        x=s*.155
        loft("Trousers | leg "+str(s),[(.12,.09,.105,.11,0),(.19,.102,.12,.12,0),(.43,.115,.13,.13,0),(.68,.13,.15,.15,0),(.88,.135,.15,.15,0),(.98,.125,.14,.14,0)],suit,40,1).location.x=x
        curve("Trouser crease "+str(s),[(x,-.12,.23),(x,-.14,.49),(x,-.13,.77)],.0035,lapel)
        ell("Shoe "+str(s),(x,-.115,.085),(.125,.235,.075),shoe)
    # Collar, tie and lapels form layered, readable tailoring.
    ell("Shirt front",(0,-.225,1.51),(.145,.035,.22),shirt)
    for s in (-1,1):
        # triangular collar leaf
        ob=bpy.data.meshes.new("Collar leaf mesh"); verts=[(s*.025,-.27,1.69),(s*.13,-.27,1.67),(s*.07,-.31,1.52)]
        ob.from_pydata(verts,[],[(0,1,2)]); ob.materials.append(shirt); obj=bpy.data.objects.new("Collar leaf "+str(s),ob); bpy.context.collection.objects.link(obj)
        curve("Lapel contour "+str(s),[(s*.045,-.263,1.70),(s*.19,-.278,1.55),(s*.29,-.25,1.40)],.022,lapel)
    ell("Tie knot",(0,-.285,1.675),(.045,.025,.048),tie)
    mesh=bpy.data.meshes.new("Tie blade mesh")
    mesh.from_pydata([(-.045,-.275,1.64),(.045,-.275,1.64),(.078,-.26,1.36),(0,-.29,1.32),(-.078,-.26,1.36)],[],[(0,1,2,3,4)]); mesh.materials.append(tie)
    o=bpy.data.objects.new("Tie blade",mesh); bpy.context.collection.objects.link(o)
    ell("Lapel pin",(s*.28,-.28,1.55),(.018,.012,.018),gold)
    # Head: narrowed lower jaw, broad cheekbone zone, compact forehead; no oversized egg.
    loft("Head | clean-room craniofacial base",[(2.02,.105,.14,.15,0),(2.055,.145,.18,.19,0),(2.10,.19,.22,.24,0),(2.16,.235,.255,.27,0),(2.23,.27,.275,.295,0),(2.31,.292,.29,.31,0),(2.40,.30,.29,.31,0),(2.49,.292,.28,.30,0),(2.57,.27,.26,.28,0),(2.64,.235,.23,.25,0),(2.70,.17,.18,.20,0),(2.735,.07,.08,.09,0),(2.74,.008,.01,.01,0)],skin,80,2)
    # Hair cap and sideburns follow skull silhouette.
    ell("Hair cap",(0,.012,2.665),(.275,.285,.105),hair)
    for s in (-1,1):
        ell("Sideburn "+str(s),(s*.278,-.008,2.49),(.035,.075,.105),hair)
        ell("Ear "+str(s),(s*.292,-.004,2.405),(.045,.065,.085),skin)
        ell("Ear inner "+str(s),(s*.32,-.045,2.407),(.014,.027,.044),skin_hi)
        x=s*.119
        ell("Eye socket "+str(s),(x,-.273,2.477),(.076,.024,.042),skin)
        ell("Sclera "+str(s),(x,-.294,2.477),(.051,.014,.027),white)
        ell("Iris "+str(s),(x+.003,-.306,2.476),(.017,.007,.019),iris)
        ell("Pupil "+str(s),(x+.004,-.312,2.476),(.008,.004,.010),black)
        curve("Upper eyelid "+str(s),[(x-.055,-.299,2.485),(x,-.31,2.505),(x+.055,-.299,2.485)],.006,skin_hi)
        curve("Eyebrow "+str(s),[(x-.068,-.285,2.526),(x,-.302,2.54),(x+.061,-.285,2.526)],.012,hair)
        # glasses rims have rounded corners and align to the face plane
        x0,x1=x-.071,x+.071; z0,z1=2.445,2.515
        curve("Glasses rim "+str(s),[(x0,-.316,z0),(x0,-.316,z1),(x1,-.316,z1),(x1,-.316,z0),(x0,-.316,z0)],.0055,frame,True)
        curve("Glasses temple "+str(s),[(s*.19,-.306,2.508),(s*.25,-.22,2.505),(s*.29,-.06,2.49)],.005,frame)
        ell("Moustache lobe "+str(s),(s*.042,-.302,2.276),(.047,.023,.015),beard)
    curve("Glasses bridge",[(-.048,-.317,2.503),(0,-.326,2.508),(.048,-.317,2.503)],.005,frame)
    # Face profile: a continuous bridge and defined nose tip, not a detached oversized sphere.
    loft("Nose bridge",[(2.315,.018,.022,.018,-.30),(2.35,.027,.045,.02,-.315),(2.405,.028,.04,.02,-.30),(2.445,.022,.022,.02,-.28)],skin_hi,32,1)
    ell("Nose tip",(0,-.35,2.337),(.036,.036,.026),skin_hi)
    for s in (-1,1): ell("Nostril wing "+str(s),(s*.028,-.332,2.33),(.019,.02,.013),skin)
    curve("Upper lip",[(-.061,-.275,2.276),(-.027,-.299,2.281),(0,-.305,2.273),(.027,-.299,2.281),(.061,-.275,2.276)],.006,lip)
    curve("Lower lip",[(-.045,-.281,2.257),(0,-.297,2.252),(.045,-.281,2.257)],.006,skin_hi)
    # neck is short and seated inside the jacket collar
    loft("Neck | integrated",[(1.67,.085,.10,.10,0),(1.78,.09,.105,.11,0),(1.94,.105,.115,.12,0),(2.06,.11,.12,.13,0)],skin,48,1)
    # Studio floor and camera views.
    floor=mat("Backdrop | warm charcoal",(.055,.062,.073),.9)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005)); bpy.context.object.name="Studio floor"; bpy.context.object.data.materials.append(floor)
    world=bpy.data.worlds.new("Neutral studio"); world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.12,.14,.17,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.4; bpy.context.scene.world=world
    def light(name,loc,power,size,color):
        bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size; l.data.color=color
        l.rotation_euler=(Vector((0,0,1.45))-l.location).to_track_quat("-Z","Y").to_euler()
    light("Key softbox",(-3.2,-4.5,4.2),500,3.5,(1,.82,.69)); light("Fill softbox",(3,-3,3.0),300,3,(.74,.83,1)); light("Rim softbox",(1.5,2,3.8),600,2.8,(1,.78,.57))
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE_NEXT" if hasattr(bpy.types,"BLENDER_EEVEE_NEXT") else "BLENDER_EEVEE"
    scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.view_settings.view_transform="AgX"
    bpy.ops.object.camera_add(location=(0,-8,2.0)); cam=bpy.context.object; cam.name="Review camera"; cam.data.type="ORTHO"; cam.data.ortho_scale=3.05; scene.camera=cam
    target=Vector((0,0,1.37)); views=[("front",(0,-8,2.0)),("three_quarter",(3.0,-8,2.15)),("profile",(8,0,2.0))]
    for name,loc in views:
        cam.location=loc; cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler(); scene.render.filepath=str(out/(name+".png")); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"idriss_el_azami_clean_v3.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH","CURVE"} and obj.name!="Studio floor": obj.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.name.startswith("Head |"))
    bpy.ops.export_scene.gltf(filepath=str(out/"idriss_el_azami_clean_v3.glb"),export_format="GLB",use_selection=True)
    manifest={"asset_id":"idriss_el_azami_clean_v3","rebuild":"clean-room; no previous character scene, mesh, or generator imported","reference_files":refs,"likeness_verified":False,"approval_status":"awaiting_actual_render_review","files":["idriss_el_azami_clean_v3.blend","idriss_el_azami_clean_v3.glb","front.png","three_quarter.png","profile.png"],"notices":["A successful export does not prove visual likeness.","The rendered views require actual inspection before acceptance."]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
    print("CLEAN_V3_MANIFEST="+json.dumps(manifest))
if __name__=="__main__": build(args())
