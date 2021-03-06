#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_namespace_packages

import os.path

readme_filename = "readme.rst"
if not os.path.isfile(readme_filename):
    readme_filename = "docs/readme.rst"
with open(readme_filename) as readme_file:
    readme = readme_file.read()

history_filename = "changelog.rst"
if not os.path.isfile(history_filename):
    history_filename = "docs/changelog.rst"

with open(history_filename) as history_file:
    history = history_file.read()

requirements = ["Click>=6.0", "graphtransliterator"]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="A. Sean Pue",
    author_email="a@seanpue.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        # "Programming Language :: Python :: 2",
        # 'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3",
        # 'Programming Language :: Python :: 3.4',
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="An Urdu-Hindi metrical scanner inspired by bioinformatics",
    entry_points={"console_scripts": ["urdubiometer=urdubiometer.cli:main"]},
    install_requires=requirements,
    license="BSD license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="urdubiometer",
    name="urdubiometer",
    packages=find_namespace_packages(include=['urdubiometer.*']),#find_packages(include),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/urdubiometer/urdubiometer",
    version="0.2.9",
    zip_safe=False,
)
