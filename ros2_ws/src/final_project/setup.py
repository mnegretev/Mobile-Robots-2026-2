from setuptools import setup

package_name = 'final_project'

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
    maintainer='Robot Project',
    maintainer_email='robot@local',
    description='Integración de ASR, LLM Planning y control de robot doméstico',
    license='LGPL-3.0-only',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'faster_whisper_asr = final_project.faster_whisper_asr:main',
            'ollama_planning = final_project.ollama_planning:main',
        ],
    },
)
