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
    description="Simple Python script to automatically dump Linux/BSD Distro files from distrowatch.com's RSS feed.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)
