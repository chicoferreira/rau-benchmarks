#version 330

layout (location = 0) in vec2 pos;
layout (location = 1) in vec2 texCoord;

out vec2 uv;

void main() {
	uv = texCoord;
	gl_Position = vec4(pos, 0.0, 1.0);
}
