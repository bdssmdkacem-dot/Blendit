# TRELLIS.2 image-to-3D workflow in Blendit

Blendit now provides an Android entry point to the TRELLIS.2 image-to-3D demo. This first integration is intentionally a safe external hand-off: it does not pretend the remote model is running locally or that a public GPU endpoint is always free.

## Current workflow

1. Open **تحويل صورة إلى مجسم 3D — TRELLIS.2** from the Android app.
2. Upload a clear image of one foreground object. A transparent PNG is preferred.
3. Generate the model, inspect the turntable preview, then use **Extract GLB**.
4. Keep the downloaded GLB as a candidate asset, not automatically approved production art.
5. Import it into Blender and Godot to inspect scale, orientation, materials, topology, silhouette, and collisions before shipping.

## Cost and hardware

TRELLIS.2 is a large GPU model. Local inference generally needs a compatible NVIDIA GPU with substantial VRAM (the upstream project specifies at least 24 GB). The public hosted demo's availability, queue, and free quota are controlled by its host and can change. Blendit therefore labels this as a hosted workflow rather than promising unlimited free generation.

## Privacy

The image is uploaded to the hosting service when the user chooses it in the remote interface. Do not upload private or sensitive images. Review the host's current data and retention notices before use.

## Next integration milestone

Replace the external hand-off only after a stable inference endpoint is selected. The native flow should then add image selection, upload/progress/error states, a generation job ID, GLB download, file-size and GLB-header validation, and a preview/import check. Never place a private Hugging Face token in the Android app; use a user-controlled local GPU service or a secured server-side credential. Do not mark generated assets production-ready based on successful generation alone.
