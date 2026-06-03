from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'path_follower'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='thedoctor',
    maintainer_email='marco.negrete@ingenieria.unam.edu',
    description='TODO: Package description',
    license='LGPL-3.0-only',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pure_pursuit = path_follower.pure_pursuit:main',
            'pure_pursuit_solved = path_follower.pure_pursuit_solved:main',
            'stanley = path_follower.stanley:main',
            'stanley_solved = path_follower.stanley_solved:main',
            'route_selector = path_follower.route_selector:main',
            'voice_faster_whisper = path_follower.voice_faster_whisper:main',
            'sequence_interpreter = path_follower.sequence_interpreter:main',
            'arm_motion_executor = path_follower.arm_motion_executor:main',
            'llm_task_planner = path_follower.llm_task_planner:main',
        ],
    },
)
