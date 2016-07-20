#!/usr/bin/env python

PROJECT = 'kostyor'

VERSION = '0.1'

from setuptools import setup, find_packages

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='Kostyor CLI tool',
    long_description=long_description,

    author='Kostyor Authors',
    author_email='TODO',

    url='https://github.com/sc68cal/kostyor',
    download_url='https://github.com/sc68cal/kostyor/tarball/master',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=['cliff'],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'kostyor = kostyor_cli.main:main'
        ],
        'kostyor.cli': [
            'cluster-status = kostyor_cli.main:ClusterStatus',
            'cluster-list = kostyor_cli.main:ClusterList',
            'list-upgrade-versions = kostyor_cli.main:ListUpgradeVersions',
            'list-discovery-methods = kostyor_cli.main:ListDiscoveryMethods',
            'upgrade-status = kostyor_cli.main:UpgradeStatus',
            'upgrade-cluster = kostyor_cli.main:ClusterUpgrade',
        ],
    },

    zip_safe=False,
)
