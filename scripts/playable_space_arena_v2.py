# Starfall Dash — Playable Space Arena v2
# Run scripts/space_arena.py first, then run this script.
# Blender 3.x / 4.x

import bpy, math, time
from mathutils import Vector

scene = bpy.context.scene
hero = bpy.data.objects.get("PLAYER_CUBE")
if not hero:
    raise RuntimeError("Run scripts/space_arena.py first.")

# Stop cinematic animation.
hero.animation_data_clear()
# Keep the inner core attached to the cube at the correct local position.
core = bpy.data.objects.get("Player_Core")
if core:
    core.parent = hero
    core.location = (0, 0, 0)

# Clean previous gameplay objects.
for o in list(scene.objects):
    if o.name.startswith(("GAME_", "DROP_CRYSTAL_", "ABILITY_")):
        bpy.data.objects.remove(o, do_unlink=True)

# Materials.
def material(name, color, emission, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Emission Color"].default_value = (*emission, 1)
    bs.inputs["Emission Strength"].default_value = strength
    return m

CRYSTAL = material("Gameplay_Crystal", (.03,.8,1), (.02,.8,1), 14)
PULSE = material("Gameplay_Pulse", (.1,.5,1), (.05,.5,1), 12)
UI = material("Gameplay_UI", (.3,.9,1), (.1,.7,1), 8)

# Constants.
SPEED = 6.5
ABILITY_RANGE = 2.25
ABILITY_COOLDOWN = .65
MAX_HP = 5
DAMAGE_COOLDOWN = 1.0
CRYSTALS_PER_STAGE = 3
STAGES = 3
BOUNDS = (-8, 8, -5.5, 5.5)
STAGE_LAYOUTS = {1:[(-1.5,2.5,0),(-.5,-3,0),(2.3,-1.3,0)],2:[(-2.5,3.5,0),(1,3,0),(3.5,-2.5,0),(-3.5,-2,0)],3:[(-5.5,4.2,0),(-1.8,4.5,0),(2,4.3,0),(5.5,3.8,0),(0,-3.8,0)]}

state = {
    "hp": MAX_HP, "crystals": 0, "stage": 1, "alive": True, "won": False, "transition": False, "transition_until": 0.0,
    "last_attack": -99.0, "invuln": 0.0, "keys": set(),
    "enemies": [], "drops": [], "pulse": None
}

# Remove decorative center crystal from the cinematic scene.
for o in list(scene.objects):
    if o.name.startswith("COSMIC_CORE_CRYSTAL"):
        bpy.data.objects.remove(o, do_unlink=True)

enemy_positions = [(-1.5,2.5,0), (-.5,-3,0), (2.3,-1.3,0)]

# Find the three existing enemies.
for i in range(1, 4):
    e = bpy.data.objects.get(f"Enemy_{i}")
    if e:
        e.location = enemy_positions[i-1]
        e.hide_viewport = False
        e.hide_render = False
        state["enemies"].append(e)

def dist(a,b):
    return math.hypot(a.x-b.x, a.y-b.y)

def make_crystal(loc, number):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.38, location=loc)
    c = bpy.context.object
    c.name = f"DROP_CRYSTAL_{number}"
    c.scale = (.65,1.25,.65)
    c.data.materials.append(CRYSTAL)
    for p in c.data.polygons:
        p.use_smooth = True
    bpy.ops.mesh.primitive_torus_add(
        major_radius=.62, minor_radius=.018, major_segments=32,
        location=loc, rotation=(math.radians(65),0,.4))
    aura = bpy.context.object
    aura.name = f"DROP_CRYSTAL_{number}_AURA"
    aura.data.materials.append(CRYSTAL)
    return c

def make_text(name, body, loc, size):
    bpy.ops.object.text_add(location=loc)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.align_x = "CENTER"
    t.data.size = size
    t.data.materials.append(UI)
    return t

hud = make_text("GAME_HUD", "", (0,5.0,.5), .38)

def update_hud():
    hud.data.body = f"STARFALL DASH   |   STAGE {state['stage']}/{STAGES}   |   HP {state['hp']}/{MAX_HP}   |   CRYSTALS {state['crystals']}/{CRYSTALS_PER_STAGE}"

def message(body):
    for name in ("GAME_MESSAGE","GAME_OVER","GAME_WIN"):
        o=bpy.data.objects.get(name)
        if o: bpy.data.objects.remove(o,do_unlink=True)
    return make_text("GAME_MESSAGE",body,(0,0,.6),.65)

def spawn_stage():
    for e in list(state["enemies"]):
        e.hide_viewport = True
        e.hide_render = True
    state["enemies"].clear()
    for c in list(state["drops"]):
        aura=bpy.data.objects.get(c.name+"_AURA")
        if c.name in scene.objects: bpy.data.objects.remove(c, do_unlink=True)
        if aura: bpy.data.objects.remove(aura, do_unlink=True)
    state["drops"].clear()
    state["crystals"]=0
    for i,loc in enumerate(STAGE_LAYOUTS[state["stage"]],1):
        e=bpy.data.objects.get(f"Enemy_{i}")
        if not e:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.62,location=loc)
            e=bpy.context.object
            e.name=f"Enemy_{i}"
            m=bpy.data.materials.get("Enemy")
            if m: e.data.materials.append(m)
        e.location=loc
        e.hide_viewport=False
        e.hide_render=False
    update_hud()

def kill_enemy(enemy):
    if enemy not in state["enemies"]:
        return
    pos=enemy.location.copy()
    enemy.hide_viewport=True
    enemy.hide_render=True
    for o in scene.objects:
        if o.name.startswith(enemy.name+"_Spike"):
            o.hide_viewport=True
            o.hide_render=True
    state["enemies"].remove(enemy)
    state["drops"].append(make_crystal((pos.x,pos.y,.25),len(state["drops"])+1))

def attack(now):
    if not state["alive"] or state["won"] or now-state["last_attack"] < ABILITY_COOLDOWN:
        return
    state["last_attack"]=now
    bpy.ops.mesh.primitive_torus_add(
        major_radius=.25, minor_radius=.055, major_segments=48,
        location=hero.location)
    pulse=bpy.context.object
    pulse.name="ABILITY_PULSE"
    pulse.data.materials.append(PULSE)
    pulse["created"]=now
    state["pulse"]=pulse

    for enemy in list(state["enemies"]):
        if dist(hero,enemy) <= ABILITY_RANGE:
            kill_enemy(enemy)

def damage(now):
    if now < state["invuln"]:
        return
    state["hp"]-=1
    state["invuln"]=now+DAMAGE_COOLDOWN
    update_hud()
    if state["hp"]<=0:
        state["alive"]=False
        message("DESTROYED   —   press R to restart")

def collect():
    for c in list(state["drops"]):
        if not c.hide_viewport and dist(hero,c)<.95:
            state["crystals"]+=1
            c.hide_viewport=True
            c.hide_render=True
            aura=bpy.data.objects.get(c.name+"_AURA")
            if aura:
                aura.hide_viewport=True
                aura.hide_render=True
            update_hud()
            if state["crystals"]>=CRYSTALS_PER_STAGE:
                if state["stage"] < STAGES:
                    state["transition"] = True
                    state["transition_until"] = time.monotonic() + 1.2
                    state["stage"] += 1
                    message("STAGE COMPLETE   —   NEXT STAGE")
                else:
                    state["won"] = True
                    message("COSMIC CORE RESTORED   —   YOU WIN!")

def reset():
    for o in list(scene.objects):
        if o.name.startswith(("DROP_CRYSTAL_","GAME_MESSAGE","GAME_OVER","GAME_WIN","ABILITY_")):
            bpy.data.objects.remove(o,do_unlink=True)
    state.update({"hp":MAX_HP,"crystals":0,"stage":1,"alive":True,"won":False,"transition":False,"transition_until":0.0,
                  "last_attack":-99.0,"invuln":0.0,"keys":set(),
                  "enemies":[],"drops":[],"pulse":None})
    hero.location=(-5.2,0,0)
    hero.hide_viewport=False
    hero.hide_render=False
    for i in range(1,4):
        e=bpy.data.objects.get(f"Enemy_{i}")
        if e:
            e.location=enemy_positions[i-1]
            e.hide_viewport=False
            e.hide_render=False
            state["enemies"].append(e)
            for o in scene.objects:
                if o.name.startswith(e.name+"_Spike"):
                    o.hide_viewport=False
                    o.hide_render=False
    update_hud()

class STARFALL_OT_PLAY(bpy.types.Operator):
    bl_idname="starfall.play_v2"
    bl_label="Starfall Dash Playable Prototype"
    timer=None
    last=0

    def execute(self,context):
        self.last=time.monotonic()
        self.timer=context.window_manager.event_timer_add(.016,window=context.window)
        context.window_manager.modal_handler_add(self)
        print("STARFALL DASH PROTOTYPE: WASD/Arrows move, SPACE attack, R restart, ESC stop")
        return {"RUNNING_MODAL"}

    def modal(self,context,event):
        now=time.monotonic()
        if event.type=="ESC" and event.value=="PRESS":
            return self.cancel(context)
        keymap={"W":"UP","UP_ARROW":"UP","S":"DOWN","DOWN_ARROW":"DOWN",
                "A":"LEFT","LEFT_ARROW":"LEFT","D":"RIGHT","RIGHT_ARROW":"RIGHT"}
        if event.type in keymap:
            k=keymap[event.type]
            if event.value=="PRESS": state["keys"].add(k)
            elif event.value=="RELEASE": state["keys"].discard(k)
        if event.type=="SPACE" and event.value=="PRESS":
            attack(now)
        if event.type=="R" and event.value=="PRESS" and (not state["alive"] or state["won"]):
            reset()

        if event.type=="TIMER":
            dt=min(max(now-self.last,0),.05)
            self.last=now

            if state["transition"] and now >= state["transition_until"]:
                state["transition"] = False
                hero.location=(-5.2,0,0)
                spawn_stage()
                message("NEW STAGE — COLLECT 3 CRYSTALS")

            if state["alive"] and not state["won"] and not state["transition"]:
                d=Vector((0,0,0))
                if "UP" in state["keys"]: d.y+=1
                if "DOWN" in state["keys"]: d.y-=1
                if "LEFT" in state["keys"]: d.x-=1
                if "RIGHT" in state["keys"]: d.x+=1
                if d.length: hero.location += d.normalized()*SPEED*dt
                hero.location.x=max(BOUNDS[0],min(BOUNDS[1],hero.location.x))
                hero.location.y=max(BOUNDS[2],min(BOUNDS[3],hero.location.y))

                for e in list(state["enemies"]):
                    d=Vector((hero.location.x-e.location.x,hero.location.y-e.location.y,0))
                    if d.length:
                        e.location += d.normalized()*min(1.15*dt,d.length)
                    if dist(hero,e)<1.1:
                        damage(now)
                collect()

            pulse=state["pulse"]
            if pulse and pulse.name in scene.objects:
                age=now-pulse["created"]
                pulse.location=hero.location
                pulse.scale=(1+age*5,1+age*5,1+age*5)
                if age>.35:
                    bpy.data.objects.remove(pulse,do_unlink=True)
                    state["pulse"]=None

            # Real-time camera follow.
            cam=bpy.data.objects.get("Cinematic_Camera")
            if cam:
                target=Vector((hero.location.x*.35,hero.location.y*.35,0))
                cam.location.x += (target.x-cam.location.x)*.06
                cam.location.y += ((-11+target.y)-cam.location.y)*.06
                cam.rotation_euler=(Vector((target.x,target.y,0))-cam.location).to_track_quat("-Z","Y").to_euler()

            if context.area:
                context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def cancel(self,context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer=None
        state["keys"].clear()
        print("Starfall Dash prototype stopped.")
        return {"CANCELLED"}

try:
    bpy.utils.unregister_class(STARFALL_OT_PLAY)
except:
    pass
bpy.utils.register_class(STARFALL_OT_PLAY)
update_hud()

# Save a ready-to-test Blender file.
try:
    bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath("//Starfall_Dash_Playable_Arena.blend"))
except Exception as exc:
    print("Auto-save skipped:", exc)

print("=== STARFALL DASH PLAYABLE PROTOTYPE ===")
print("WASD / Arrows = move")
print("SPACE = close-range attack")
print("Kill enemies -> collect their dropped crystals")
print("3 crystals per stage; 3 stages = WIN")
print("Enemy contact = damage")
print("R = restart after death or victory")
print("ESC = stop")
print("========================================")
