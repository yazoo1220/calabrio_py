from setuptools import setup, find_packages

setup(
    name='calabrio_py',
    version='0.1.1',
    description='A Python client library for accessing the Calabrio API.',
    author='yachimat',
    author_email='podman1220@hotmail.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'aiohttp'
    ],
)
