from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aws-flow-corrector",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert Amazon Connect flows to Terraform templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws_flow_corrector",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Add runtime dependencies here
    ],
    entry_points={
        "console_scripts": [
            "aws-flow-corrector=aws_flow_corrector.cli:main",
        ],
    },
)
