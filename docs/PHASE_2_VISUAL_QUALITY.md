# Blendit Phase 2 — Visual Quality Gate

Status: **active; do not mark complete until every gate below passes**.

This phase improves the existing procedural Blender generator. TRELLIS.2 must not be reintroduced as part of this phase.

## Scope and acceptance criteria

1. **Shape and proportions**
   - Review every generated asset at close, medium, and game-camera distance.
   - Check silhouette readability, believable proportions, intersections, floating parts, flipped faces, and unintended gaps.
   - Keep individual exports centered at a predictable local origin and at consistent real-world/game scale.
2. **Materials and surface detail**
   - Give every visible mesh primitive a valid material assignment.
   - Use coherent physically based material values; vary roughness/metalness by material type.
   - Check that color, metallic, roughness, alpha, and any texture references survive GLB export and Godot import.
   - Do not claim a texture exists merely because a material has a name or color.
3. **Lighting and presentation**
   - Produce readable silhouettes, controlled highlights, contact shadows, and non-clipped highlights.
   - Review both the Blender preview and the Godot-imported scene; engine lighting is the final authority for exported assets.
4. **Coherent art styles**
   - Define named, repeatable style presets with consistent palettes, material response, bevel/detail density, and lighting.
   - Expose only controls that the current generator actually implements. A preset must be deterministic and must not silently change geometry in unrelated ways.
5. **Per-asset visual comparisons**
   - Generate a clearly named review image for each asset using a consistent camera, neutral background, and lighting.
   - Include a useful close-up plus an in-context Godot view where practical.
   - Package the images with the manifest and technical audit report for review on a phone.
6. **Reject invalid outputs**
   - Fail the pipeline on missing/empty files, invalid GLB headers, empty meshes, unusable triangle data, invalid material references, malformed material values, or failed engine import.
   - Technical checks are necessary but do not prove artistic quality. A human visual review remains required.
7. **Evidence and reproducibility**
   - Store the generator, audit, tests, review checklist, and workflow changes in GitHub.
   - Run unit tests, regenerate the pack from a clean Blender scene, audit every standalone GLB, import all assets in Godot 4, and publish review artifacts.
   - Record failures rather than suppressing them. Do not describe a build as visually approved solely because CI passed.

## Review checklist (repeat for every asset)

- [ ] Silhouette and proportions read clearly at phone-screen size.
- [ ] No missing, detached, floating, buried, or visibly intersecting parts unless intentional.
- [ ] No blank/black/pink materials or unexpected material loss after Godot import.
- [ ] Surface response matches the named material (wood, stone, metal, glass, foliage, etc.).
- [ ] Highlights and shadows reveal form without washing out detail.
- [ ] Asset scale, orientation, pivot, and local origin are practical for a game.
- [ ] Standalone GLB opens in Godot 4 and has useful bounds.
- [ ] Per-asset comparison image exists and is included in the review artifact.
- [ ] Approved visually on a phone, or explicitly marked **needs revision**.

## Exit criteria

Phase 2 is complete only when every asset in the generated pack passes technical and Godot checks, per-asset comparisons are published, the style controls are implemented and tested, and the visual checklist has been reviewed on a phone. Until then, status remains **in progress**.
