# SSAO in Nau3D

The deviations from the Rau project:

- Gamma. Rau's final target is `Rgba8UnormSrgb`, so the hardware encodes the write. Nau3D's GL texture formats include no sRGB variant and it never enables `GL_FRAMEBUFFER_SRGB`, so `lighting.frag` ends with `pow(colour, 1/2.2)`. Without it the image is visibly darker, and the cost is negligible.
- Room normals. Rau generates the cube in the vertex shader and negates hardcoded face normals. Nau3D uses the built-in `BOX` with real normal attributes, so `room.vert` negates `NormalMatrix * normal`. Both materials carry a `noCull` state to match Rau's `cull_mode: None`.
- V-sync. Nau3D has no setting for it and it is always off.
