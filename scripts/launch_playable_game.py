# Starfall Dash — One-click Blender prototype launcher
# Run this script from Blender's Scripting workspace.
# It builds the arena, installs gameplay, saves the .blend, and starts the prototype.

import bpy

BASE = bpy.path.abspath("//")

def run_script(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    exec(compile(source, path, "exec"), {"__file__": path, "__name__": "__main__"})

run_script(BASE + "scripts/space_arena.py")
run_script(BASE + "scripts/playable_space_arena_v2.py")

bpy.ops.starfall.play_v2()
print("Starfall Dash playable prototype launched.")
