#version 330

in vec4 position;
in vec3 normal;

uniform mat4 PVM;
uniform mat4 VM;
uniform mat3 NormalMatrix;

out vec3 viewPosition;
out vec3 viewNormal;

void main() {
	viewPosition = vec3(VM * position);
	viewNormal = -(NormalMatrix * normal);
	gl_Position = PVM * position;
}
