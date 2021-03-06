import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-sanity",
    version = "1.0",
    author = "Rob Combs, Richard Bronosky, Clay Mcclure, Matt Anderson",
    author_email = "robert.combs@cmgdigital.com",
    description = "Django management command for determining if resources are sane within the context of an environment.",
    keywords = "sanity",
    packages = ['sanity'],
    long_description = read('README'),
    classifiers = [
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: BSD License",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
    ],
)
