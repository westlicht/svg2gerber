import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="svg2gerber-westlicht",
    version="0.0.1",
    author="Simon Kallweit",
    author_email="",
    description="Utility to convert an SVG file to a set of gerber files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/westlicht/svg2gerber",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ["svg2gerber=svg2gerber.svg2gerber:main"],
    },
    package_dir={"svg2gerber": "svg2gerber"},
    license="GPLv2",
    keywords=["svg2gerber", "svg", "gerber", "pcb"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv2 License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
