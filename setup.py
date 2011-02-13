from setuptools import setup, find_packages
import os

version = "0.1"

setup(name='Yaybu',
      version=version,
      description="",
      long_description=open("README.rst").read() + "\n" + open("HISTORY.rst").read(),
      author="Isotoma Limited",
      author_email="support@isotoma.com",
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'jinja2',
          'yay',
      ],
      entry_points = """
      [console_scripts]
      yaybu = yaybu.core.runner:main
      """
      )
