from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pydaybit',
      version='0.0.3',
      description='an API wrapper for Daybit-exchange',
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: Apache Software License",
      ],
      author='Daybit Developers',
      url='https://github.com/daybit-exchange/pydaybit',
      packages=find_packages(),
      setup_requires=[
          'pytest-runner',
      ],
      install_requires=[
          'async_timeout',
          'furl',
          'websockets',

          # Examples
          'dateparser',
          'pandas',
          'numpy',
          'tabulate',
          'pytz',
      ],
      tests_require=[
          'pytest',
          'pytest-asyncio',
      ],
      zip_safe=False)
