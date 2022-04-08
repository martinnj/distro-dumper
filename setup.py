from setuptools import setup, find_packages

# Get dependencies from requirements file.
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Get README from markdown file.
with open('README.md') as f:
    readme = f.read().splitlines()

setup(
    name='DistroDumper',
    version='###VERSION###',
    author="Martin Jørgensen",
    author_email="hello@martinnj.dk",
    python_requires=">=3.9",
    install_requires=requirements,

    packages=find_packages(),
    scripts=[
        "dumper.py",
    ],

    license="MIT",
    description="Simple Python script to automatically dump Linux/BSD Distro files from distrowatch.com's RSS feed.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)
