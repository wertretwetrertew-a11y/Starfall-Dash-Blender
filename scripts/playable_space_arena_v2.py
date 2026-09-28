# Starfall Dash — Playable Space Arena v2
# Run scripts/space_arena.py first, then run this script.
# Blender 3.x / 4.x

import bpy, math, time
from mathutils import Vector

scene = bpy.context.scene
hero = bpy.data.objects.get("PLAYER_CUBE")
if not hero:
    raise RuntimeError("Run scripts/space_arena.py first.")

HERO_BASE_SCALE = hero.scale.copy()

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
BOSS = material("Gameplay_Boss", (.55,.08,1), (.7,.03,1), 18)
BOSS_AURA = material("Gameplay_Boss_Aura", (.15,.02,.35), (.4,.02,1), 10)
ENEMY_NORMAL = material("Gameplay_Enemy_Normal", (.9,.18,.08), (1,.05,.01), 7)
ENEMY_FAST = material("Gameplay_Enemy_Fast", (.95,.65,.05), (1,.35,.01), 10)
ENEMY_HEAVY = material("Gameplay_Enemy_Heavy", (.45,.12,.8), (.3,.02,1), 8)

# Constants.
SPEED = 6.5
DASH_SPEED = 15.0
DASH_DURATION = 0.16
DASH_COOLDOWN = 1.2
ABILITY_RANGE = 2.25
ABILITY_COOLDOWN = .65
MAX_HP = 5
DAMAGE_COOLDOWN = 1.0
CRYSTALS_PER_STAGE = 3
STAGES = 3
BOSS_HP = 10
BOSS_SPEED = 1.35
BOSS_CONTACT_RANGE = 1.35
BOSS_ATTACK_COOLDOWN = 1.15
BOSS_PHASE2_SPEED = 1.75
BOSS_PHASE2_COOLDOWN = 0.8
BOUNDS = (-8, 8, -5.5, 5.5)
STAGE_LAYOUTS = {1:[(-1.5,2.5,0),(-.5,-3,0),(2.3,-1.3,0)],2:[(-2.5,3.5,0),(1,3,0),(3.5,-2.5,0),(-3.5,-2,0)],3:[(-5.5,4.2,0),(-1.8,4.5,0),(2,4.3,0),(5.5,3.8,0),(0,-3.8,0)]}

state = {
    "hp": MAX_HP, "crystals": 0, "stage": 1, "alive": True, "won": False, "transition": False, "transition_until": 0.0,
    "last_attack": -99.0, "last_dash": -99.0, "dash_until": 0.0, "dash_dir": Vector((0,0,0)), "invuln": 0.0, "keys": set(),
    "enemies": [], "drops": [], "pulse": None, "boss": None, "boss_hp": BOSS_HP, "boss_last_attack": -99.0, "boss_active": False, "boss_phase": 1, "message_until": 0.0,
    "damage_flash_until": 0.0, "dash_trail_until": 0.0, "boss_phase_notice": False
}

# Remove decorative center crystal from the cinematic scene.
for o in list(scene.objects):
    if o.name.startswith("COSMIC_CORE_CRYSTAL"):
        bpy.data.objects.remove(o, do_unlink=True)

enemy_positions = [(-1.5,2.5,0), (-.5,-3,0), (2.3,-1.3,0)]

# Hide any previous boss instance if the script is re-run.
existing_boss = bpy.data.objects.get("STAR_EATER_BOSS")
if existing_boss:
    existing_boss.hide_viewport = True
    existing_boss.hide_render = True
existing_boss_aura = bpy.data.objects.get("STAR_EATER_BOSS_AURA")
if existing_boss_aura:
    existing_boss_aura.hide_viewport = True
    existing_boss_aura.hide_render = True

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
    if state["boss_active"]:
        phase = "II" if state["boss_phase"] == 2 else "I"
        hud.data.body = f"STARFALL DASH   |   STAR EATER PHASE {phase}   |   HP {state['hp']}/{MAX_HP}   |   BOSS {state['boss_hp']}/{BOSS_HP}"
    else:
        hud.data.body = f"STARFALL DASH   |   STAGE {state['stage']}/{STAGES}   |   HP {state['hp']}/{MAX_HP}   |   CRYSTALS {state['crystals']}/{CRYSTALS_PER_STAGE}"

def message(body, duration=1.5):
    for name in ("GAME_MESSAGE","GAME_OVER","GAME_WIN"):
        o=bpy.data.objects.get(name)
        if o: bpy.data.objects.remove(o,do_unlink=True)
    msg = make_text("GAME_MESSAGE",body,(0,0,.6),.65)
    state["message_until"] = time.monotonic() + duration
    return msg

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
        # Three readable melee roles: normal, fast/fragile, heavy/slow.
        role = "normal" if i % 3 == 1 else ("fast" if i % 3 == 2 else "heavy")
        e["role"] = role
        # Visual language matches combat role.
        if role == "fast":
            e.data.materials.clear()
            e.data.materials.append(ENEMY_FAST)
        elif role == "heavy":
            e.data.materials.clear()
            e.data.materials.append(ENEMY_HEAVY)
        else:
            e.data.materials.clear()
            e.data.materials.append(ENEMY_NORMAL)
        if role == "fast":
            e["speed"] = 1.65 + (state["stage"] - 1) * .18
            e["hp"] = 1
            e["knockback"] = 1.25
            e.scale = (.72,.72,.72)
        elif role == "heavy":
            e["speed"] = .82 + (state["stage"] - 1) * .12
            e["hp"] = 3
            e["knockback"] = .55
            e.scale = (1.28,1.28,1.28)
        else:
            e["speed"] = 1.15 + (state["stage"] - 1) * .28
            e["hp"] = 1
            e["knockback"] = .9
            e.scale = (1,1,1)
        e.location=loc
        e.hide_viewport=False
        e.hide_render=False
    update_hud()

def spawn_boss():
    for e in list(state["enemies"]):
        e.hide_viewport = True
        e.hide_render = True
    state["enemies"].clear()
    for c in list(state["drops"]):
        aura = bpy.data.objects.get(c.name+"_AURA")
        if c.name in scene.objects:
            bpy.data.objects.remove(c, do_unlink=True)
        if aura:
            bpy.data.objects.remove(aura, do_unlink=True)
    state["drops"].clear()
    boss = bpy.data.objects.get("STAR_EATER_BOSS")
    if not boss:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(3.0,0,0))
        boss = bpy.context.object
        boss.name = "STAR_EATER_BOSS"
        boss.data.materials.append(BOSS)
        for p in boss.data.polygons:
            p.use_smooth = True
        bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=.055, major_segments=48, location=boss.location)
        aura = bpy.context.object
        aura.name = "STAR_EATER_BOSS_AURA"
        aura.data.materials.append(BOSS_AURA)
        aura.rotation_euler=(math.radians(65),0,0)
    boss.location=(3.0,0,0)
    boss.scale=(1.55,1.55,1.55)
    boss.hide_viewport=False
    boss.hide_render=False
    aura=bpy.data.objects.get("STAR_EATER_BOSS_AURA")
    if aura:
        aura.location=boss.location
        aura.hide_viewport=False
        aura.hide_render=False
    state["boss"]=boss
    state["boss_hp"]=BOSS_HP
    state["boss_last_attack"]=-99.0
    state["boss_active"]=True
    state["boss_phase"]=1
    state["crystals"]=0
    hero.location=(-4.5,0,0)
    update_hud()
    message("STAR EATER — DEFEAT THE BOSS", 2.5)

def damage_boss():
    boss=state["boss"]
    if not state["boss_active"] or not boss or boss.hide_viewport:
        return
    state["boss_hp"]-=1
    if state["boss_hp"] <= BOSS_HP // 2 and state["boss_phase"] == 1:
        state["boss_phase"]=2
        state["boss_phase_notice"]=True
        message("STAR EATER — PHASE II", 1.4)
    boss.scale=(1.75,1.75,1.75)
    boss["hit_until"]=time.monotonic()+.12
    boss["base_scale"]=1.55
    update_hud()
    if state["boss_hp"]<=0:
        boss.hide_viewport=True
        boss.hide_render=True
        aura=bpy.data.objects.get("STAR_EATER_BOSS_AURA")
        if aura:
            aura.hide_viewport=True
            aura.hide_render=True
        state["boss_active"]=False
        state["won"]=True
        message("STAR EATER DEFEATED — COSMIC CORE RESTORED", 9999)

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
    update_hud()

def hit_enemy(enemy):
    if enemy not in state["enemies"]:
        return
    enemy["hp"] = max(0, int(enemy.get("hp", 1)) - 1)
    enemy["hit_until"] = time.monotonic() + .12
    away = Vector((enemy.location.x-hero.location.x, enemy.location.y-hero.location.y, 0))
    if away.length:
        enemy["knockback_dir"] = away.normalized()
        enemy["knockback_until"] = time.monotonic() + .10
    if enemy["hp"] <= 0:
        kill_enemy(enemy)
    else:
        enemy.scale = enemy.scale * 1.14

def attack(now):
    if not state["alive"] or state["won"] or state["transition"] or now-state["last_attack"] < ABILITY_COOLDOWN:
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

    if state["boss_active"] and state["boss"] and dist(hero,state["boss"]) <= ABILITY_RANGE + .25:
        damage_boss()
    else:
        for enemy in list(state["enemies"]):
            if dist(hero,enemy) <= ABILITY_RANGE:
                hit_enemy(enemy)

def dash(now):
    if not state["alive"] or state["won"] or state["transition"] or now-state["last_dash"] < DASH_COOLDOWN:
        return
    d=Vector((0,0,0))
    if "UP" in state["keys"]: d.y+=1
    if "DOWN" in state["keys"]: d.y-=1
    if "LEFT" in state["keys"]: d.x-=1
    if "RIGHT" in state["keys"]: d.x+=1
    if not d.length:
        d=Vector((1,0,0))
    state["dash_dir"]=d.normalized()
    state["last_dash"]=now
    state["dash_until"]=now+DASH_DURATION
    state["dash_trail_until"]=now+.22
    bpy.ops.mesh.primitive_cube_add(size=1, location=hero.location)
    trail=bpy.context.object
    trail.name="ABILITY_DASH_TRAIL"
    trail.scale=HERO_BASE_SCALE*1.08
    trail.data.materials.append(PULSE)
    trail["created"]=now
    state["invuln"]=max(state["invuln"],state["dash_until"])

def damage(now):
    if now < state["invuln"]:
        return
    state["hp"]-=1
    state["invuln"]=now+DAMAGE_COOLDOWN
    state["damage_flash_until"]=now+.18
    update_hud()
    if state["hp"]<=0:
        state["alive"]=False
        message("DESTROYED   —   press R to restart", 9999)

def collect():
    for c in list(state["drops"]):
        if not c.hide_viewport and dist(hero,c)<.95:
            state["crystals"]+=1
            c.hide_viewport=True
            c.hide_render=True
            state["drops"].remove(c)
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
                    message("STAGE COMPLETE   —   NEXT STAGE", 1.2)
                else:
                    state["transition"] = True
                    state["transition_until"] = time.monotonic() + 1.2
                    message("STAGE COMPLETE — BOSS INCOMING", 1.8)

def reset():
    for o in list(scene.objects):
        if o.name.startswith(("DROP_CRYSTAL_","GAME_MESSAGE","GAME_OVER","GAME_WIN","ABILITY_")):
            bpy.data.objects.remove(o,do_unlink=True)
    state.update({"hp":MAX_HP,"crystals":0,"stage":1,"alive":True,"won":False,"transition":False,"transition_until":0.0,
                  "last_attack":-99.0,"last_dash":-99.0,"dash_until":0.0,"dash_dir":Vector((0,0,0)),"invuln":0.0,"keys":set(),
                  "enemies":[],"drops":[],"pulse":None,"boss":None,"boss_hp":BOSS_HP,"boss_last_attack":-99.0,"boss_active":False,"boss_phase":1,"message_until":0.0,
                  "damage_flash_until":0.0,"dash_trail_until":0.0,"boss_phase_notice":False})
    hero.location=(-5.2,0,0)
    hero.hide_viewport=False
    hero.hide_render=False
    boss=bpy.data.objects.get("STAR_EATER_BOSS")
    if boss:
        boss.hide_viewport=True
        boss.hide_render=True
    boss_aura=bpy.data.objects.get("STAR_EATER_BOSS_AURA")
    if boss_aura:
        boss_aura.hide_viewport=True
        boss_aura.hide_render=True
    for i in range(1,6):
        e=bpy.data.objects.get(f"Enemy_{i}")
        if e:
            e.hide_viewport=True
            e.hide_render=True
            for o in scene.objects:
                if o.name.startswith(e.name+"_Spike"):
                    o.hide_viewport=True
                    o.hide_render=True
    spawn_stage()
    update_hud()

class STARFALL_OT_PLAY(bpy.types.Operator):
    bl_idname="starfall.play_v2"
    bl_label="Starfall Dash Playable Prototype"
    timer=None
    last=0

    def execute(self,context):
        if scene.get("STARFALL_RUNNING", False):
            print("Starfall Dash prototype is already running.")
            return {"CANCELLED"}
        scene["STARFALL_RUNNING"] = True
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
        if event.type=="LEFT_SHIFT" and event.value=="PRESS":
            dash(now)
        if event.type=="R" and event.value=="PRESS" and (not state["alive"] or state["won"]):
            reset()

        if event.type=="TIMER":
            dt=min(max(now-self.last,0),.05)
            self.last=now

            if state["transition"] and now >= state["transition_until"]:
                state["transition"] = False
                hero.location=(-5.2,0,0)
                state["last_attack"]=now
                state["last_dash"]=now
                if state["stage"] == STAGES and not state["boss_active"] and not state["won"]:
                    spawn_boss()
                else:
                    spawn_stage()
                    message("NEW STAGE — COLLECT 3 CRYSTALS", 1.2)

            if state["alive"] and not state["won"] and not state["transition"]:
                d=Vector((0,0,0))
                if "UP" in state["keys"]: d.y+=1
                if "DOWN" in state["keys"]: d.y-=1
                if "LEFT" in state["keys"]: d.x-=1
                if "RIGHT" in state["keys"]: d.x+=1
                if d.length: hero.location += d.normalized()*SPEED*dt
                if now < state["dash_until"]:
                    hero.location += state["dash_dir"]*DASH_SPEED*dt
                hero.location.x=max(BOUNDS[0],min(BOUNDS[1],hero.location.x))
                hero.location.y=max(BOUNDS[2],min(BOUNDS[3],hero.location.y))

                for e in list(state["enemies"]):
                    enemy_speed = e.get("speed", 1.15 + (state["stage"] - 1) * 0.28)
                    d=Vector((hero.location.x-e.location.x,hero.location.y-e.location.y,0))
                    if d.length:
                        e.location += d.normalized()*min(enemy_speed*dt,d.length)
                    if e.get("knockback_until", 0.0) > now:
                        kb=e.get("knockback_dir", Vector((0,0,0)))
                        e.location += kb * (3.0 + e.get("knockback", .9) * 2.0) * dt
                    contact_range = {"fast": .95, "heavy": 1.25, "normal": 1.1}.get(e.get("role"), 1.1)
                    if dist(hero,e)<contact_range:
                        damage(now)

                for e in list(state["enemies"]):
                    if e.name in scene.objects and e.get("hit_until", 0.0) > now:
                        base = {"fast": .72, "heavy": 1.28, "normal": 1.0}.get(e.get("role"), 1.0)
                        e.scale=(base*1.14,base*1.14,base*1.14)
                    elif e.name in scene.objects:
                        base = {"fast": .72, "heavy": 1.28, "normal": 1.0}.get(e.get("role"), 1.0)
                        e.scale=(base,base,base)

                if state["boss_active"] and state["boss"] and not state["boss"].hide_viewport:
                    boss=state["boss"]
                    d=Vector((hero.location.x-boss.location.x,hero.location.y-boss.location.y,0))
                    if d.length:
                        boss_speed = BOSS_PHASE2_SPEED if state["boss_phase"] == 2 else BOSS_SPEED
                        boss.location += d.normalized()*min(boss_speed*dt,d.length)
                    aura=bpy.data.objects.get("STAR_EATER_BOSS_AURA")
                    if aura:
                        aura.location=boss.location
                        aura.rotation_euler.z += dt * (2.4 if state["boss_phase"] == 2 else 1.2)
                    boss_cooldown = BOSS_PHASE2_COOLDOWN if state["boss_phase"] == 2 else BOSS_ATTACK_COOLDOWN
                    if dist(hero,boss)<BOSS_CONTACT_RANGE and now-state["boss_last_attack"]>=boss_cooldown:
                        state["boss_last_attack"]=now
                        damage(now)
                collect()

            for index, crystal in enumerate(list(state["drops"])):
                if crystal.name in scene.objects and not crystal.hide_viewport:
                    crystal.rotation_euler.z += dt * 2.2
                    crystal.location.z = 0.25 + math.sin(now * 4.0 + index) * 0.08
                    aura = bpy.data.objects.get(crystal.name+"_AURA")
                    if aura:
                        aura.location = crystal.location
                        aura.rotation_euler.z += dt * 1.4

            boss=state["boss"]
            if boss and boss.name in scene.objects and "hit_until" in boss:
                if now >= boss["hit_until"] and not boss.hide_viewport:
                    base = 1.55
                    boss.scale=(base,base,base)

            msg=bpy.data.objects.get("GAME_MESSAGE")
            if msg and state["message_until"] and now >= state["message_until"] and state["alive"] and not state["won"]:
                bpy.data.objects.remove(msg,do_unlink=True)
                state["message_until"]=0.0

            trail=bpy.data.objects.get("ABILITY_DASH_TRAIL")
            if trail and trail.name in scene.objects:
                age=now-trail["created"]
                trail.location=hero.location-state["dash_dir"]*.38
                trail.scale=hero.scale*(1.08+max(0,.22-age)*1.6)
                if age>.22:
                    bpy.data.objects.remove(trail,do_unlink=True)

            if now < state["damage_flash_until"]:
                hero.scale=HERO_BASE_SCALE*1.12
            else:
                hero.scale=HERO_BASE_SCALE

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
        scene["STARFALL_RUNNING"] = False
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
print("LEFT SHIFT = dash / brief invulnerability")
print("Kill enemies -> collect their dropped crystals")
print("3 crystals per stage; after stage 3, face the Star Eater boss")
print("Enemy roles: normal / fast / heavy; all attacks are melee")
print("Enemy contact = damage; boss is a close-range duel")
print("R = restart after death or victory")
print("ESC = stop")
print("========================================")
