from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="physicell-settings",
    version="0.1.9",  # Added automatic number_of_cells user parameter
    author="Marco Ruscone",
    author_email="ym.ruscone94@gmail.com",
    description="User-friendly Python package for generating PhysiCell_settings.xml configuration files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mruscone/PhysiCell_Settings",
    project_urls={
        "Bug Tracker": "https://github.com/mruscone/PhysiCell_Settings/issues",
        "Documentation": "https://github.com/mruscone/PhysiCell_Settings#readme",
        "Source Code": "https://github.com/mruscone/PhysiCell_Settings",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme",
            "myst-parser",
        ],
    },
    entry_points={
        "console_scripts": [
            "physicell-config-test=physicell_config.test_config:main",
        ],
    },
    keywords=[
        "physicell",
        "multicellular",
        "simulation",
        "biology",
        "computational-biology",
        "bioinformatics",
        "cancer",
        "tissue",
        "xml",
        "configuration",
    ],
    include_package_data=True,
    zip_safe=False,
)
