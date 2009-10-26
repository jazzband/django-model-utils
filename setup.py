from setuptools import setup, find_packages
 
setup(
    name='django-model-utils',
    version='0.3.1',
    description='Django model mixins and utilities',
    long_description=open('README.txt').read(),
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
