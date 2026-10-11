# Asset Reference Acceptance — Phase 2

The two reference images supplied during the Blendit visual-quality review define acceptance targets for the procedural assets. They are visual targets, not merely inspiration.

## Crystal cluster reference

Target characteristics:
- Several translucent turquoise/cyan crystal shards in one coherent cluster.
- Strong variation in shard height, width, tilt, and silhouette; avoid repeated identical cones.
- Faceted surfaces with readable internal color variation and crisp highlights.
- A single irregular, dark rocky base with visible surface relief.
- Small secondary shards fill gaps around the large central shard.
- The cluster must remain readable at gameplay camera distance and under neutral studio lighting.

Reject the asset if it looks like simple opaque cones, has uniform shard sizes, has a flat featureless base, or loses its silhouette in the Godot import.

## Evergreen tree reference

Target characteristics:
- A visible, continuous brown trunk.
- Numerous overlapping, leaf-like boughs arranged around the trunk, with varied lengths and angles.
- Branch tiers become smaller toward the crown but do not read as a stack of separate cones.
- Rich but controlled green variation, with light/shadow separation between overlapping boughs.
- An irregular natural silhouette when viewed from the front and oblique angles.
- No gaps that make the tree look like disconnected geometric rings.

Reject the asset if its crown is only a few stacked cones, lower branches are not readable, or the silhouette remains mechanically repetitive.

## Required review loop

For every change to either asset:
1. Generate the asset using the Blender pipeline.
2. Inspect its dedicated preview image, not only the full asset-pack montage.
3. Confirm the GLB imports into Godot 4 and inspect the in-engine playtest image.
4. Compare silhouette, proportions, material readability, and detail density against the supplied reference.
5. Keep the generated preview and quality report with the CI visual-review artifact.

A green CI result proves the pipeline completed; it does **not** by itself mean the asset has met the visual target.

## Current review note

The pine-tree revision in workflow run 55 completes successfully, but the dedicated preview still reads as a small stack of broad, faceted cone tiers. It is a functional intermediate improvement, not yet a match for the layered leaf-like branches in the reference. Continue refining branch geometry and inspect a new preview before marking the tree accepted.

Workflow run 55: https://github.com/bdssmdkacem-dot/Blendit/actions/runs/38138585531
