import os

from setuptools import find_packages, setup


def long_desc(root_path):
    FILES = ['README.rst', 'CHANGES.rst']
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath) as f:
                yield f.read()


HERE = os.path.abspath(os.path.dirname(__file__))
long_description = "\n\n".join(long_desc(HERE))


setup(
    name='django-model-utils',
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    license="BSD",
    description='Django model mixins and utilities',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Carl Meyer',
    author_email='carl@oddbird.net',
    maintainer='JazzBand',
    url='https://github.com/jazzband/django-model-utils',
    packages=find_packages(exclude=['tests*']),
    python_requires=">=3.8",
    install_requires=['Django>=3.2'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
    ],
    zip_safe=False,
    package_data={
        'model_utils': [
            'locale/*/LC_MESSAGES/django.po',
            'locale/*/LC_MESSAGES/django.mo',
            'py.typed',
        ],
    },
)
