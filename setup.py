from setuptools import setup
import os
from freecad.weldfeature.version import __version__

version_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "freecad", "weldfeature", "version.py"
)
with open(version_path) as fp:
    exec(fp.read())

setup(
    name="freecad.weldfeature",
    version=str(__version__),
    packages=["freecad", "freecad.weldfeature"],
    maintainer="Alex Neufeld",
    maintainer_email="alex.d.neufeld@gmail.com",
    url="https://github.com/alexneufeld/FreeCAD_WeldfFeature",
    description="FreeCAD module for adding visual representations "
    "of welded joints to assemblies",
    install_requires=[],
    include_package_data=True,
)
