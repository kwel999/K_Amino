import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text()

setup(
    name="kamino",
    version="1.0.0",
    url="https://github.com/kwel999/KAmino",
    download_url="https://github.com/kwel999/KAmino/archive/refs/heads/main.zip",
    description="Amino Bots with python!",
    long_description=README,
    long_description_content_type="text/markdown",
    author="KWEL",
    author_email="itskwel999@gmail.com",
    license="MIT",
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
        "setuptools",
        "aiohttp",
        "websocket-client==1.3.1",
        "websockets",
        "ujson",
    ],
    setup_requires=["wheel"],
    packages=find_packages(),
)
