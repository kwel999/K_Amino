import os
import sys

if not os.path.exists('dist'):
    os.system(f'{sys.executable} setup.py sdist bdist_wheel')
    os.system('cls' if os.name == 'nt' else 'clear')
    print('dist creted successfully\n')

if input('Upload to Pypi?[0,1]: ').strip().lower() in ['1', 'y', 's']:
    os.system(f'{sys.executable} -m twine upload dist/*')
