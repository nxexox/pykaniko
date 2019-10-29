import os
import kaniko

from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    README = f.read()


setup(
    name=kaniko.__title__,
    version=kaniko.__version__,
    packages=kaniko(
        exclude=('tests', '*tests', '*tests*')
    ),  # We throw away from the assembly too much.
    include_package_data=True,
    test_suite='tests',  # Include tests.
    license='Apache 2.0',  # Put the license.
    description='Python kaniko https://github.com/GoogleContainerTools/kaniko',
    long_description=README,
    long_description_content_type='text/markdown',
    install_requires=[],
    tests_require=['codecov>=2', 'coverage>=4'],
    setup_requires=['twine>=1', 'mkdocs>=1'],
    url=kaniko.__url__,
    author=kaniko.__author__,
    author_email=kaniko.__email__,
    maintainer='Deys Timofey',
    maintainer_email='nxexox@gmail.com',
    classifiers=[
        'Environment :: Server Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    zip_safe=True,
)
