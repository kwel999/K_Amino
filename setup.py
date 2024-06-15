from setuptools import setup, find_packages
import k_amino

with open("README.md", "r") as stream:
    README = stream.read()

with open("requirements.txt", "r") as stream:
    REQUIREMENTS = stream.read()

setup(
    name=k_amino.__title__,
    description=k_amino.__description__,
    version=k_amino.__version__,
    url=k_amino.__url__,
    long_description=README,
    long_description_content_type="text/markdown",
    author=k_amino.__author__,
    author_email=k_amino.__author_email__,
    license=k_amino.__license__,
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
    install_requires=REQUIREMENTS,
    setup_requires=["wheel"],
    packages=find_packages(),
    package_data={'k_amino': ['py.typed']}
)
