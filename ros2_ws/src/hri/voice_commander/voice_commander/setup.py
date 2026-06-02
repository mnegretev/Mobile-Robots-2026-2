from setuptools import find_packages, setup
import os
from glob import glob

package_name = "voice_commander"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Alejandre Mercado",
    maintainer_email="alumno@fi.unam.mx",
    description="Navegación por comandos de voz - Robots Móviles 2026-2",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "voice_commander_node = voice_commander.voice_commander_node:main",
            "faster_whisper_asr   = voice_commander.faster_whisper_asr:main",
        ],
    },
)
