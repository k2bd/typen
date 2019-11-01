import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="typen-k2bd",
    version="0.0.1",
    author="Kevin Duff",
    author_email="kduff@enthought.com",
    description="Enforce function type hints with Traits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/k2bd/typen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
