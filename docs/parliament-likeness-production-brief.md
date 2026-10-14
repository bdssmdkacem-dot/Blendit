# Reference-led caricature production brief

**Status:** production specification; no named 3D likeness is approved yet.
**First batch:** Ahmed Touizi and Idriss El Azami El Idrissi.
**Related tracker:** [Issue #1](https://github.com/bdssmdkacem-dot/Blendit/issues/1)

## Source collection

### Ahmed Touizi
- Official House of Representatives speaker profile: https://www.chambredesrepresentants.ma/fr/group/101
- Official election announcement: https://www.chambredesrepresentants.ma/fr/ElectionTouizi?q=ar%2FElectionTouizi
- The profile page establishes identity/context; choose a clear portrait from the page and record its exact image URL, capture date, and reuse/credit terms before packaging it.

### Idriss El Azami El Idrissi
- Official parliamentary member profile: https://www.chambredesrepresentants.ma/fr/m/delazami20162021
- Official parliamentary member index: https://www.chambredesrepresentants.ma/fr/%D8%AF%D9%84%D9%8A%D9%84-%D8%A3%D8%B9%D8%B6%D8%A7%D8%A1-%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8/all?page=124&q=fr%2F%D8%AF%D9%84%D9%8A%D9%84-%D8%A3%D8%B9%D8%B6%D8%A7%D8%A1-%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%2Fall
- The member profile establishes identity/context; select a usable portrait and record its exact image URL, capture date, and reuse/credit terms before packaging it.

## Required modeling method

1. Build a reference sheet per person from clear frontal and three-quarter portraits where available. Do not infer unpictured details.
2. Sculpt a unique head silhouette and facial landmarks from the reference. Do not use the current generic archetype head as the starting mesh for the named likeness.
3. Use artistic caricature exaggeration only after the base identity landmarks are established. Exaggeration should strengthen recognition, not erase it.
4. Create a person-specific body silhouette, hair, eyewear/facial hair (only if supported by reference), suit fit, collar, and accessories.
5. Render a neutral likeness study first. Only after it passes reference comparison, create exaggerated expressions and animation poses.
6. Render front, three-quarter, and profile views with consistent camera, scale, and lighting; add side-by-side reference comparison panels to the workflow artifact.
7. Export GLB only after preview review. Include source metadata, profile ID, model status, and preview paths in a manifest.

## Hard rejection checklist

Reject the model if any of these apply:
- It looks like the same generic face used for another politician.
- Identity depends only on a name label, party color, enlarged head, or suit color.
- Hairline, glasses, facial hair, face width, nose, jaw, age impression, or other visible features contradict the reference.
- Any required view is missing, clipped, too small, or poorly lit for comparison.
- No exact reference URL or reuse/credit status is recorded.
- The only evidence is a successful build, node count, or material count.

A model with missing or inadequate references must be marked `blocked_on_reference`, not approved.

## Delivery gates

- [ ] Reference image(s), source URL(s), date, and credit/license status recorded.
- [ ] Unique high-quality sculpt created; not derived by relabelling generic archetypes.
- [ ] Front, three-quarter, and profile renders exist.
- [ ] Reference comparison reviewed by a human.
- [ ] GLB imports into the parliament scene with correct scale, materials, and floor/chair contact.
- [ ] Rig and expression tests pass after sculpt approval.
- [ ] Satire disclosure shown: «عمل ساخر خيالي — الشخصيات كاريكاتيرية والمواقف تمثيلية».

## First implementation milestone

Complete the reference sheets and neutral likeness studies for Touizi and El Azami before modeling the rest of the cast. Do not batch-generate ten low-fidelity characters; produce two distinguishable, reviewable hero assets first.
