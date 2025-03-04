from setuptools import setup, find_packages

setup(
    name="gmx_copilot",
    version="0.1.0",
    py_modules=["gmx_copilot"],
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "gmx_copilot=gmx_copilot:main",
        ],
    },
    author="ChatMol Team",
    author_email="jinyuansun@chatmol.org",
    description="A molecular dynamics simulation assistant powered by AI using GROMACS.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ChatMol/gromacs_copilot", 
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
