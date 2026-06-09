from setuptools import setup
import os
from glob import glob

package_name = 'speech2text_pro'

setup(
    name=package_name,
    version='0.1.0',
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
    description='Speech recognition node with TTS mute support.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'faster_whisper_asr = speech2text_pro.faster_whisper_asr:main',
        ],
    },
)
