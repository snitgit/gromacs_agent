from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gromacs_copilot",
    version="0.2.2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "gmx_copilot=gromacs_copilot.cli:main",
        ],
    },
    author="ChatMol Team",
    author_email="jinyuansun@chatmol.org",
    description="A molecular dynamics simulation assistant powered by AI using GROMACS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ChatMol/gromacs_copilot", 
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)