#version 440
uniform vec4 color1 = vec4(0.0, 0.0, 1.0, 1.0);
uniform vec4 color2 = vec4(1.0, 1.0, 0.5, 1.0);
in vec2 texCoordV;

out vec4 colorOut;

void main() {

    vec2 t = texCoordV * 8.0;

    float f = fract(t.s);

    if (f < 0.4)
        colorOut = color1;
    else if (f < 0.5)
        colorOut = mix(color1, color2, (f - 0.4)* 10.0) ;
    else if (f < 0.9)
        colorOut = color2;
    else
        colorOut = mix(color2, color1, (f - 0.9) * 10.0);
}
