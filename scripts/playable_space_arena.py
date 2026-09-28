# Starfall Dash — Playable Space Arena Prototype
# Blender 3.x / 4.x
# Run space_arena.py first, then run this script.
# This adds a small playable prototype without changing the main game repo.

import bpy, math, time
from mathutils import Vector

# ---------- cleanup previous gameplay ----------
if hasattr(bpy.types, "STARFALL_OT_SPACE_ARENA"):
    try:
        bpy.utils.unregister_class(bpy.types.STARFALL_OT_SPACE_ARENA)
    except Exception:
        pass

for name in ("GAME_HUD", "GAME_OVER_TEXT", "GAME_WIN_TEXT"):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

for obj in list(bpy.context.scene.objects):
    if obj.name.startswith(("DROP_CRYSTAL_", "ABILITY_PULSE_")):
        bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
hero = bpy.data.objects.get("PLAYER_CUBE")

if hero is None:
    raise RuntimeError("PLAYER_CUBE not found. Run scripts/space_arena.py first.")

hero.animation_data_clear()

def get_mat(name, color, emission=None, strength=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = .3
    if emission:
        bs.inputs["Emission Color"].default_value = (*emission, 1)
        bs.inputs["Emission Strength"].default_value = strength
    return m

CRYSTAL = get_mat("Gameplay_Crystal", (.05, .95, 1.0), (.02, .8, 1.0), 15)
PULSE = get_mat("Ability_Pulse", (.1, .75, 1.0), (.05, .65, 1.0), 10)
DAMAGE = get_mat("Damage_Flash", (1.0, .08, .12), (1.0, .02, .02), 8)

MIN_X, MAX_X = -8.0, 8.0
MIN_Y, MAX_Y = -5.5, 5.5
MOVE_SPEED = 6.5
ABILITY_RADIUS = 2.25
ABILITY_COOLDOWN = .65
PLAYER_MAX_HP = 5
CONTACT_DAMAGE_COOLDOWN = 1.0
REQUIRED_CRYSTALS = 3

state = {
    "hp": PLAYER_MAX_HP,
    "crystals": 0,
    "alive": True,
    "won": False,
    "last_ability": -99.0,
    "last_damage": -99.0,
    "invulnerable_until": 0.0,
    "keys": set(),
    "enemies": [],
    "drops": [],
    "pulse": None,
}

# Remove the decorative center crystal. Gameplay crystals are created only by kills.
for obj in list(scene.objects):
    if obj.name == "COSMIC_CORE_CRYSTAL" or obj.name.startswith("COSMIC_CORE_CRYSTAL"):
        bpy.data.objects.remove(obj, do_unlink=True)

def create_crystal(name, loc):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.38, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (.65, 1.25, .65)
    o.rotation_euler = (0, .3, .4)
    o.data.materials.append(CRYSTAL)
    for p in o.data.polygons:
        p.use_smooth = True

    bpy.ops.mesh.primitive_torus_add(
        major_radius=.62, minor_radius=.018, major_segments=32,
        location=loc, rotation=(math.radians(65), 0, .4)
    )
    aura = bpy.context.object
    aura.name = name + "_Aura"
    aura.data.materials.append(CRYSTAL)
    return o

# Collect existing enemies.
for obj in scene.objects:
    if obj.name.startswith("Enemy_") and obj.type == "MESH" and "_Spike" not in obj.name:
        state["enemies"].append(obj)

enemy_positions = [(-1.5, 2.5, 0), (-.5, -3.0, 0), (2.3, -1.3, 0)]
for enemy, pos in zip(state["enemies"], enemy_positions):
    enemy.location = pos
    enemy.hide_viewport = False
    enemy.hide_render = False

def hud_text(name, body, x, y, size=.045):
    bpy.ops.object.text_add(location=(x, y, 0))
    o = bpy.context.object
    o.name = name
    o.data.body = body
    o.data.align_x = "LEFT"
    o.data.size = size
    o.data.extrude = .002
    o.data.materials.append(CRYSTAL)
    return o

hud = hud_text(
    "GAME_HUD",
    "STARFALL DASH  |  HP: 5/5  |  CRYSTALS: 0/3",
    -7.6, 5.05, .38
)

def set_message(name, body):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    o = hud_text(name, body, -4.5, 0, .7)
    o.data.align_x = "CENTER"
    o.location.z = .5
    return o

def make_pulse():
    bpy.ops.mesh.primitive_torus_add(
        major_radius=.25, minor_radius=.055, major_segments=48,
        location=hero.location
    )
    ring = bpy.context.object
    ring.name = "ABILITY_PULSE_RING"
    ring.data.materials.append(PULSE)
    ring["created_at"] = time.monotonic()
    return ring

def update_hud():
    hud.data.body = f"STARFALL DASH  |  HP: {state['hp']}/{PLAYER_MAX_HP}  |  CRYSTALS: {state['crystals']}/{REQUIRED_CRYSTALS}"

def distance_xy(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def kill_enemy(enemy):
    if enemy not in state["enemies"]:
        return

    pos = enemy.location.copy()
    enemy.hide_viewport = True
    enemy.hide_render = True

    prefix = enemy.name + "_Spike"
    for obj in scene.objects:
        if obj.name.startswith(prefix):
            obj.hide_viewport = True
            obj.hide_render = True

    idx = len(state["drops"]) + 1
    crystal = create_crystal(f"DROP_CRYSTAL_{idx}", (pos.x, pos.y, .25))
    state["drops"].append(crystal)
    state["enemies"].remove(enemy)

def use_ability(now):
    if not state["alive"] or state["won"]:
        return
    if now - state["last_ability"] < ABILITY_COOLDOWN:
        return

    state["last_ability"] = now
    pulse = make_pulse()
    state["pulse"] = pulse

    for enemy in list(state["enemies"]):
        if distance_xy(hero.location, enemy.location) <= ABILITY_RADIUS:
            kill_enemy(enemy)

def damage_player(now):
    if now < state["invulnerable_until"]:
        return

    state["hp"] -= 1
    state["last_damage"] = now
    state["invulnerable_until"] = now + CONTACT_DAMAGE_COOLDOWN

    if state["hp"] <= 0:
        state["alive"] = False
        set_message("GAME_OVER_TEXT", "DESTROYED  —  press R to restart")
    update_hud()

def collect_crystals():
    for crystal in list(state["drops"]):
        if crystal.hide_viewport:
            continue
        if distance_xy(hero.location, crystal.location) < .9:
            state["crystals"] += 1
            crystal.hide_viewport = True
            crystal.hide_render = True
            aura = bpy.data.objects.get(crystal.name + "_Aura")
            if aura:
                aura.hide_viewport = True
                aura.hide_render = True

            if state["crystals"] >= REQUIRED_CRYSTALS:
                state["won"] = True
                set_message("GAME_WIN_TEXT", "CORE FRAGMENT RECOVERED  —  YOU WIN!")
            update_hud()

def move_enemies(dt, now):
    if not state["alive"] or state["won"]:
        return

    for enemy in list(state["enemies"]):
        direction = Vector((hero.location.x - enemy.location.x, hero.location.y - enemy.location.y, 0))
        dist = direction.length
        if dist > .001:
            direction.normalize()
            enemy.location += direction * min(1.15 * dt, dist)

        if distance_xy(hero.location, enemy.location) < 1.15:
            damage_player(now)

def restart_game():
    for obj in list(scene.objects):
        if obj.name.startswith("DROP_CRYSTAL_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    state["hp"] = PLAYER_MAX_HP
    state["crystals"] = 0
    state["alive"] = True
    state["won"] = False
    state["last_ability"] = -99
    state["last_damage"] = -99
    state["invulnerable_until"] = 0
    state["enemies"] = []
    state["drops"] = []
    state["pulse"] = None

    hero.location = (-5.2, 0, 0)
    hero.hide_viewport = False
    hero.hide_render = False

    for i, pos in enumerate(enemy_positions, 1):
        enemy = bpy.data.objects.get(f"Enemy_{i}")
        if enemy:
            enemy.location = pos
            enemy.hide_viewport = False
            enemy.hide_render = False
            enemy.data.materials.clear()
            enemy.data.materials.append(bpy.data.materials.get("Enemy"))
            state["enemies"].append(enemy)

    for name in ("GAME_OVER_TEXT", "GAME_WIN_TEXT"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    update_hud()

class STARFALL_OT_SPACE_ARENA(bpy.types.Operator):
    bl_idname = "starfall.play_space_arena"
    bl_label = "Starfall Dash — Play Space Arena"

    _timer = None
    _last_time = 0.0

    def modal(self, context, event):
        now = time.monotonic()

        if event.type == "ESC" and event.value == "PRESS":
            self.cancel(context)
            return {"CANCELLED"}

        key_map = {
            "W": "UP", "UP_ARROW": "UP",
            "S": "DOWN", "DOWN_ARROW": "DOWN",
            "A": "LEFT", "LEFT_ARROW": "LEFT",
            "D": "RIGHT", "RIGHT_ARROW": "RIGHT",
        }
        if event.type in key_map:
            key = key_map[event.type]
            if event.value == "PRESS":
                state["keys"].add(key)
            elif event.value == "RELEASE":
                state["keys"].discard(key)

        if event.type == "SPACE" and event.value == "PRESS":
            use_ability(now)

        if event.type == "R" and event.value == "PRESS" and not state["alive"]:
            restart_game()

        if event.type == "TIMER":
            dt = min(max(now - self._last_time, 0.0), .05)
            self._last_time = now

            if state["alive"] and not state["won"]:
                direction = Vector((0, 0, 0))
                if "UP" in state["keys"]:
                    direction.y += 1
                if "DOWN" in state["keys"]:
                    direction.y -= 1
                if "LEFT" in state["keys"]:
                    direction.x -= 1
                if "RIGHT" in state["keys"]:
                    direction.x += 1

                if direction.length > 0:
                    direction.normalize()
                    hero.location += direction * MOVE_SPEED * dt

                hero.location.x = max(MIN_X, min(MAX_X, hero.location.x))
                hero.location.y = max(MIN_Y, min(MAX_Y, hero.location.y))

                move_enemies(dt, now)
                collect_crystals()

            pulse = state.get("pulse")
            if pulse and pulse.name in scene.objects:
                age = now - pulse.get("created_at", now)
                pulse.location = hero.location
                pulse.scale = (1 + age * 5, 1 + age * 5, 1 + age * 5)
                if age > .35:
                    bpy.data.objects.remove(pulse, do_unlink=True)
                    state["pulse"] = None

            if context.area:
                context.area.tag_redraw()

        return {"RUNNING_MODAL"}

    def execute(self, context):
        self._last_time = time.monotonic()
        wm = context.window_manager
        self._timer = wm.event_timer_add(.016, window=context.window)
        wm.modal_handler_add(self)
        print("Starfall Dash playable prototype started.")
        print("WASD / arrows = move | SPACE = close-range ability | R = restart after death | ESC = stop")
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        state["keys"].clear()
        print("Starfall Dash playable prototype stopped.")

bpy.utils.register_class(STARFALL_OT_SPACE_ARENA)

cam = bpy.data.objects.get("Cinematic_Camera")
if cam:
    def track_camera(scene):
        if not hero or hero.name not in scene.objects:
            return
        target = Vector((hero.location.x * .35, hero.location.y * .35, 0))
        cam.location.x += (target.x - cam.location.x) * .035
        cam.location.y += ((-11 + target.y) - cam.location.y) * .035
        cam.rotation_euler = (Vector((target.x, target.y, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()

    for h in list(bpy.app.handlers.frame_change_post):
        if getattr(h, "__name__", "") == "starfall_track_camera":
            bpy.app.handlers.frame_change_post.remove(h)

    track_camera.__name__ = "starfall_track_camera"
    bpy.app.handlers.frame_change_post.append(track_camera)

update_hud()
print("")
print("=== STARFALL DASH PLAYABLE PROTOTYPE ===")
print("WASD / Arrow Keys : move")
print("SPACE             : close-range cosmic pulse")
print("Kill enemies to make them drop crystals.")
print("Collect 3 dropped crystals to win.")
print("Touching enemies damages the player.")
print("R                 : restart after death")
print("ESC               : stop prototype")
print("Run: bpy.ops.starfall.play_space_arena()")
print("=========================================")
