from setuptools import setup, find_packages
import subprocess
import os.path

try:
    # don't get confused if our sdist is unzipped in a subdir of some 
    # other hg repo
    if os.path.isdir('.hg'):
        p = subprocess.Popen(['hg', 'parents', r'--template={rev}\n'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not p.returncode:
            fh = open('HGREV', 'w')
            fh.write(p.communicate()[0].splitlines()[0])
            fh.close()
except (OSError, IndexError):
    pass
    
try:
    hgrev = open('HGREV').read()
except IOError:
    hgrev = ''
    
long_description = (open('README.rst').read() + 
                    open('CHANGES.rst').read() +
                    open('TODO.rst').read())

setup(
    name='django-model-utils',
    version='0.4.0',
    description='Django model mixins and utilities',
    long_description=long_description,
    author='Carl Meyer',
    author_email='carl@dirtcircle.com',
    url='http://bitbucket.org/carljm/django-model-utils/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe=False,
    test_suite='model_utils.tests.runtests.runtests'
)
