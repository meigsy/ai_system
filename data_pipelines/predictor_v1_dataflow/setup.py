import pathlib

from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")


def parse_requirements(filename):
    requirements_path = here / filename
    if not requirements_path.exists():
        raise FileNotFoundError(f"{filename} not found. Please ensure the file exists in the project root directory.")

    with open(requirements_path, "r") as file:
        lines = file.readlines()
        # Filter out comments and empty lines
        return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


# NOTE: You must include 'requirements.txt' in the manifest file for this to work
# otherwise it'll complain about the missing file.
requirements = parse_requirements("requirements.txt")

setup(
    name="predictor-v1-dataflow",  # Required
    version="1.0.0",  # Required
    packages=find_packages(exclude=("tests",)),
    py_modules=["main",
                "example_data",
                "model_output_schema",
                "output_schema",
                "tag",
                "setup"],
    python_requires=">=3.7, <4",
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown"
)
