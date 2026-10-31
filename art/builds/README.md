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

## Round 2 · 2026-10-29

![round 2](2026-10-29_gate_round2.png)

Fixed since round 1: night mood (dark blue-grey fog, less forward glare), 35 mm low-angle CineCamera with shallow depth of field, lanterns limited to ~8 m, carving decal rotated to read horizontally, editor icons removed, every exposure saves.

Differences from the reference, to fix in round 3:
1. A large pink blur hides the CROATOAN post and its carving: the UV lantern's light source now sits inside the 35 mm frame. Move it out of frame to the right and soften its glow in the fog.
2. The stripped post must read as the brightest, palest object; it is currently hidden.
3. Fog leans mauve; the reference is colder blue-grey.
4. Ground foreground is good (wet mud, reflections); grass and weeds barely read.
5. Warm glow behind the gate is still larger than the reference's small lantern points.

## Round 3 · 2026-10-29

![round 3](2026-10-29_gate_round3.png)

Fixed since round 2: the UV lantern is out of frame; colder fog; dimmer gate lantern.

Differences from the reference, to fix in round 4:
1. The UV beam reads as a wide, out-of-focus pink band across the frame; the reference has a tight violet-blue beam landing on the letters.
2. The carving decal's width and height were swapped by the rotation, so CROATOAN is stretched about 2.5 m round the post and only a sliver shows.
3. The stripped post doesn't read pale: nothing lights it from the front. The reference post is the palest, best-lit object.
4. Grass, weeds and rocks still barely read.

## Round 4 · 2026-10-29

![round 4](2026-10-29_gate_round4.png)

Fixed since round 3: the stripped post now reads as the palest object (cool fill from out of frame); CROATOAN is legible at 1.5 m; deeper focus.

Differences from the reference, to fix in round 5:
1. The UV beam renders red-orange instead of violet: the light colour channels were set in the wrong order.
2. CROATOAN is too small in frame: the camera is ~13 m from the post, where the reference stands close. Move to ~8 m, keeping the bastion and gate in shot.
3. Rocks, weeds and tall grass still to add.

## Round 5 · 2026-10-29

No image: the editor throttled itself to ~3 fps while it was not the front window and every capture timed out. Fixed in `Config/DefaultEditorPerProjectUserSettings.ini` (`bThrottleCPUWhenNotForeground=False`). Its changes (violet beam colour, closer camera) went into round 6.

## Round 6 · 2026-10-29

![round 6](2026-10-29_gate_round6.png)

New since round 4 (design-session review applied): irregular axe-hewn wedge tips, some broken flat; trunks 25-45 cm x 3.5-4.5 m with random lean and spin, a few gaps; lashed cross-rails; the entrance rebuilt as a narrow gap between two great posts barred with heavy timbers (the CROATOAN post is now the right-hand post itself), bark left on above the stripped band; carved-normal on the letters; 8 more free Megascans (3 rocks, curbside weeds, nettle, dry grass, wheat grass, dead shrubs) crowding the wall foot; watch platform with its lantern in the fog, top left as in the reference.

Differences from the reference, to fix in round 7:
1. Camera too close and too low: the post fills the frame and is cropped; the flanker and gate are mostly out of shot. Go to 40 mm at ~8.6 m, eye height.
2. Violet floods the rails and the left gatepost; the UV beam should be a tight spot on the letters only.
3. CROATOAN barely reads: the violet glow washes out the dark cuts. Darker, deeper grooves; less UV emission.
4. The bark band above the stripped section bulges like a cap; it should be flush.
5. A floating lantern hook rod; the warm glow behind the right wall is too strong.

## Round 7 · 2026-10-29

![round 7](2026-10-29_gate_round7.png)

Fixed since round 6: 40 mm framing with the watch platform, flanker, barred gap and post all in shot; the UV beam is a tight spot; the later names (MARGERY HARVIE, ROGER BAYLYE, THOMAS WARNER…) read on the post.

Differences from the reference, to fix in round 8 (with the design session's round 6 review):
1. CROATOAN shows only "ROATO": it wraps past the visible face, and a gate bar crosses the 1.5 m line. Turn the carving to face the camera, use condensed Roman capitals (~11 cm) on a wider post, move the bars clear.
2. The cuts read lavender, not dark: remove the UV glow from the grooves.
3. The stripped band reads as white plaster; it should be cream-to-tan wood with grain.
4. Palisade: thicker trunks (35-55 cm) set tight with no daylight; rails behind the trunks, not in front.
5. Orange haze behind the wall; the reference is a cool blue-grey night with small warm points.

## Round 8 · 2026-10-29

![round 8](2026-10-29_gate_round8.png)

Fixed since round 7: CROATOAN reads in dark, deep Roman capitals at 1.5 m with the later names round it; the carving faces the camera on a wider post; stripped band is pale tan wood with grain; trunks 35-55 cm set tight with rails behind; the orange is mostly gone.

Differences from the reference, to fix in round 9:
1. The final N is clipped at the post's edge: narrow the word slightly and centre it on the visible face.
2. The UV spot also lights the left gatepost through the gap: tighter cone.
3. Gate bars stop short of the post.
4. The bark band above the stripped section still bulges like a cap (the scan used has a knot there).
5. Warm glow behind the gap still a little large.

## Round 9 · 2026-10-29

![round 9](2026-10-29_gate_round9.png)

Fixed since round 8: flush bark band above the stripped section; gate bars reach the post; tight UV spot; smaller warm glow behind the gap.

Differences from the reference, to fix in round 10 (final pass for now):
1. The last N is still clipped: turning the carving to -31° moved it the wrong way. Turn to about -12°.
2. The letters look printed (design-session review): cut them by hand: each letter its own size, tilt and baseline, uneven spacing, V-grooves with chipped edges, wood grain visible inside the cuts.

## Round 10 · 2026-10-29

![round 10](2026-10-29_gate_round10.png)

New: CROATOAN cut by hand: each letter its own size, tilt and baseline, uneven spacing, V-grooves with chipped edges, wood grain inside the cuts (`tools/make_carving_mask.ps1`). The scene script is in `tools/build_beauty_gate.py`.

Still to fix (round 11): the final N touches the post's edge; the cuts read lighter than in round 9.

## Round 11 · 2026-10-29

![round 11](2026-10-29_gate_round11.png)

Darker cuts with grain; turning the carving moved the word left, but it was simply wider than the visible face: C at the left edge, N still clipped.

## Round 12 · 2026-10-29 · first beauty pass done

![round 12](2026-10-29_gate_round12_final.png)

All eight letters of CROATOAN read: hand-cut Roman capitals, 1.5 m up the stripped right-hand post, in the violet beam, with the later names scratched round them. Word narrowed 20% to sit on the visible face.

Agreed with the design session: this closes the first beauty pass. A second pass will come with Nysa (MetaHuman) in the shot. Known items for that pass: the warm glow behind the gap is still a little large; the left gatepost catches some violet; Nysa and her lantern replace the off-screen UV source.

## Sketch match · round 1 · 2026-10-30

![sketch match round 1](2026-10-29_gate_match_r1.png)

Scene rebuilt against `art/levels/roanoke/croatoan-gate.jpg`. Render 2560x1440, 35 mm at eye height 1.6 m, exposure -2 EV.

New this round:
- Moonlit blue-grey fog. Warm light only from the gate lantern, the tower lantern and the house windows. UV beam aimed at the post only.
- Wet mud ground with puddles, a few stones, small tufts at stake feet only (no tall grass).
- Thicker CROATOAN post (76 cm) with a tall stripped panel. Letters are 10 cm high at 1.5 m. No cross, no extra names.
- Gate between two posts with lashed crossbars, rope-lashed rails on the palisade, stakes of uneven height, lean and girth.
- Axe-cut stake points built from our own faceted meshes (`tools/make_hewn_tips.py`), not cones.
- Watchtower with shingle roof, rails and lantern. Timber-frame house with chimney and two lit windows.

Still far from the sketch (round 2):
1. Composition: the two gateposts stand like a tall ladder in mid-frame. The palisade on the left fills too much of the frame. The tower and house are lost in the fog.
2. Fog is too thick and shows streaky shadow shafts. It needs to be thinner near the camera so the background shapes read.
3. The UV pool is a hard, saturated blue oval. It should be a softer violet wash.
4. The stripped panel reads grey, not pale wood. The last N is clipped at the post edge, and the letters still look too even.
5. Stake points are too regular and slightly wider than the log, so they read as arrowheads.
6. The foreground mud is too flat and empty.

## Sketch match · round 2 · 2026-10-30

![sketch match round 2](2026-10-30_gate_match_r2.png)

Changes from the round 1 review (exposure -0.5 EV):
- A. Camera 4 m from the post, looking along one wall that recedes left. The gate opening with its lantern is centre-left. The right gatepost stands close to the CROATOAN post, and a short run of palisade continues behind it to the right. The lintels now span only the opening.
- B. Every letter is cut differently: height ±15%, tilt ±4°, wandering baseline, its own stroke weight, uneven spacing. All 8 letters sit on the panel with margin. A few dry cracks run with the grain.
- C. UV beam is violet-white with a soft edge, held off-axis from the left, about 1.5x the width of the word.
- D. The post uses its own log scan (the old mismatch gave the "grey paint" look). The panel grain now comes from one continuous strip of the scan, with no repeated tiles. A torn bark rim with depth runs round the panel edge.
- E/F. Fog shadow shafts are off. The sky and fog glow are lifted, so the watchtower (top left) and the house with two lit windows (top right) read as dark shapes.
- G. Thicker rope lashings on the gate crossbars beside the lantern.
- Stake points no wider than the log, shorter and more uneven.

Still to fix (round 3):
1. The fog went too thin. The background is too crisp, and the tower and house look too near. Bring back a light, even haze that grows with distance, and push the tower and house further back or make them smaller.
2. The tower roof reads as one flat slab. It needs visible shingle rows and a darker underside.
3. The post bark edges are not dark enough against the pale panel. Darken the bark and make the rim stand out more.
4. The mud foreground shows a regular tile pattern in the puddles. Break it up with the mud decals and more stones.
5. At this distance the letters still look a little even. The variation could go further.
6. The house windows are a little too bright. Tone them down so they glow through the haze.

## Sketch match · round 3 · 2026-10-30

![sketch match round 3](2026-10-30_gate_match_r3.png)

UV light off (test for H): the word still reads from the grooves alone, under the moon and the lantern.

![round 3, UV off](2026-10-30_gate_match_r3_uvoff.png)

Changes from the round 2 review (exposure -0.5 EV):
- H/I. The CROATOAN post is now real geometry (`tools/make_panel_mask.ps1` writes the mesh), not a decal:
  - Dark, deeply furrowed bark all round the post.
  - One stripped panel, about 54 x 120 cm, centred at 1.5 m and sunk 2.5 cm below the bark, so the torn bark edge shows its thickness.
  - CROATOAN cut as V-grooves about 1.1 cm deep (letters 10 cm high, each one different), with darker raw wood inside the cuts. The letters carry no colour; they read from shadow.
  - The panel and bark share the log scan's grain strip, with no repeated tiles.
- J. UV beam: three overlapping soft lobes of different widths, slightly mis-aimed, so the pool has an uneven edge. It is held up and to the left, so it rakes across the grooves. An IES profile was tried but pointed off the light's axis in UE 5.8, so it is not used.
- K. Stakes are 20-32 cm and narrower at the point. Each point is 3-4 flat axe planes at random angles (`tools/make_hewn_tips.py`). The moon now comes from behind-left, so the stake edges pick up a rim.
- M. Mud varies at large scale, so the puddles no longer repeat as evenly. Hand-placed puddles on the approach catch the gate lantern, plus mud patches, two cart ruts and more stones.
- N. Tower: two storeys with X braces, a ladder, floor beams, a railed walk, a pitched shingle roof with 80 cm overhang and a dark underside, and a lantern. Set back in the fog.
- The house is pushed back and its windows toned down. A light haze returns with distance.

Assets: only the free Quixel Megascans already in the project (Fab Standard License, free for commercial use in Unreal): Old Wooden Log x2, Old Wooden Beam, Soil Mud, Military Trenches Ground Mud, Small Stones Pack, Scatter Rocks 03/06, plus grass and weeds. The post, stake points, tower and house are our own geometry.

Still to do (round 4):
1. L: Megascans bark, roof shingles and a timber-frame building would beat the hand-built tower roof and house. Adding them needs the project owner's Fab sign-in, so it is waiting on that.
2. The N of CROATOAN sits close to the panel's right edge. Give it a few more cm of margin.
3. At this distance the letters read a little thin. Cut them deeper and wider.
4. The tower roof still reads as a plain slab through the fog.
5. The far-left foreground mud still shows some repeat.

## Full scene · 2026-10-31

![full scene](2026-10-30_gate_full_scene.png)

One complete shot of the CROATOAN gate against the sketch (`art/levels/roanoke/croatoan-gate.jpg`), rendered with Movie Render Queue: Lumen, 32 temporal samples, 64 warm-up frames, 2560x1440. Path Tracer was not used, because hardware ray tracing is off on this PC since the GPU driver crash.

In frame:
- Photographed moonlit night sky with the moon above the gate.
- Real fir trees in layered height fog.
- Palisade and gate built from a scanned trunk.
- Wet mud with puddles reflecting the gate lantern and the moon.
- Watchtower with lantern, house with two lit windows.
- The carved CROATOAN post: bark, stripped panel and V-cut letters as real geometry.

**Stand-ins and what's missing**
- **Nysa is not in the shot.** Her spot by the post is left clear. Free MetaHuman hair and clothing can't give her long dark curly hair, a fitted coat and the raised torch, so she waits for her own MetaHuman.
- The tower, house, gate lantern, hewn stake points and shingle roofs are our own simple geometry, textured with scanned wood. No free scanned versions exist.
- The moon disc and halo are drawn into the sky material; the sky behind them is the photograph.

**Assets and licences**
- Poly Haven, CC0 (public domain, no attribution needed, no AI restriction):
  - `rogland_moonlit_night`: sky
  - `fir_tree_01`: forest
  - `dead_tree_trunk`: stakes, rails, gateposts, tower legs
  - `knotted_pine_bark`: post bark
  - `brown_mud_leaves_01`: ground
  - `rock_moss_set_01`: stones
- Downloaded but not used yet (CC0): `bark_brown_02`, `brown_mud_02`, `forest_ground_04`, `dead_tree_trunk_02`, `tree_stump_01`, `Lantern_01`, `wooden_lantern_01`, `qwantani_night_puresky`.
- Quixel Megascans still in frame (Fab Standard License, marked "no AI usage"), to be replaced with CC0 next:
  - Old Wooden Log grain: stripped panel and cut wood
  - Old Wooden Beam: rope lashings, beams, house walls, shingles
  - Military Trenches mud decal: mud patches and ruts
  - Grass tufts
- Nothing bought. No Medieval Village sample.

**Differences from the sketch**
1. No Nysa (see above).
2. The light is cooler and flatter. The sketch has deeper blacks, a warmer gate lantern and a lit tower platform.
3. Tower and house read as plain shapes in the fog. They need real timber detail, or scans.
4. The stake points still read a little like arrowheads.
5. CROATOAN still looks somewhat even, and the panel is cleaner than the weathered one in the sketch.
6. The scanned Poly Haven lanterns are not yet swapped in for the gate and tower lanterns.

## Full scene · round 2 · 2026-10-31

![full scene round 2](2026-10-31_gate_full_scene_r2.png)

Sydra's six fixes after the first full scene (Movie Render Queue, Lumen, 32 samples, 2560x1440):
1. **Panel:** now the post's own wood with the bark peeled away. It's sunk 3.5 cm with a thick, torn bark edge (bigger tears, less fringe), in silver-grey weathered wood with vertical grain and cracks (Poly Haven `rough_wood`). No hard white.
2. **Letters:** cut deeper and more unevenly. Each letter has its own size, tilt and baseline, and the straight strokes have knife nicks at their ends. The cuts show darker raw wood (`fine_grained_wood`), with the violet beam raking from the upper left.
3. **Stakes:** whole scanned trunks (Poly Haven `dead_tree_trunk`), 20-32 cm, with uneven heights and leans. The axe points sit full width and start inside the trunk, and some stakes are snapped off.
4. **House:** thick thatched roof (`thatch_roof_angled`), plaster daub between the timbers (ambientCG `Plaster001`), framed windows, chimney. Both buildings sit deep in the fog.
5. **Light:** dimmer moon and sky fill, so the foreground goes darker. Warm gate lantern, tower lantern and house windows glow into the fog and onto the mud. More contrast, soft violet pool.
6. **Quixel "no AI" items:** all replaced in frame:
   - rope → ambientCG `Rope001`
   - beams → the scanned trunk
   - grass and weeds → Poly Haven `grass_medium_01`, `weed_plant_02`
   - Quixel mud decals → removed

Assets in frame (all CC0, free, nothing bought):
- Poly Haven: `rogland_moonlit_night`, `fir_tree_01`, `dead_tree_trunk`, `knotted_pine_bark`, `rough_wood`, `fine_grained_wood`, `thatch_roof_angled`, `wood_trunk_wall`, `brown_mud_leaves_01`, `rock_moss_set_01`, `grass_medium_01`, `weed_plant_02`
- ambientCG: `Rope001`, `Plaster001`

Our own geometry: the carved post, axe-cut stake points, tower, house frame, gate lantern. Nysa is out for now, as Sydra asked.

Still different from the sketch:
1. Many stake points still read a little arrow-like, and a few snapped stakes show flat round tops.
2. The tower is still a plain shape; it needs posts and a railing that read through the fog.
3. The foreground mud is very dark and empty. The sketch has lit puddles and stones close to the camera.
4. The letters are better but still a little regular. The sketch's are deeper and wider.
5. The Poly Haven lanterns are not yet swapped in for the gate and tower lanterns.

## Spec match · round 1 · 2026-10-31

![spec match round 1](2026-10-31_gate_spec_match_r1.png)

Rebuilt to `art/levels/roanoke/croatoan-gate-spec.md` and measured with `tools/measure_frame.ps1`: the spec's brightness bands plus 24 named regions, boxes as frame fractions. Run on the painting itself, the script reproduces the spec's numbers (average #272427 against the spec's #282527), so the two columns below are measured the same way.

Rendered with Movie Render Queue (Lumen, 32 samples, 2560x1440). Everything in frame is CC0 (Poly Haven, ambientCG) or our own geometry; nothing was bought. Nysa is still out, so her space (x 0.505-0.65) is clear.

**1. Brightness**

| Band | Painting | Render |
|---|---|---|
| 0-20% | 71.1% | 72.7% |
| 20-40% | 27.5% | 23.7% |
| 40-60% | 1.2% | 2.8% |
| 60-80% | 0.2% | 0.8% |
| 80-100% | 0.0% | 0.1% |
| Average | #272427 | #2B262C |

**2. Regions** (average colour; within about ±15 RGB of the painting counts as close)

| Region | Painting | Render | |
|---|---|---|---|
| Sky, top left | #494A59 | #383947 | darker |
| Sky, top centre | #454955 | #35323C | darker |
| Sky, top right | #454755 | #36292B | darker, warmer |
| Ground mist, left | #39393D | #31323F | close |
| Through the gate gap | #1B1918 | #5E4D4D | **too bright**: fog lights the firs behind the gate |
| Watchtower roof | #46454F | #524A56 | close |
| Tower lantern | #845D46 | #5B505B | missed: the lantern sits off its spot (0.19, 0.14) |
| Left palisade stakes | #202022 | #31303C | slightly bright |
| Gate lantern core | #BF8446 | #D39655 | close |
| Gate lantern halo | #372618 | #705544 | halo too wide and bright |
| Gate crossbeams | #1D1C1C | #56515E | **too bright**: fog behind them |
| Dark second post | #0E0E10 | #221F20 | slightly bright |
| Post bark | #110F0E | #050405 | slightly dark |
| Post left edge (UV) | #54426A | #6B5B63 | close, less violet |
| Stripped panel, upper | #393131 | #463F46 | close |
| Stripped panel, lower | #372C28 | #211B1B | darker |
| Panel inside UV pool | #564583 | #3C333A | **less violet** |
| Letters band | #584A7B | #615075 | close |
| Foreground mud | #262426 | #110E0F | **too dark** |
| Middle mud | #292829 | #2C2B35 | close |
| Puddle reflection | #201B17 | #1A1311 | close |
| House wall, right | #403C41 | #3F2E2D | close, warmer |
| House window | #5D4237 | #211F26 | missed: our window lands at about (0.97, 0.08), not (0.85, 0.20) |
| Right palisade stakes | #141312 | #0E0D11 | close |

**What changed from round 2:**
- Low-key overcast night: no moon, sky dimmed, overall exposure matched to the painting.
- Camera horizon at y 0.55.
- Gate lantern moved to (0.537, 0.38) with an amber core.
- Lavender UV (#7961D9) from Nysa's hand position (0.645, 0.505).
- The whole front face of the post is stripped, with CROATOAN at y 0.40-0.445 and a wide, clear T. No extra names.
- A dark full-bark second post at x 0.58-0.645.
- Left palisade leans outward 12°, with rails at the spec heights.
- Taller right palisade.
- Gate leaf and rope rails at the spec heights.
- A low mist bank on the left.
- Neutral grade (the blue shadow tint is gone).

**Still to fix (round 2):**
1. The gate gap and crossbeams are lit grey by fog, where the painting is dark. They need dark structures right behind the gate.
2. The watchtower and its lantern sit too high and left. The house window lands near the top-right corner.
3. The UV pool is too pale. The painting's is a stronger violet (#564583).
4. The foreground mud near the camera is too dark and plain. It needs wet highlights and stones.
5. The stake points still read arrow-like, and there is no barrel at the right.
