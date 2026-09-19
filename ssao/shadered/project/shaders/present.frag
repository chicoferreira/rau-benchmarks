#version 330

uniform sampler2D litMap;

in vec2 uv;

layout (location = 0) out vec4 fragColor;

void main() {
	fragColor = texture(litMap, uv);
}
