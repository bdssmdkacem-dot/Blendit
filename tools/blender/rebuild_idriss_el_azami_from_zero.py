"""Independent from-zero rebuild for the Idriss El Azami character.
Creates a fresh Blender scene and a new continuous head/body base; does not import
or modify the previous generated asset. Stylized likeness remains unverified until
human review of the rendered evidence.
Run: blender --background --python tools/blender/rebuild_idriss_el_azami_from_zero.py -- --output-dir build/idriss-el-azami-v2
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

def arguments():
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(a[a.index("--output-dir")+1]) if "--output-dir" in a else Path("build/idriss-el-azami-v2")
    refs=Path("source/parliament/references/idriss_el_azami_el_idrissi")
    return out,refs

def material(name,color,rough=.45,metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1); p.inputs["Roughness"].default_value=rough; p.inputs["Metallic"].default_value=metal
    return m

def mesh_object(name,verts,faces,mat,smooth=True):
    me=bpy.data.meshes.new(name+" topology"); me.from_pydata(verts,[],faces); me.materials.append(mat); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    return ob

def uv(name,loc,scale,mat,segments=40,rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def tube(name,points,radius,mat):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D";c.resolution_u=16;c.bevel_depth=radius;c.bevel_resolution=4
    sp=c.splines.new("BEZIER");sp.bezier_points.add(len(points)-1)
    for bp,co in zip(sp.bezier_points,points):bp.co=co;bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o

def loft(name,rings,mat,segments=64,subdiv=1):
    # ring tuple: z, half-width, front-depth, rear-depth, center-y
    vs=[];fs=[]
    for z,w,fd,bd,cy in rings:
        for j in range(segments):
            a=2*math.pi*j/segments; sx=math.sin(a); cx=math.cos(a)
            y=cy-fd*cx if cx>=0 else cy+bd*(-cx)
            vs.append((w*sx,y,z))
    for i in range(len(rings)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments
            fs.append((a,b,b+segments,a+segments))
    fs.extend([tuple(range(segments-1,-1,-1)),tuple((len(rings)-1)*segments+j for j in range(segments))])
    ob=mesh_object(name,vs,fs,mat)
    if subdiv:
        s=ob.modifiers.new("Surface refinement","SUBSURF");s.levels=subdiv;s.render_levels=subdiv
    return ob

def build(out,refs):
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        pass
    out.mkdir(parents=True,exist_ok=True)
    refs_found=sorted(p for p in refs.glob("*") if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png",".webp"} and p.stat().st_size>1000)
    if not refs_found: raise RuntimeError("No design reference files found: "+str(refs))
    skin=material("Skin | olive warm neutral",(.48,.30,.205),.57)
    skinlight=material("Skin | subtle highlights",(.55,.36,.26),.58)
    hair=material("Hair | charcoal",(.12,.105,.09),.7)
    beard=material("Facial hair | charcoal grey",(.18,.17,.15),.82)
    suit=material("Suit | deep navy wool",(.025,.045,.08),.62)
    lapel=material("Suit | satin lapel",(.055,.075,.11),.32)
    shirt=material("Shirt | ivory",(.82,.80,.74),.5)
    tie=material("Tie | cobalt blue",(.025,.09,.34),.35)
    metal=material("Eyeglass frames | dark bronze",(.075,.055,.035),.25,.55)
    eye_white=material("Eyes | ivory",(.86,.82,.73),.3)
    iris=material("Eyes | brown iris",(.16,.085,.035),.28)
    pupil=material("Eyes | pupils",(.012,.009,.007),.2)
    mouth=material("Lips | muted rose brown",(.24,.10,.08),.55)
    gold=material("Pin | brushed gold",(.65,.39,.1),.28,.7)
    sole=material("Shoes | dark oxblood",(.045,.022,.02),.25)
    # New body proportions are modeled directly in this file; no previous asset is loaded.
    loft("Body | continuous tailored silhouette",[
      (.82,.22,.18,.18,0),(.94,.30,.22,.23,0),(1.12,.31,.23,.24,0),
      (1.34,.36,.25,.25,0),(1.55,.43,.27,.27,0),(1.69,.48,.26,.26,0),
      (1.78,.40,.23,.23,0),(1.84,.20,.18,.18,0)],suit,48,2)
    # Shoulder slope and upper arms use tapered lofts rather than oversized spheres.
    for s in (-1,1):
        loft("Jacket | shaped shoulder "+str(s),[
          (1.60,.30,.24,.23,0),(1.68,.38,.25,.24,0),(1.73,.43,.23,.22,0),(1.77,.34,.20,.20,0)],suit,40,1)
        # fitted legs, tapered from thigh to ankle
        x=s*.19
        loft("Trousers | tailored leg "+str(s),[
          (.13,.105,.12,.12,0),(.22,.115,.13,.13,0),(.48,.13,.15,.15,0),
          (.72,.15,.17,.17,0),(.94,.145,.16,.16,0),(1.04,.14,.15,.15,0)],suit,32,1).location.x=x
        uv("Shoes | shaped toe "+str(s),(x,-.12,.105),(.14,.27,.095),sole)
        # cuff and crease are understated, aligned to the leg
        tube("Trouser | pressed crease "+str(s),[(x,-.145,.27),(x,-.17,.54),(x,-.15,.82)],.004,lapel)
        # arms with narrower forearms and visible wrists
        tube("Sleeve | upper arm "+str(s),[(s*.36,0,1.70),(s*.49,-.005,1.52),(s*.52,-.04,1.34)],.105,suit)
        tube("Sleeve | forearm "+str(s),[(s*.52,-.04,1.34),(s*.55,-.08,1.18),(s*.55,-.10,1.08)],.082,suit)
        uv("Hand | palm "+str(s),(s*.55,-.11,1.015),(.068,.052,.095),skin)
        # anatomically separated fingers with graduated lengths, attached at palm
        for j in range(4):
            xx=s*.55+(j-1.5)*.027
            length=(.105,.13,.125,.095)[j]
            tube("Hand | finger %d %d"%(s,j),[(xx,-.13,.98),(xx+s*(j-1.5)*.006,-.14,.98-length)],.012,skin)
        tube("Hand | thumb "+str(s),[(s*.49,-.12,1.03),(s*.46,-.145,.99),(s*.46,-.15,.96)],.016,skin)
    # Shirt bib and collar are tailored panels rather than cubes
    uv("Shirt | front bib",(0,-.255,1.60),(.17,.035,.25),shirt)
    for s in (-1,1):
        loft("Shirt | collar panel "+str(s),[(1.75,.055,.03,.025,-.275),(1.84,.075,.025,.025,-.275)],shirt,24,0).location.x=s*.075
        tube("Lapel | sculpted edge "+str(s),[(s*.055,-.29,1.80),(s*.20,-.30,1.66),(s*.31,-.28,1.52)],.025,lapel)
    uv("Tie | knot",(0,-.302,1.78),(.055,.028,.055),tie)
    mesh_object("Tie | tapered blade",[(-.05,-.295,1.74),(.05,-.295,1.74),(.09,-.29,1.40),(0,-.30,1.36),(-.09,-.29,1.40)],[(0,1,2,3,4)],tie,False)
    # New craniofacial base: bespoke ring profile, jaw and forehead taper with higher density.
    head=loft("HEAD V2 | new continuous craniofacial sculpt",[
      (2.12,.105,.17,.18,-.005),(2.15,.15,.22,.23,-.004),(2.19,.205,.26,.28,0),
      (2.24,.25,.29,.31,0),(2.30,.285,.31,.34,0),(2.37,.315,.325,.35,0),
      (2.45,.335,.33,.355,0),(2.53,.34,.325,.35,.004),(2.61,.325,.31,.335,.008),
      (2.68,.295,.285,.31,.012),(2.74,.245,.24,.27,.015),(2.785,.16,.16,.18,.015),
      (2.80,.015,.015,.015,.015)],skin,64,2)
    # Nose bridge, tip and alae sit on the new face plane with restrained scale.
    uv("Nose | bridge",(0,-.325,2.405),(.041,.047,.103),skin,32,20)
    uv("Nose | tip",(0,-.365,2.355),(.047,.041,.034),skinlight,32,20)
    for s in (-1,1):
        uv("Nose | ala "+str(s),(s*.035,-.355,2.352),(.024,.022,.018),skin,24,16)
        # ears follow head height and are smaller than previous generation
        uv("Ear | outer "+str(s),(s*.335,-.005,2.455),(.052,.075,.105),skin)
        uv("Ear | concha "+str(s),(s*.36,-.058,2.455),(.022,.027,.055),skinlight,24,16)
        # eye sockets are darker recesses; sclera and iris are small and embedded
        x=s*.132
        uv("Eye | socket "+str(s),(x,-.306,2.495),(.083,.023,.048),skin,32,20)
        uv("Eye | sclera "+str(s),(x,-.326,2.495),(.055,.018,.031),eye_white,32,20)
        uv("Eye | iris "+str(s),(x+.004,-.341,2.493),(.019,.008,.021),iris,24,16)
        uv("Eye | pupil "+str(s),(x+.005,-.348,2.493),(.009,.005,.012),pupil,20,12)
        tube("Brow | shaped "+str(s),[(x-.075,-.325,2.55),(x,-.342,2.566),(x+.067,-.32,2.552)],.013,hair)
        # glasses frame rectangles sized around the eyes, curved polyline
        x0,x1=x-.083,x+.083;z0,z1=2.455,2.535
        tube("Glasses | rim "+str(s),[(x0,-.351,z0),(x0,-.351,z1),(x1,-.351,z1),(x1,-.351,z0),(x0,-.351,z0)],.006,metal)
        tube("Glasses | temple "+str(s),[(s*.215,-.34,2.525),(s*.28,-.23,2.525),(s*.34,-.07,2.51)],.006,metal)
        # moustache shaped to the lip line; no floating beard clumps
        uv("Moustache | lobe "+str(s),(s*.046,-.348,2.285),(.052,.025,.017),beard,32,16)
    tube("Glasses | bridge",[(-.05,-.353,2.52),(.05,-.353,2.52)],.006,metal)
    tube("Mouth | upper lip",[(-.075,-.302,2.286),(-.035,-.33,2.29),(0,-.334,2.278),(.035,-.33,2.29),(.075,-.302,2.286)],.008,mouth)
    tube("Mouth | lower lip",[(-.05,-.307,2.263),(0,-.327,2.257),(.05,-.307,2.263)],.007,skinlight)
    # subtle lower-face shading is integrated into material and lighting, not detached beard beads.
    uv("Lapel | gold pin",(.30,-.302,1.68),(.025,.012,.025),gold,24,16)
    # head/neck transition; neck is partially hidden by collar and chin
    loft("Neck | shaped transition",[(1.78,.105,.12,.12,0),(1.90,.115,.13,.13,0),(2.18,.12,.13,.14,0)],skin,40,1)
    # Studio scene
    floor=material("Studio | graphite",(.075,.085,.10),.85)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));bpy.context.object.name="Studio | floor";bpy.context.object.data.materials.append(floor)
    world=bpy.data.worlds.new("Studio | neutral world");world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.15,.17,.20,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35;bpy.context.scene.world=world
    def area(name,loc,power,size,color):
        bpy.ops.object.light_add(type="AREA",location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape="DISK";o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat("-Z","Y").to_euler()
    area("Studio | key",(-3.5,-4.5,5.0),520,4.0,(1,.83,.70));area("Studio | fill",(3,-3,3.5),360,3.5,(.72,.82,1));area("Studio | rim",(1,2,4),620,3,(1,.78,.57))
    scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE_NEXT" if hasattr(bpy.types,"BLENDER_EEVEE_NEXT") else "BLENDER_EEVEE";scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.view_settings.view_transform="AgX"
    bpy.ops.object.camera_add(location=(0,-8,2.45));cam=bpy.context.object;cam.name="Studio | camera";cam.data.type="ORTHO";cam.data.ortho_scale=3.12;scene.camera=cam
    target=Vector((0,0,1.47))
    def aim(loc):cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    previews=[]
    for label,loc in [("front",(0,-8,2.45)),("three_quarter",(3.4,-8,2.6)),("profile",(8,0,2.5))]:
        aim(loc);scene.render.filepath=str(out/(label+".png"));bpy.ops.render.render(write_still=True);previews.append(label+".png")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"idriss_el_azami_v2_from_zero.blend"))
    # Export only newly generated character geometry, excluding studio objects.
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type in {"MESH","CURVE"} and not o.name.startswith(("Studio |","Studio | floor")):
            o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.name.startswith("HEAD V2"))
    bpy.ops.export_scene.gltf(filepath=str(out/"idriss_el_azami_v2_from_zero.glb"),export_format="GLB",use_selection=True)
    manifest={"asset_id":"idriss_el_azami_v2_from_zero","construction":"independent new scene and newly authored geometry; previous asset not imported or edited","reference_files":[p.name for p in refs_found],"files":["idriss_el_azami_v2_from_zero.blend","idriss_el_azami_v2_from_zero.glb",*previews],"likeness_verified":False,"approval_status":"awaiting_actual_render_review","notes":["New build is isolated from the prior asset script.","Rendered evidence must be inspected before visual acceptance.","This procedural sculpt is a fresh base, not a claim of verified photographic likeness."]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("V2_MANIFEST="+json.dumps(manifest))
if __name__=="__main__":build(*arguments())
