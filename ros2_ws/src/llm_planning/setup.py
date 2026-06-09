from setuptools import setup

package_name = 'llm_planning'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='juan',
    maintainer_email='jg3606739@gmail.com',
    description='LLM Planning package for robot instruction processing',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ollama_planning = llm_planning.ollama_planning:main',
            'robot_planner = llm_planning.robot_planner:main',
        ],
    },
)
