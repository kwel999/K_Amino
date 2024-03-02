from urllib.request import urlopen
from json import loads
import sys
import re
import os

ext = '.tar.gz'

RE_VERSION = re.compile(r'-([0-9.]+)[-]?')
RE_NAME = re.compile(r'(.*)-[0-9.]+[-]?')


if not os.path.exists('dist'):
    os.system(f'{sys.executable} setup.py sdist bdist_wheel')
    os.system('cls' if os.name == 'nt' else 'clear')
    print('dist creted successfully\n')

distfiles = sorted(filter(lambda n: n.endswith(ext), os.listdir('dist')), reverse=True)

if input('Upload to Pypi? [0,1]: ').strip().lower() in ['1', 'y', 's']:
    command = [sys.executable, '-m', 'twine', 'upload']
    name = RE_NAME.findall(distfiles[0].split(ext)[0])[0]
    version = RE_VERSION.findall(distfiles[0].split(ext)[0])[0]
    latest = loads(urlopen(f"https://pypi.python.org/pypi/{name}/json").read())["info"]["version"]
    if version.strip() <= latest:
        if input(f'Try to overwrite the {version} version? [0,1]: ').strip().lower() in ['1', 'y', 's']:
            command.append('--skip-existing')
    command.append('dist/*')
    os.system(' '.join(command))
