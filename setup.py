from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="physicell-config",
    version="1.0.0",
    author="PhysiCell Configuration Builder Contributors",
    author_email="your-email@domain.com",
    description="User-friendly Python package for generating PhysiCell XML configuration files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/physicell-config",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/physicell-config/issues",
        "Documentation": "https://github.com/your-username/physicell-config#readme",
        "Source Code": "https://github.com/your-username/physicell-config",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
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
