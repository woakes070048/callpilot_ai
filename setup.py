from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f.read().split("\n") if line.strip()]

from callpilot_ai import __version__ as version

setup(
    name="callpilot_ai",
    version=version,
    description="AI Voice Agent",
    author="Nexgen",
    author_email="nexgen@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
