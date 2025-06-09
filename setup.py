import re
from setuptools import setup

with open("requirements.txt") as f:
    req = f.read().splitlines()

with open("README.md") as f:
    ldr = f.read()

with open('mbbank_mcp/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name='mbbank_mcp',
    version=version,
    license="MIT",
    description='An MCP server for MBBank',
    long_description=ldr,
    long_description_content_type="text/markdown",
    url='https://github.com/thedtvn/mbbank-mcp',
    author='The DT',
    packages=["mbbank_mcp"],
    install_requires=req,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "mbbank-mcp=mbbank_mcp.__main__:main",
        ],
    }
)