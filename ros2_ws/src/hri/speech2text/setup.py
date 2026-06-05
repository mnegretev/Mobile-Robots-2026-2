from setuptools import find_packages, setup

package_name = 'speech2text'

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
    maintainer='emmanueldom',
    maintainer_email='emmanueldom007@outlook.com',
    description='Speech-to-text converter using Faster Whisper',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'faster_whisper_asr = speech2text.faster_whisper_asr:main',
        ],
    },
)
