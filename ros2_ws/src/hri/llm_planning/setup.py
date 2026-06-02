from setuptools import find_packages, setup
import os

package_name = 'llm_planning'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), os.path.join('config', 'Prompts.txt')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='emmanueldom',
    maintainer_email='emmanueldom007@outlook.com',
    description='TODO: Package description',
    license='LPGPL-3.0-only',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ollama_planning_node = llm_planning.ollama_planning:main',
        ],
    },
)
