# Satirical Parliament Video — Asset and Production Plan

## Creative target
Create a clearly labelled political-satire video staged inside a reference-led Moroccan parliamentary chamber. The cast should include recognizable, stylized caricatures of real public political figures, guided by verified public portraits, alongside generic background members. The scenes and dialogue remain fictional satire; they must not be presented as documentary evidence or as verified quotations/actions.

## Character casting
The prioritized named cast, role notes, source register and likeness acceptance checklist live in [parliament-real-figure-caricature-roster.md](parliament-real-figure-caricature-roster.md).

**Do not call the current six generic models likenesses.** The first-pass generator creates anonymous archetypes only. Each named figure needs a reference sheet, a distinct facial sculpt, preview renders from multiple angles, and visual review before being approved.

## Asset inventory
- Environment: parliament_domed_chamber.glb and optional parliament_exterior.glb from the architecture workflow.
- Named cast: follow the prioritized roster, beginning with Ahmed Touizi and Idriss El Azami El Idrissi for the House-presidency debate scene, while keeping Mohamed Ould Errachid for a clearly identified House of Councillors scene or period.
- Background cast: retain the six existing generic archetypes for non-identifiable chamber members.
- Props to add: desk nameplates, papers, folders, microphones, phones, water glasses, clocks, voting buttons, and a podium.
- Animation set: idle/listen, talk with hand gestures, interrupt, glance at phone, doze/head-nod, shuffle papers, shrug, sarcastic applause, and group reaction.
- Cinematic shots: close-up, speaker medium shot, wide chamber shot, reaction shot, empty-seat insert, and establishing exterior shot.

## Current character generator status
The first pass exports six separate generic GLBs and one preview PNG per character, with a manifest. Body/head/arm/hand/face pieces are separate named objects to make a later rigging pass easier. The models are not armature-rigged and are not likeness-ready. Structural workflow checks only confirm basic file integrity, node/material counts, and preview image presence/dimensions.

## Acceptance gates
1. Run the architecture and character workflows successfully.
2. Collect a source-checked reference sheet for each named figure; record source URL, access date and usage/license status.
3. Inspect front, three-quarter and profile renders against the reference. Reject generic faces with only renamed files, clipped faces, awkward silhouettes, intersecting limbs, hidden props, and poor framing.
4. Import the chamber and at least two characters into the intended renderer/engine. Check scale, orientation, materials, transparency, shadows, and floor/seating contact.
5. Add armatures and test face/eye/jaw controls plus shoulder, elbow, wrist and hand deformation.
6. Stage a 10–20 second animatic with wide, medium, and reaction shots; evaluate whether the satire reads without dialogue alone.
7. Add an Arabic on-screen disclosure: "عمل ساخر خيالي — الشخصيات كاريكاتيرية والمواقف تمثيلية".
8. Do not label the pack finished until the rendered test scene and animatic have been visually reviewed.

## Tone and representation
Political satire of public figures is intentional. Keep the exaggeration clearly artistic and scenes visibly fictional. Do not invent quotations, votes, misconduct or events and present them as factual. Avoid fake news lower-thirds or edits that could make the animation appear to be authentic footage.
