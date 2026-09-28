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

### One-click launch (recommended)
1. Open the repository folder in Blender's environment so the `scripts` folder is next to the `.blend` file.
2. Open `scripts/launch_playable_game.py` in Blender's Scripting workspace.
3. Run the script.
4. Move the mouse over the **3D Viewport** so Blender sends keyboard input to the viewport.
5. Press **WASD** or the arrow keys.
6. Use **Space** near an enemy.
7. Collect three crystals.

The launcher builds the arena, installs gameplay, saves `Starfall_Dash_Playable_Arena.blend`, and starts the prototype.

### Manual launch
1. Run `scripts/space_arena.py` first.
2. Then run `scripts/playable_space_arena_v2.py`.
3. Use the same controls above.

The v2 prototype starts from the current PLAYER_CUBE, enemies, arena, planet, comets and camera created by space_arena.py. It also saves a ready-to-test Starfall_Dash_Playable_Arena.blend.

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
