from setuptools import setup, find_packages


long_description = (open('README.rst').read() +
                    open('CHANGES.rst').read() +
                    open('TODO.rst').read())


setup(
    name='django-model-utils',
    version='1.3.1.post1',
    description='Django model mixins and utilities',
    long_description=long_description,
    author='Carl Meyer',
    author_email='carl@oddbird.net',
    url='https://github.com/carljm/django-model-utils/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe=False,
    tests_require=["Django>=1.2"],
    test_suite='runtests.runtests'
)
