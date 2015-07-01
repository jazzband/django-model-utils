from os.path import join
from setuptools import setup, find_packages
from setuptools.command.install_lib import install_lib as _install_lib
from distutils.command.build import build as _build
from distutils.cmd import Command


long_description = (open('README.rst').read() +
                    open('CHANGES.rst').read() +
                    open('TODO.rst').read())


def get_version():
    with open(join('model_utils', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


class compile_translations(Command):
    """command tries to compile messages via django compilemessages, does not 
       interrupt setup if gettext is not installed"""

    description = 'compile message catalogs to MO files via django compilemessages'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import os
        import sys
        
        from django.core.management import execute_from_command_line, CommandError
        
        curdir = os.getcwd()
        os.chdir(os.path.realpath('model_utils'))
        
        try:
            execute_from_command_line(['django-admin', 'compilemessages'])
        except CommandError:
            # raised if gettext pkg is not installed
            pass
        finally:
            os.chdir(curdir)


class build(_build):
    sub_commands = [('compile_translations', None)] + _build.sub_commands


class install_lib(_install_lib):
    def run(self):
        self.run_command('compile_translations')
        _install_lib.run(self)

setup(
    name='django-model-utils',
    version=get_version(),
    description='Django model mixins and utilities',
    long_description=long_description,
    author='Carl Meyer',
    author_email='carl@oddbird.net',
    url='https://github.com/carljm/django-model-utils/',
    packages=find_packages(),
    install_requires=['Django>=1.4.2'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Framework :: Django',
    ],
    zip_safe=False,
    tests_require=["Django>=1.4.2"],
    test_suite='runtests.runtests',
    setup_requires=['Django>=1.4.2'],
    include_package_data=True,
    package_data = {
        'model_utils': ['locale/*/LC_MESSAGES/django.po','locale/*/LC_MESSAGES/django.mo'],
    },
    cmdclass={'build': build, 'install_lib': install_lib,
              'compile_translations': compile_translations}
)
