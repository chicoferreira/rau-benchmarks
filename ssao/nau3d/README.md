Worth flagging:

- Gamma. Rau's final target is Rgba8UnormSrgb, so the hardware encodes the write. Nau's GL texture formats include no sRGB variant and it never enables GL_FRAMEBUFFER_SRGB, so lighting.frag ends with pow(colour, 1/2.2). Without it the Nau image is visibly darker; the cost is negligible.
- Room normals. Rau generates the cube in the vertex shader and negates hardcoded face normals; Nau uses the built-in BOX with real normal attributes, so room.vert negates NormalMatrix * normal. Both materials carry a noCull state to match Rau's cull_mode: None.
- V-sync. A toggle does not exist and is always off.
