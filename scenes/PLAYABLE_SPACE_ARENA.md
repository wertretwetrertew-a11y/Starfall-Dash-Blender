# Playable Space Arena Prototype

This is a small playable prototype built on top of the cinematic Space Arena scene.

It is intentionally separate from the main 2D Starfall Dash game.

## What is playable

- **WASD / Arrow Keys** — move the cube.
- **SPACE** — short-range Cosmic Pulse. It damages/destroys enemies only when they are close to the player.
- Enemies move toward the player.
- Touching an enemy costs **1 HP**.
- The player starts with **5 HP**.
- Defeated enemies create crystal drops.
- Collect **3 crystals** to win.
- **R** — restart after death.
- **ESC** — stop the prototype.

There are no ranged attacks in this prototype.

## How to run

1. Open Blender 3.x/4.x.
2. Open the repository script: scripts/space_arena.py
3. Run it first. This creates the Space Arena.
4. Then open: scripts/playable_space_arena.py
5. Run that script.
6. Move the mouse over the **3D Viewport** so Blender sends keyboard input to the viewport.
7. Press **WASD** or the arrow keys.
8. Use **Space** near an enemy.
9. Collect three crystals.

The prototype starts from the current PLAYER_CUBE, enemies, arena, planet, comets and camera created by space_arena.py.

## Important

This is a Blender gameplay experiment, not a standalone build of Starfall Dash.

It does **not** modify the main game repository.

The prototype is designed to test the feel of:
- cube movement in the arena;
- close-range combat;
- enemy pressure;
- collision damage;
- crystal collection;
- a simple win condition.

## Suggested next iteration

After the basic loop feels good, this prototype can be expanded with:
- better close-range attack animation;
- hit-stop and impact effects;
- enemy variants;
- health bar;
- crystal attraction/pickup effect;
- a proper start/restart screen;
- boss encounter;
- stage transitions;
- a more faithful recreation of the 2D game's movement and combat rules.
