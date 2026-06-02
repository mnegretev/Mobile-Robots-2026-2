from setuptools import find_packages, setup

package_name = 'voice_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jalejandro',
    maintainer_email='venomweblol@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
   entry_points={
        'console_scripts': [
            'command_interpreter = voice_control.command_interpreter:main',
            'speech_recognition_node = voice_control.speech_recognition_node:main',
            'speech_synthesis_node = voice_control.speech_synthesis_node:main',
            'keyboard_backup = voice_control.keyboard_backup:main',
        ],
    },
)
