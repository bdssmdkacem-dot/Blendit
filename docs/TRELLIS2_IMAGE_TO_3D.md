# TRELLIS.2 image-to-3D workflow in Blendit

Blendit now provides an Android entry point to the official TRELLIS.2 Hugging Face Space. This is an external hand-off, not an embedded inference engine: Blendit does not claim the remote model is running locally or that a public GPU endpoint is always free.

Official entry point: https://huggingface.co/spaces/microsoft/TRELLIS.2

## Current workflow

1. In the Android app, choose a source image from the phone gallery; Blendit displays a local preview and rejects files larger than 20 MiB.
2. Open the official TRELLIS.2 Space and manually select the same image in its interface. Blendit does not silently upload personal photos.
3. Generate the model, inspect the hosted preview, and export/download GLB if the Space currently supports it.
4. Treat the downloaded GLB as a candidate asset, not approved production art. The app does not yet automatically import the remote result into its local asset library.
5. Import it into Blender and Godot to inspect scale, orientation, materials, topology, silhouette, and collisions before shipping.

## Cost and hardware

TRELLIS.2 is a large GPU model. Local inference generally needs a compatible NVIDIA GPU with substantial VRAM (the upstream project specifies at least 24 GB). The public hosted demo's availability, queue, and free quota are controlled by its host and can change. Blendit therefore labels this as a hosted workflow rather than promising unlimited free generation.

## Privacy

The image is uploaded to the hosting service when the user chooses it in the remote interface. Do not upload private or sensitive images. Review the host's current data and retention notices before use.

## Next integration milestone

Replace the external hand-off only after a stable inference endpoint is selected. Remaining integration work is a secure upload/progress/error flow, a generation job ID, GLB download into the Blendit library, file-size and GLB-header validation, and a preview/import check. Never place a private Hugging Face token in the Android app; use a user-controlled local GPU service or a secured server-side credential. Do not mark generated assets production-ready based on successful generation alone.
