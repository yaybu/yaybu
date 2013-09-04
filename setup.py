from setuptools import setup, find_packages
import os

version = '3.0'

setup(name='Yaybu',
      version=version,
      url="http://yaybu.com/",
      description="Server deployment and configuration management in Python",
      long_description = open("README.rst").read() + "\n" + \
                         open("CHANGES").read(),
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
          'yay >= 0.0.57',
          'python-dateutil < 2.0',
          'apache-libcloud >= 0.12.1',
          'paramiko >= 1.8.0',
          'gevent',
          'lockfile',
      ],
      dependency_links = [
          'https://gevent.googlecode.com/files/gevent-1.0rc2.tar.gz#egg=gevent-1.0rc2',
          ],
      extras_require = {
          'test': ['unittest2', 'mock', 'fakechroot'],
          },
      entry_points = """
      [console_scripts]
      yaybu = yaybu.core.main:main
      """
      )
