# Idriss El Azami El Idrissi — Hero Character Production Specification

**Priority:** P0 — first named politician asset  
**Asset ID:** `idriss_el_azami_el_idrissi`  
**Current state:** `blocked_on_reference` — no likeness sculpt is claimed complete  
**Target:** production-quality stylized 3D caricature for the Moroccan parliament satire scene  
**Disclosure:** «عمل ساخر خيالي — الشخصيات كاريكاتيرية والمواقف تمثيلية»

## Non-negotiable rule

Build a new person-specific asset from a reviewed reference sheet. Do not reuse, relabel, or cosmetically modify one of the anonymous toy-like cast models. Do not invent glasses, hairline, facial hair, face width, nose, jaw, age cues, clothing details, or accessories. Each visible likeness decision must be traceable to an image reference or explicitly marked as an artistic choice.

## Reference gate — blocks likeness sculpt

Reference candidates:
- Official House of Representatives member profile: https://www.chambredesrepresentants.ma/fr/m/delazami20162021
- Official parliamentary profile/archive article: https://www.chambredesrepresentants.ma/ar/أخبار/الدكتور-ادريس-الأزمي-الادريسي-رئيسا-لفريق-العدالة-والتنمية-بمجلس-النواب

Before using any image as a texture, embedded reference, or redistributable source:
- Record the exact image URL (not just the page URL), date accessed, photographer/credit, and reuse/license status.
- Confirm redistribution rights or obtain permission. A public page is not proof of a reusable license.
- Prefer clear, well-lit frontal and three-quarter portraits; add a profile view if available.
- Preserve the original references and record checksums in the project source directory.
- If rights remain unknown, keep the profile `blocked_on_reference`; do not bundle the portrait or claim likeness accuracy.

## Character build — new asset, not a patch

### 1. Reference sheet and proportion study
- Assemble the approved portrait sheet and annotate visible landmarks: head silhouette, forehead/hairline, brow line, eye spacing, nose bridge/tip, cheek volume, mouth width, chin, jaw, ears, neck, and visible eyewear/facial hair if present.
- Establish a neutral, unexaggerated likeness blockout before caricature.
- Record uncertain or occluded features rather than guessing them.

### 2. Dedicated head sculpt
- Create a unique head mesh with a deliberate silhouette and facial planes; avoid primitive-sphere face construction as the final result.
- Shape forehead, temples, cheekbones, eyelids, nose bridge and nostrils, philtrum, lips, nasolabial region, chin, jawline, and ears as connected anatomy.
- Use controlled stylization: modest exaggeration only after reference landmarks are matched.
- Create separate, well-fitted hair/eyewear/facial-hair geometry only where the source supports it.
- Inspect the silhouette and likeness at front, three-quarter, and profile angles under neutral lighting.

### 3. Full body and wardrobe
- Build a proportionally coherent adult body with shoulder, chest, waist, neck, hands, and feet—not a floating head on a generic toy torso.
- Tailor the suit jacket, lapels, collar, shirt, tie if visible, sleeves, cuffs, trousers, shoes, and seams to the selected reference/context. Avoid party-color coding as a substitute for likeness.
- Include believable jacket thickness, layered fabric edges, folds at elbows/waist/knees, stitching, buttons, and subtle fabric roughness.
- Model hands with palm, thumb, and individually readable fingers; verify contact with props and desk/microphone when staged.
- Add only source-supported personal accessories.

### 4. Materials and grooming
- Use physically based skin, hair, fabric, leather, and metal materials with controlled roughness and realistic scale.
- Skin must not look like glossy plastic; hair must read as groomed strands/clumps or a carefully sculpted hair mass, not a featureless cap.
- Validate color under neutral key/fill/rim lighting and in the final chamber lighting.
- Avoid over-sharpened pores or noisy texture that disappears at the intended camera distance.

### 5. Rig and acting readiness
- Use a clean hierarchy or armature for pelvis, spine, chest, neck, head, clavicles, upper/lower arms, wrists, fingers, thighs, shins, and feet.
- Add facial controls or shape keys for blink, brow, jaw, mouth-open, smile/frown, and speech-ready mouth poses after neutral sculpt approval.
- Test speaking, listening, pointing, seated posture, standing posture, and hand-to-desk contact without mesh intersections.
- Keep satire expressions adjustable and reversible; do not bake a single exaggerated expression into the neutral face.

### 6. Rendering and delivery
- Render neutral front, three-quarter, and profile views at matching scale, camera height, and lighting; include a full-body view and a face close-up.
- Produce a side-by-side comparison against the approved source image for human review.
- Inspect the actual PNGs for silhouette, face, material, clipping, and hand defects; a successful Blender process or GLB export is not visual acceptance.
- Export GLB with named meshes/materials, correct origin/scale, no missing textures, and a manifest containing source metadata, rights status, sculpt status, render paths, and review status.
- Test the GLB in the target parliament scene for scale, floor/chair contact, material fidelity, and animation deformation.

## Acceptance checklist

- [ ] Exact portrait source(s), access date, credit, and reuse rights recorded.
- [ ] Front/three-quarter/profile references reviewed.
- [ ] Unique head sculpt approved as recognizably based on the reference.
- [ ] Full body, hands, wardrobe, shoes, and supported accessories complete.
- [ ] PBR materials and final lighting visually reviewed.
- [ ] Front, three-quarter, profile, full-body, and close-up renders exist.
- [ ] Human reviewer explicitly approves the likeness; never infer this from CI.
- [ ] Rig/face controls and pose tests pass without visible intersections.
- [ ] GLB imports and renders correctly in the parliament scene.
- [ ] Satire disclosure appears in the video/scene delivery.

Until the reference and rights gates are satisfied, the honest status remains `blocked_on_reference`. This document is a production specification, not evidence that the character has already been sculpted.
