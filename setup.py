from setuptools import setup, find_packages

# Get dependencies from requirements files.
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
with open('requirements-dev.txt') as f:
    dev_requirements = f.read().splitlines()

# Get README from markdown file.
with open('README.md') as f:
    readme = f.read().splitlines()

setup(
    name='DistroDumper',
    version='###VERSION###',
    author="Martin Jørgensen",
    author_email="hello@martinnj.dk",
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={"dev": dev_requirements},

    packages=find_packages(),
    scripts=[
        "dumper.py",
    ],

    license="MIT",
    description="Overengineered Python script and Docker container to automatically dump Linux/BSD torrents from the internet.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)
