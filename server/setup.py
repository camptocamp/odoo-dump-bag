from setuptools import find_packages, setup

setup(
    name="dumpbagserver",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["flask", "awscli", "Flask-WTF"],
    setup_requires=["pytest-runner"],
    tests_requires=["pytest", "mock"],
)
