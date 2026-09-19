#version 330

in vec4 position;
in vec4 texCoord0;

out vec2 uv;

void main() {
	uv = texCoord0.xy;
	gl_Position = position;
}
