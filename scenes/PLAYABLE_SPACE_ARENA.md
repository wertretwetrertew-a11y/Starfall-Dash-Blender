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
- Collect **3 crystals per stage**. There are **3 stages**, with enemy pressure increasing from 3 to 4 to 5 enemies.
- **R** — restart after death or victory.
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


## Current prototype progression

- Stage 1: 3 enemies, collect 3 crystals.
- Stage 2: 4 enemies, collect 3 crystals; enemies move faster.
- Stage 3: 5 enemies, collect 3 crystals; enemies move faster again.
- After completing a stage, the arena resets its enemy group and the player is repositioned for the next stage.
- The prototype prevents duplicate gameplay timers when the launcher is run twice.
- Reset clears stage-created drops and hides all known enemy slots before rebuilding Stage 1.

The final boss encounter is intentionally left as the next gameplay milestone so it can be implemented and tested separately rather than adding unverified combat logic to the current stable loop.


## Design direction

The prototype now treats movement and positioning as part of combat: the player has no ranged weapon, so the dash provides a controlled way to enter or escape close-range encounters. Dash cooldown and brief invulnerability are intentionally short so it remains a defensive tool rather than a permanent escape.


### Stability notes

The stage transition disables movement and combat input, resets attack/dash cooldown state for the new arena, and removes collected drops from the active drop list. This prevents repeated collection or attack effects from firing during the transition window.


### Star Eater boss

After collecting the third set of 3 crystals, the normal enemies disappear and the prototype starts a 1-on-1 Star Eater encounter. The boss has its own HP bar, follows the player at a higher speed, and damages the player only at close range. The player's existing Space attack is the only way to damage it; Dash remains the defensive tool. Defeating the boss completes the prototype run.

This is intentionally a first boss prototype: the fight is melee-only and uses simple pursuit/contact pressure before adding more complex boss phases.
