#version 330

uniform sampler2D ssaoInput;

in vec2 uv;

layout (location = 0) out vec4 blurred;

void main() {
	vec2 texelSize = 1.0 / vec2(textureSize(ssaoInput, 0));
	float result = 0.0;
	for (int x = -2; x < 2; x = x + 1) {
		for (int y = -2; y < 2; y = y + 1) {
			vec2 offset = vec2(float(x), float(y)) * texelSize;
			result = result + texture(ssaoInput, uv + offset).r;
		}
	}
	result = result / 16.0;
	blurred = vec4(result, result, result, 1.0);
}
