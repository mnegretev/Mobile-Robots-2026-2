#include <mujoco/mujoco.h>
#include <GLFW/glfw3.h>
#include <iostream>

int main() {
    // Activar MuJoCo
    if (!mj_activate("~/.mujoco/mjkey.txt")) {
        std::cerr << "Error activating MuJoCo" << std::endl;
        return 1;
    }

    // Cargar tu modelo XML
    const char* filename = "install/humanoid_simul/share/humanoid_simul/models/booster_t1/t1.xml";
    mjModel* m = mj_loadXML(filename, NULL, NULL, 0);
    if (!m) {
        std::cerr << "Error loading model: " << filename << std::endl;
        return 1;
    }

    std::cout << "Modelo cargado correctamente!" << std::endl;

    // Limpiar
    mj_deleteModel(m);
    mj_deactivate();
    return 0;
}
