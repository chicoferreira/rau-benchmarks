#version 330

layout (location = 0) in vec3 pos;
layout (location = 1) in vec3 normal;

uniform mat4 matProjection;
uniform mat4 matView;
uniform mat4 matGeo;

out vec3 viewPosition;
out vec3 viewNormal;

void main() {
	vec4 world = matGeo * vec4(pos, 1.0);
	viewPosition = vec3(matView * world);
	viewNormal = -vec3(matView * matGeo * vec4(normal, 0.0));
	gl_Position = matProjection * matView * world;
}
