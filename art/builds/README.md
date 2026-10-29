# CROATOAN gate beauty corner: build log

Target: `art/levels/roanoke/croatoan-gate.jpg`. Unreal Engine 5.8.4, Lumen (software; this Shadow PC's NVIDIA 565.90 driver crashes with hardware ray tracing), volumetric fog.
Assets: free Quixel Megascans from Fab (Standard License, $0 for Unreal): Old Wooden Log x2, Old Wooden Beam, Soil Mud, Wild Grass, Military Trenches Ground Mud. The CROATOAN carving and the scratched 1587 colonists' names are our own texture.
Project: `C:\LETHE` (map `L_Beauty_CroatoanGate`, script `Scripts/build_beauty_gate.py`).

## Round 1 · 2026-10-29

![round 1](2026-10-29_gate_round1.png)

Working: real scanned bark and cracks on every log; wet mud with puddles in the low spots; composition close to the reference (bastion left, lashed pole gate with lantern, dark gatepost, stripped post right).

Differences from the reference, to fix in round 2:
1. Fog glows yellow-white; the reference is a dark blue-grey night. Warm light behind the wall floods the fog, and the fog scatters strongly toward the camera.
2. CROATOAN reads vertically: the carving decal is rotated 90°.
3. Post reads magenta (violet UV beam mixed with orange light); should be pale wood under a cool violet beam.
4. Editor icons (light bulbs, fog sprite, a volume outline) were captured in the render.
5. Still the old 24 mm camera; the 35 mm low-angle camera from the brief applies from round 2.
6. No rocks or weeds yet; tall grass reads too sparse.
