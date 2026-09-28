# Starfall Dash — One-click Blender prototype launcher
# Open this file together with the other scripts in Blender's Text Editor and Run Script.
# This version executes the scripts from Blender Text datablocks, so it does not depend
# on the current working directory or an already-saved .blend path.

import bpy

def run_text(name):
    text = bpy.data.texts.get(name)
    if not text:
        raise RuntimeError("Missing Blender Text datablock: " + name)
    source = text.as_string()
    exec(compile(source, name, "exec"), {"__file__": name, "__name__": "__main__"})

run_text("space_arena.py")
run_text("playable_space_arena_v2.py")
bpy.ops.starfall.play_v2()
print("Starfall Dash playable prototype launched.")
