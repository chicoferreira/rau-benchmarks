#version 330

uniform sampler2D gPosition;
uniform sampler2D gNormal;

uniform mat4 projection;

uniform float radius;
uniform float bias;
uniform float power;
uniform uint kernelSize;

in vec2 uv;

layout (location = 0) out vec4 occlusionOut;

float hash11(float p) {
	float x = fract(p * 0.1031);
	x = x * (x + 33.33);
	x = x * (x + x);
	return fract(x);
}

vec3 hash33(vec3 p) {
	vec3 p3 = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p3 = p3 + dot(p3, p3.yxz + 33.33);
	return fract((p3.xxy + p3.yxx) * p3.zyx);
}

vec3 kernelSample(uint i, uint count) {
	float fi = float(i);
	vec3 r = hash33(vec3(fi, fi * 0.37 + 1.0, fi * 1.71 + 2.0));
	vec3 s = normalize(vec3(r.x * 2.0 - 1.0, r.y * 2.0 - 1.0, r.z + 0.05));
	s = s * hash11(fi * 2.13 + 0.5);
	float scale = fi / float(count);
	scale = mix(0.1, 1.0, scale * scale);
	return s * scale;
}

void main() {
	vec3 fragPos = texture(gPosition, uv).xyz;
	vec3 normal = normalize(texture(gNormal, uv).xyz);

	if (dot(normal, normal) < 0.5) {
		occlusionOut = vec4(1.0);
		return;
	}

	vec2 pixel = mod(floor(gl_FragCoord.xy), 4.0);
	vec3 rnd = hash33(vec3(pixel, 7.0));
	vec3 randomVec = normalize(vec3(rnd.x * 2.0 - 1.0, rnd.y * 2.0 - 1.0, 0.0));

	vec3 tangent = normalize(randomVec - normal * dot(randomVec, normal));
	vec3 bitangent = cross(normal, tangent);
	mat3 tbn = mat3(tangent, bitangent, normal);

	float occlusion = 0.0;
	for (uint i = 0u; i < kernelSize; i = i + 1u) {
		vec3 samplePos = fragPos + (tbn * kernelSample(i, kernelSize)) * radius;

		vec4 offset = projection * vec4(samplePos, 1.0);
		vec2 ndc = offset.xy / offset.w;
		vec2 sampleUv = ndc * 0.5 + 0.5;

		float sampleDepth = textureLod(gPosition, sampleUv, 0.0).z;

		float rangeCheck = smoothstep(0.0, 1.0, radius / abs(fragPos.z - sampleDepth));
		occlusion = occlusion + (sampleDepth >= samplePos.z + bias ? 1.0 : 0.0) * rangeCheck;
	}

	occlusion = 1.0 - occlusion / float(kernelSize);
	occlusion = pow(clamp(occlusion, 0.0, 1.0), power);
	occlusionOut = vec4(occlusion, occlusion, occlusion, 1.0);
}
