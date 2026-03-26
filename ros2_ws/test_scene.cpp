#include <mujoco/mujoco.h>
#include <GLFW/glfw3.h>
#include <iostream>

int main() {
    if (mj_activate("~/.mujoco/mjkey.txt") != 1) return 1;

    if (!glfwInit()) return 1;
    GLFWwindow* window = glfwCreateWindow(800, 600, "MuJoCo Scene", nullptr, nullptr);
    if (!window) return 1;
    glfwMakeContextCurrent(window);

    mjModel* m = mj_loadXML("scene.xml", nullptr, nullptr, 0);
    if (!m) return 1;
    mjData* d = mj_makeData(m);

    mjvScene sc;
    mjv_defaultScene(&sc);
    mjrContext con;
    mjr_defaultContext(&con);

    while (!glfwWindowShouldClose(window)) {
        mj_step(m, d);

        int w, h;
        glfwGetFramebufferSize(window, &w, &h);
        glViewport(0, 0, w, h);
        glClear(GL_COLOR_BUFFER_BIT);

        mjv_updateScene(m, d, &sc, nullptr);
        mjr_render(w, h, &sc, &con);

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    mj_deleteData(d);
    mj_deleteModel(m);
    glfwDestroyWindow(window);
    glfwTerminate();
    mj_deactivate();
    return 0;
}
