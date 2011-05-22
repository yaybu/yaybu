from setuptools import setup, find_packages
import os

version = "0.1.2"

setup(name='Yaybu',
      version=version,
      url="http://yaybu.com/",
      description="Server deployment and configuration management in Python",
      long_description=open("README.rst").read(),
      author="Isotoma Limited",
      author_email="support@isotoma.com",
      license="Apache Software License",
      classifiers = [
          "Intended Audience :: System Administrators",
          "Operating System :: POSIX",
          "License :: OSI Approved :: Apache Software License",
      ],
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'jinja2',
          'yay',
      ],
      extras_require = {
          'test': ['testtools', 'discover', 'mock'],
          },
      entry_points = """
      [console_scripts]
      yaybu = yaybu.core.main:main
      """
      )
