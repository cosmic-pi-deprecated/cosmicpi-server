#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'pika>=0.10.0',
]

test_requirements = [
    'pytest>=3',
]

setup(
    name='cosmicpi_server',
    version='0.1.0',
    description='Cosmic Pi server application.',
    long_description=readme + '\n\n' + history,
    author='CosmicPi team',
    author_email='info@cosmicpi.org',
    url='https://github.com/CosmicPi/cosmicpi-server',
    packages=[
        'cosmicpi_server',
    ],
    package_dir={'cosmicpi_server':
                 'cosmicpi_server'},
    entry_points={
        'console_scripts': [
            'cosmicpi_server=cosmicpi_server.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license='GNU General Public License v3',
    zip_safe=False,
    keywords='cosmicpi_server',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
