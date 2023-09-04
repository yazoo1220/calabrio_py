from setuptools import setup, find_packages

setup(
    name='calabrio_py',
    version='0.1.7',
    description='A Python client library for accessing the Calabrio API.',
    author='yachimat',
    author_email='podman1220@hotmail.com',
    packages=find_packages(),
    long_description='''
    A Python client library for accessing the Calabrio API.

    This library provides convenient methods for interacting with the Calabrio API,
    making it easy to retrieve data and perform actions using Python code.
    ''',
    long_description_content_type='text/x-rst',
    install_requires=[
        'requests>=2.28.1',
        'aiohttp>=3.8.3',
        'python-dateutil>=2.8.2'
    ],
)
