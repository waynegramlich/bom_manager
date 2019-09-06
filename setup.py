import setuptools

def long_description_read():
    with open("README.md") as readme_file:
        long_description = readme_file.read()
    return long_description

# Arguments to *setup*() are in alphabetical order:
setuptools.setup(
    author="Wayne Gramlich",
    author_email="Wayne@Gramlich.Net",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Opearating System :: OS Independent",
    ],
    description="Bill Of Materials Manager",
    entry_points = {
        "console_scripts": ["bom_manager=bom_manager:main"],
    },
    install_requires = [
        "bs4",
        "currencyconverter",
        "lxml",
        "pyside2",
        "requests",
        "sexpdata",
    ],
    license="MIT",
    long_description=long_description_read(),
    long_description_content_type="text/markdown",
    name="bom_manager_wayne_gramlich",
    packages=[
        "bom_manager",
    ],
    python_requires=">=3.6",
    url="https://github.com/waynegramlich/bom_manager",
    version="0.0.1"
)
