cmake_minimum_required(VERSION 3.8)
project(humanoid_simul)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# ### FIX START: Configuración explicita de MuJoCo ###
# Leemos la variable de entorno que pusimos en el .bashrc
set(MUJOCO_ROOT $ENV{MUJOCO_DIR})

if(NOT MUJOCO_ROOT)
  message(WARNING "MUJOCO_DIR no esta definida. Intentando ruta por defecto...")
  set(MUJOCO_ROOT "$ENV{HOME}/mujoco") # Fallback por si acaso
endif()

message(STATUS "Usando MuJoCo en: ${MUJOCO_ROOT}")

# Agregamos la ruta de los headers (para que encuentre mujoco/mujoco.h)
include_directories(${MUJOCO_ROOT}/include)

# Buscamos la librería física (libmujoco.so)
find_library(MUJOCO_LIB NAMES mujoco PATHS ${MUJOCO_ROOT}/lib NO_DEFAULT_PATH)
if(NOT MUJOCO_LIB)
    message(FATAL_ERROR "No se encontro libmujoco.so en ${MUJOCO_ROOT}/lib")
endif()
# ### FIX END ###

# --- Target 1: humanoid_simul ---
add_executable(humanoid_simul src/humanoid_simul.cpp)
target_include_directories(humanoid_simul PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>)
target_compile_features(humanoid_simul PUBLIC c_std_99 cxx_std_17)

# ### FIX: Enlazamos con la libreria encontrada (MUJOCO_LIB) en vez de solo "mujoco"
target_link_libraries(humanoid_simul ${MUJOCO_LIB} glfw) 

ament_target_dependencies(
  humanoid_simul
  "rclcpp"
  "std_msgs"
  "geometry_msgs"
  "sensor_msgs"
)

# --- Target 2: basic_mujoco ---
add_executable(basic_mujoco src/basic_mujoco.cpp)
target_include_directories(basic_mujoco PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>)
target_compile_features(basic_mujoco PUBLIC c_std_99 cxx_std_17)

# ### FIX: Enlazamos con la libreria encontrada
target_link_libraries(basic_mujoco ${MUJOCO_LIB} glfw)

install (
  DIRECTORY launch models
  DESTINATION share/${PROJECT_NAME}
)

install(TARGETS humanoid_simul
  DESTINATION lib/${PROJECT_NAME})

install(TARGETS basic_mujoco
  DESTINATION lib/${PROJECT_NAME})

ament_package()