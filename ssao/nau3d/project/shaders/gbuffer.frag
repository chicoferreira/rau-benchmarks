#version 330

in vec3 viewPosition;
in vec3 viewNormal;

layout (location = 0) out vec4 gPosition;
layout (location = 1) out vec4 gNormal;

void main() {
	gPosition = vec4(viewPosition, 1.0);
	gNormal = vec4(normalize(viewNormal), 1.0);
}
