#version 440

uniform mat4 pvm;

in vec4 position;
in vec2 texCoord;

out vec2 texCoordV;

void main() {

    texCoordV = texCoord;
    gl_Position = pvm * position;
}
