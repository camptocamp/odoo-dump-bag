from setuptools import setup, find_packages

setup(
    name='dumpbagserver',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'awscli',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_requires=[
        'pytest',
        'mock',
    ],
)
