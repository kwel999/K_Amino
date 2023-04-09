from setuptools import setup, find_packages
from k_amino import __version__

with open("README.md", "r") as stream:
    README = stream.read()


setup(
    name="k-amino.py",
    version=__version__,
    url="https://github.com/kwel999/KAmino",
    download_url="https://github.com/kwel999/KAmino/archive/refs/heads/main.zip",
    description="Amino Bots with python!",
    long_description=README,
    long_description_content_type="text/markdown",
    author="KWEL",
    author_email="itskwel999@gmail.com",
    license="Apache",
    keywords=[
        "api",
        "python",
        "python3",
        "python3.x",
        "KWEL",
        "kwel999",
        "kwel.py",
        "Amino",
        "kamino",
        "kamino py"
        "K-Amino",
        "kamino",
        "kamino",
        "kamino-bot",
        "kamino-bots",
        "kamino-bot",
        "ndc",
        "narvii.apps",
        "aminoapps",
        "kamino-py",
        "kamino",
        "kamino-bot",
        "narvii",
    ],
    include_package_data=True,
    install_requires=[
        "JSON_minify",
        "httpx",
        "setuptools",
        "aiohttp",
        "websocket-client==1.3.1",
        "websockets",
        "ujson",
        "requests",
        "easy-events==2.8.2"
    ],
    setup_requires=["wheel"],
    packages=find_packages(),
)
