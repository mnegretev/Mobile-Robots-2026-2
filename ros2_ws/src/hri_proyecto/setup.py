from setuptools import setup
import os
from glob import glob

package_name = 'hri_proyecto'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ducky_ubuntu',
    maintainer_email='ducky_ubuntu@todo.com',
    description='Voice-controlled robot brain using Ollama LLM for intent parsing.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'brain = hri_proyecto.brain:main',
        ],
    },
)
