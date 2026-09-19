#version 330

uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D ssao;

uniform mat4 view;

uniform vec4 lightPosition;
uniform vec4 lightColor;
uniform float lightLinear;
uniform float lightQuadratic;

const vec3 ALBEDO = vec3(0.95, 0.95, 0.95);
const vec3 BACKGROUND = vec3(0.05, 0.06, 0.08);

in vec2 uv;

layout (location = 0) out vec4 fragColor;

void main() {
	vec3 fragPos = texture(gPosition, uv).xyz;
	vec3 normal = texture(gNormal, uv).xyz;
	float occlusion = texture(ssao, uv).r;

	if (dot(normal, normal) < 0.5) {
		fragColor = vec4(pow(BACKGROUND, vec3(1.0 / 2.2)), 1.0);
		return;
	}

	vec3 n = normalize(normal);
	vec3 lightViewPos = vec3(view * vec4(lightPosition.xyz, 1.0));

	vec3 ambient = ALBEDO * 0.3 * occlusion;

	vec3 toLight = lightViewPos - fragPos;
	float dist = length(toLight);
	vec3 lightDir = toLight / dist;

	float diff = max(dot(n, lightDir), 0.0);
	vec3 diffuse = ALBEDO * diff * lightColor.rgb;

	vec3 viewDir = normalize(-fragPos);
	vec3 halfway = normalize(lightDir + viewDir);
	float spec = pow(max(dot(n, halfway), 0.0), 16.0);
	vec3 specular = lightColor.rgb * spec * 0.2;

	float attenuation = 1.0 / (1.0 + lightLinear * dist + lightQuadratic * dist * dist);

	vec3 lighting = ambient + (diffuse + specular) * attenuation;
	fragColor = vec4(pow(lighting, vec3(1.0 / 2.2)), 1.0);
}
