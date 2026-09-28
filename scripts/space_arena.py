# Starfall Dash — Space Arena
# Blender 3.x / 4.x
# Run: Blender -> Scripting -> New -> paste this file -> Run Script.
# The script builds a standalone cinematic prototype and does not touch the game repo.

import bpy, math, random
from mathutils import Vector

random.seed(7)

# ---------- reset ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
    pass

# ---------- helpers ----------
def mat(name, color, emission=None, strength=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=.35
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1)
        bs.inputs['Emission Strength'].default_value=strength
    return m

SPACE=mat('Space',(0.003,0.006,0.018))
CUBE=mat('Hero_Cube',(0.08,0.55,1.0),(.03,.35,1),5)
CUBE2=mat('Hero_Core',(0.7,0.9,1),(.2,.7,1),8)
ENEMY=mat('Enemy',(0.65,0.08,0.9),(.4,.02,.8),4)
CRYSTAL=mat('Core_Crystal',(0.05,0.9,1),(.02,.8,1),12)
PLANET=mat('Planet',(0.05,0.12,0.24),(.01,.03,.08),0)
RING=mat('Planet_Ring',(.2,.55,1),(.1,.3,1),3)
AST=mat('Asteroid',(.12,.14,.2))
COMET=mat('Comet',(.4,.8,1),(.2,.7,1),8)

def smooth(obj):
    if obj.type=='MESH':
        for p in obj.data.polygons: p.use_smooth=True

def cube(name, loc, scale, material, bevel=.12):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Soft_Edges','BEVEL'); b.width=bevel; b.segments=3
    o.data.materials.append(material)
    return o

def ico(name, loc, scale, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=scale, location=loc)
    o=bpy.context.object; o.name=name; o.data.materials.append(material); smooth(o); return o

def uv(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material); smooth(o); return o

def curve_line(name, points, material, bevel=.025):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=bevel; c.bevel_resolution=3
    s=c.splines.new('BEZIER'); s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points): p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material); return o

# ---------- world ----------
world=bpy.data.worlds.new('Starfall Space') if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.001,0.003,0.012,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.08

# stars
for i in range(180):
    p=(random.uniform(-18,18),random.uniform(-10,10),random.uniform(-8,10))
    uv('Star',p,random.uniform(.012,.035),CUBE2)

# ---------- planet + ring ----------
planet=uv('Planet_Arena',(5.2,2.2,0.2),2.2,PLANET)
bpy.ops.mesh.primitive_torus_add(major_radius=3.0,minor_radius=.045,major_segments=96,location=(5.2,2.2,0.2),rotation=(math.radians(67),0,math.radians(18)))
ring=bpy.context.object; ring.name='Planet_Ring'; ring.data.materials.append(RING)

# ---------- asteroids ----------
for i in range(14):
    a=random.uniform(0,math.tau); r=random.uniform(5.5,11)
    loc=(math.cos(a)*r, math.sin(a)*r*.55, random.uniform(-2,2))
    o=ico('Asteroid',loc,random.uniform(.22,.65),AST,2)
    o.rotation_euler=[random.random()*math.tau for _ in range(3)]

# ---------- hero ----------
hero=cube('PLAYER_CUBE',(-5.2,0,0),(0.65,0.65,0.65),CUBE,.16)
# small glowing inner core
core=ico('Player_Core',(-5.2,0,0),.28,CUBE2,2); core.parent=hero

# ---------- enemies ----------
for idx,loc in enumerate([(-1.5,2.5,0),(-.5,-3,0),(2.3,-1.3,0)]):
    e=ico(f'Enemy_{idx+1}',loc,.62,ENEMY,2)
    e.rotation_euler=(.3*idx,.6,idx)
    # horns/spikes
    for j in range(4):
        ang=j*math.tau/4
        tip=Vector(loc)+Vector((math.cos(ang)*.95,math.sin(ang)*.95,0))
        curve_line(f'Enemy_{idx+1}_Spike', [Vector(loc),tip], ENEMY,.055)

# ---------- core crystal ----------
cr=ico('COSMIC_CORE_CRYSTAL',(0,.4,0),.55,CRYSTAL,2)
cr.scale=(.75,1.35,.75)
cr.rotation_euler=(0,.25,math.radians(15))

# crystal aura
for r in (.75,1.0,1.25):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.012,major_segments=64,location=(0,.4,0),rotation=(math.radians(65),0,math.radians(r*30)))
    bpy.context.object.data.materials.append(CRYSTAL)

# ---------- comets ----------
for idx,(start,end) in enumerate([
    (Vector((-11,7,0)),Vector((8,-1,0))),
    (Vector((10,7,1)),Vector((-5,-5,1)))
]):
    tail=[]
    for k in range(9):
        t=k/8; tail.append(start.lerp(end,t))
    curve_line(f'Comet_{idx+1}_Tail',tail,COMET,.055)
    head=ico(f'Comet_{idx+1}',start,.18,COMET,2)
    head.keyframe_insert('location',frame=1)
    head.location=end; head.keyframe_insert('location',frame=180)

# ---------- hero animation ----------
hero.location=(-5.2,0,0); hero.keyframe_insert('location',frame=1)
hero.location=(-1.5,0.8,0); hero.keyframe_insert('location',frame=90)
hero.location=(0,0.4,0); hero.keyframe_insert('location',frame=180)
for fc in hero.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation='BEZIER'

# ---------- camera ----------
bpy.ops.object.camera_add(location=(0,-13,12),rotation=(math.radians(40),0,0))
cam=bpy.context.object; cam.name='Cinematic_Camera'
bpy.context.scene.camera=cam
# point camera toward arena
def look_at(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
look_at(cam,(0,0,0))
cam.keyframe_insert('location',frame=1); cam.keyframe_insert('rotation_euler',frame=1)
cam.location=(0,-11,8); look_at(cam,(0,0,0)); cam.keyframe_insert('location',frame=180); cam.keyframe_insert('rotation_euler',frame=180)

# ---------- lighting ----------
bpy.ops.object.light_add(type='AREA',location=(-3,-2,6))
key=bpy.context.object; key.name='Key_Light'; key.data.energy=900; key.data.shape='DISK'; key.data.size=8
look_at(key,(0,0,0))
bpy.ops.object.light_add(type='POINT',location=(0,.4,3))
bpy.context.object.data.energy=500; bpy.context.object.data.color=(.1,.6,1)

# ---------- render ----------
scene=bpy.context.scene
scene.frame_start=1; scene.frame_end=180; scene.render.fps=30
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath='//renders/space_arena_test.png'
scene.render.film_transparent=False

# compositor glow
scene.use_nodes=True
nt=scene.node_tree; nt.nodes.clear()
rl=nt.nodes.new('CompositorNodeRLayers')
gl=nt.nodes.new('CompositorNodeGlare'); gl.glare_type='FOG_GLOW'; gl.quality='HIGH'; gl.threshold=.4; gl.size=7
comp=nt.nodes.new('CompositorNodeComposite')
nt.links.new(rl.outputs['Image'],gl.inputs['Image']); nt.links.new(gl.outputs['Image'],comp.inputs['Image'])

# organize
for obj in bpy.context.scene.objects:
    if obj.name.startswith('Star'):
        obj.hide_render=False

# save
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath('//Starfall_Dash_Space_Arena.blend'))
print('Starfall Dash Space Arena created. Press Play or render frames 1-180.')
