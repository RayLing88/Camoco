#!/usr/bin/env python3

from setuptools import setup, find_packages, Extension

import os
import io
import re

def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

pccup = Extension(
    'camoco.PCCUP',
    sources=['camoco/PCCUP.pyx'],
#   extra_compile_args=['-ffast-math'],
#   include_dirs=[numpy.get_include()]
)
refgendist = Extension(
    'camoco.RefGenDist',
    sources=['camoco/RefGenDist.pyx'],
#   extra_compile_args=['-ffast-math'],
#   include_dirs=[numpy.get_include()]
)

setup(
    name = 'camoco',
    version = find_version('camoco','__init__.py'),
    packages = find_packages(),
    scripts = [
        'camoco/cli/camoco'
    ],
    ext_modules = [pccup,refgendist],
    cmdclass = {
    },

    package_data = {
        '':['*.cyx']    
    },
    setup_requires = [
        # Setuptools 18.0 properly handles Cython extensions.
        'setuptools>=18.0',
        'numpy==1.14.5',
        'cython',
    ],
    include_dirs=['camoco/include'],
    install_requires = [		
        #'minus80==0.1.3',
        'flask==0.12.2',
        'cython==0.16',    		
        'igraph==0.1.11',		
        'matplotlib==2.0.0',		
        'numpy==1.12.0',		
        'pandas==0.19.2',		
        'scipy==1.1.0',		
        'termcolor==1.1.0',
        'scikit-learn==0.18.1',
        'powerlaw==1.3.5',
        'networkx==1.11', 
        'statsmodels==0.8.0',
        'bcolz==1.2.1',
        'pyyaml==3.12',
        'apsw'
    ],
    dependency_links = [
        'git+https://github.com/rogerbinns/apsw' 
    ],
    include_package_data=True,

    author = 'Rob Schaefer',
    author_email = 'rob@linkgae.io',
    description = 'Library for Co-Analysis of Molecular Componenets.',
    license = "Copyright Linkage Analytics 2017, Available under the MIT License",
    url = 'https://github.com/schae234/camoco'
)
