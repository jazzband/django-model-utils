from setuptools import setup, find_packages
 
setup(
    name='django-model-utils',
    version='0.2.1',
    description='Django model mixins and utilities',
    long_description=open('README.txt').read(),
    author='Carl Meyer',
    author_email='carl@dirtcircle.com',
    url='http://launchpad.net/django-model-utils',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    setup_requires=['setuptools_bzr'],
)
