from setuptools import setup, find_packages

name = 'pytil'
setup(
    version='8.0.1.dev',
    name=name,
    # Only include {name}/, not e.g. tests/
    packages=find_packages(include=(name, name + '.*')),
)
