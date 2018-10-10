from setuptools import setup

setup(name='pydaybit',
      version='0.0.1',
      description='an API wrapper for Daybit-exchange',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Natural Language :: Korean',
          'Programming Language :: Python :: 3.5',
      ],
      author='Daybit Developers',
      url='https://github.com/daybit-exchange/pydaybit',
      license='Copyright (c) Daybit',
      packages=['pydaybit'],
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
