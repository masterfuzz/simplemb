import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="simplemb-masterfuzz",
    version="0.9.0",
    author="masterfuzz",
    author_email="master.fuzz@gmail.com",
    description="Toy message bus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masterfuzz/simplemb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)