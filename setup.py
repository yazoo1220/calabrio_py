from setuptools import setup, find_packages

setup(
    name='calabrio_py',
    version='0.1.3',
    description='A Python client library for accessing the Calabrio API.',
    author='yachimat',
    author_email='podman1220@hotmail.com',
    packages=find_packages(),
    long_description_content_type='text/x-rst',
    install_requires=[
        'requests>=2.28.1',
        'aiohttp>=3.8.3',
        'python-dateutil>=2.8.2'
    ],
)
