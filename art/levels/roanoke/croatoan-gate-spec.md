# CROATOAN gate: recreation spec for the painting

Target image: `art/levels/roanoke/croatoan-gate.jpg` (1536x864, 16:9).
Annotated version: `art/levels/roanoke/croatoan-gate-annotated.jpg`.

The painting was made by an AI image model in one pass, so it has no real layers. Everything below was **measured from its pixels** (colours are region averages, positions are fractions of frame width and height, where 0,0 is top-left). Rebuild to these numbers, then measure the render the same way and compare.

---

## 1. The most important finding: exposure

The painting is a **low-key night image**. Measured brightness (luminance) of all pixels:

| Brightness band | Painting | Our round 2 render |
|---|---|---|
| 0–20% (near black) | **70.6%** | 70.4% |
| 20–40% (dark) | **27.9%** | 12.4% |
| 40–60% | 1.3% | 5.3% |
| 60–80% | 0.2% | 7.5% |
| 80–100% (near white) | **0%** | 4.3% |
| Average colour | **#282527** | #373136 |

**Rules that follow:**
- Nothing in frame may be brighter than about 40%, except the **cores** of the lanterns, the UV torch tip and small wet highlights on the mud.
- **No visible moon and no bright sky.** The sky is an overcast dark grey-blue.
- The "pale" stripped panel is **not pale**. It measures about **#3C3437**, a dark warm grey. It reads pale only because the bark around it is near black (#14110F). Contrast, not brightness.
- The image is compressed and soft: deep darks that are **not crushed to pure black**, with few hard highlights.

## 2. Measured palette

| Element | Colour | Notes |
|---|---|---|
| Sky, top left | #474957 | overcast, no moon, no stars |
| Sky, top centre | #525666 | brightest sky area |
| Sky, top right | #444653 | |
| Low ground mist, left | #515158 | rolling mist, brightness up to ~65% at its densest |
| Through the gate gap | #181615 | dark: the gap is NOT a glowing hole |
| Watchtower roof | #434048 | a silhouette, softened by fog |
| Tower lantern | #93684C | small warm point |
| Left palisade stakes | #171718 | near-black wet wood |
| Stake rim light | edges up to 90% | only thin rims catch light |
| Gate lantern core | #D29857 | amber, about 2,700 K; brightest thing in frame |
| Gate lantern halo | #332417 | small and tight: warm spill radius ~5% of frame width |
| Gate crossbeams | #212121 | |
| Post bark | #14110F | darkest wood in frame |
| Post left edge (UV spill) | #54425C | faint violet spill wraps the left edge |
| Stripped panel, upper | #3C3437 | dark warm grey |
| Stripped panel, lower | #3D312C | slightly warmer and browner |
| Panel inside UV pool | #625190 | |
| Letters band (CROATOAN) | #584A7A | letters darker than the pool around them |
| UV torch tip | #7961D9 | lavender-violet, not electric blue |
| Nysa's hair | #150F0B | very dark brown, warm highlights |
| Nysa's coat | #080809 | almost black |
| Nysa's bag | #0B0B0E | dark leather; the strap is brown |
| Foreground mud | #282526 | wet highlights up to ~87% |
| Middle mud | #1B1A19 | |
| Puddle reflection | #221C18 | reflects the lantern in warm streaks |
| House wall, right | #423735 | warm, in fog |
| House window | #6B4736 | dim warm orange, NOT bright |
| Right palisade stakes | #151312 | |

**Colour grade:** desaturated overall. Shadows lean cool blue-grey, warm light stays amber, and the UV light is lavender. Add a slight vignette and fine film grain.

## 3. Camera

- **16:9 frame.** Eye height about 1.6 m, level or tilted up slightly.
- **About 28–35 mm lens.** The horizon (where the ground meets the fog) sits at about **y 0.55**.
- **Depth of field:** the post and Nysa are sharp; the tower, house and far stakes are softened mainly by fog, with only a slight blur.

## 4. Layout (positions as fractions of the frame)

| Element | x (left–right) | y (top–bottom) | Description |
|---|---|---|---|
| Watchtower | 0.05 – 0.25 | 0.00 – 0.27 | top-left. A square timber tower with a hipped shingle roof cut off by the top of the frame, an open gallery with railing, a lantern at (0.19, 0.14) and a small figure on watch. |
| Left palisade | 0.00 – 0.40 | stake tops from 0.30 (left edge) rising to 0.10 (near the gate); bottoms at about 0.70 | recedes to the left. The stakes are bundled tightly and **lean outward about 10–15°**, held by two horizontal log rails (y ≈ 0.33 and ≈ 0.65). Sharpened tips. |
| Left gatepost pair | 0.39 – 0.46 | 0.02 – 0.80 | two tall trunks rising above the palisade. |
| Gate crossbeams | 0.42 – 0.58 | 0.15 – 0.28 | two thick round logs lashed to the posts with rope. |
| The gate | 0.40 – 0.58 | 0.25 – 0.80 | vertical stakes with rope-lashed rails at y ≈ 0.51 and ≈ 0.72 (thick rope bands, many turns). |
| Gate lantern | 0.537, 0.38 | | hung on the gate. Iron frame, amber flame. |
| Dark second post | 0.58 – 0.645 | full height | a full-bark trunk left of the CROATOAN post, almost black. |
| **CROATOAN post** | **0.645 – 0.80** | **full height, top cut off** | about 0.7 m diameter. The bark is stripped on the **whole front face** from y ≈ 0.05 to the bottom (panel x 0.65–0.76). The bark edge is thick and torn. |
| CROATOAN word | 0.655 – 0.75 | 0.40 – 0.445 | about 4.6% of frame height. Carved capitals, deep and dark. |
| UV light pool | 0.65 – 0.76 | 0.33 – 0.55 | soft, elongated vertically, brightest on the word, falling off fast. |
| **Nysa** | **0.505 – 0.65** | **head top 0.375 to the bottom of the frame** | seen from behind at a three-quarter angle, facing right toward the post. Right arm raised forward; the torch tip is at (0.645, 0.505). |
| House | 0.80 – 1.00 | 0.05 – 0.30 | behind the right palisade. Steep roof, chimney at x ≈ 0.89, y 0.05–0.12, one lit window at (0.85, 0.20). |
| Right palisade | 0.80 – 1.00 | tops 0.17 – 0.25, bottoms ≈ 0.78 | tall, separate pointed stakes, more upright. A barrel at x 0.81–0.85, y 0.67–0.80. |
| Foreground mud | 0.00 – 1.00 | 0.75 – 1.00 | wet mud and puddles with scattered stones. Puddles at x 0.30–0.50 catch the lantern. |
| Ground mist | 0.00 – 0.25 | 0.50 – 0.75 | a low mist bank drifting in from the left. |

## 5. Lighting rig

1. **Sky and ambient:** an overcast night. Dim, cool, even fill (sky colour ~#4D5060). No moon disc and no directional moon shadows, or a very weak moonlight from behind-left only to rim the stake tips.
2. **Gate lantern:** a warm point light of about 2,700 K. Small radius, falling off quickly, so it lights only the gate rails, the inside edges of the nearby posts and the puddle reflections.
3. **Tower lantern and house window:** small, dim warm points seen through fog. Not bright.
4. **UV torch:** a spotlight from Nysa's hand at (0.645, 0.505), aimed up-right at the word. Colour about #7961D9. A soft cone with an elongated pool, and a little violet spill on the left edge of the post.
5. **Fog:** dense exponential height fog plus volumetric fog. The far palisade and buildings fade to grey (#4A4B55) within about 15–20 m. A separate low mist layer sits at ground level on the left.
6. **Wetness:** everything is damp. Rough-but-wet mud gives speculars, and the puddles are mirrors.

## 6. Materials

- **Stakes:** whole trunks 20–35 cm across with dark wet bark. Uneven, hand-axed tips that show paler cut wood. Irregular heights, with gaps between some stakes.
- **Stripped panel:** the post's own wood, not an applied plate. Fine vertical grain, splits and cracks, slightly sunk below the bark, with a torn bark lip 2–3 cm thick around the edge.
- **Letters:** deep V-cuts. The painting's letters are very even capitals, but the record and our design want them hand-cut, so keep them **clearly legible** (each letter unmistakable, especially the T) with only small irregularities.
- **Rope:** thick hemp bands of many wraps on the gate and crossbeams.
- **The extra faint names in the painting** (scratched lines above and below CROATOAN) are our invention, not in John White's 1590 record. Leave them out for now.

## 7. Nysa (when she is added)

- Long, very dark brown curly hair to mid-back, with a soft warm rim from the lantern.
- An ankle-length near-black wool coat, fitted at the waist, with a belt.
- A brown leather crossbody strap over the left shoulder, and a satchel at the right hip.
- Pose: weight on the right foot, slightly turned toward the post. Right arm extended forward and up, holding a small UV torch at the word. Head tilted, studying the letters.
- She fills about 14% of the frame width and stands **in front of** the dark second post.

## 8. Checklist before pushing any render

- [ ] Brightness bands are within a few % of section 1 (run the same measurement).
- [ ] No moon, no bright sky. The sky is around #4A4D5C.
- [ ] Each region colour is within ±15 RGB of section 2.
- [ ] The post, gate, lantern, tower and house sit at the positions in section 4 (±0.02).
- [ ] CROATOAN reads clearly at a glance; the T is unmistakable.
- [ ] Put the render side by side with the painting and check it honestly before pushing.
