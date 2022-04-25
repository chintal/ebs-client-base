import setuptools

_requires = [
    'six',
    'appdirs',
    'setuptools-scm',
    'tendril-utils-core',
    'tendril-async-utils-core',
    'pyserial',
    'construct',
]

setuptools.setup(
    name='ebs-client-base',
    url='',

    author='Chintalagiri Shashank',
    author_email='shashank.chintalagiri@gmail.com',

    description='EBS Client Development Infrastructure',
    long_description='',

    packages=setuptools.find_packages(),
    # package_dir={'ebs.linuxnode.updater': 'ebs/linuxnode/updater'},
    # package_data={'ebs.linuxnode.updater': ['default/config.ini']},

    install_requires=_requires,
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
    ],
    entry_points={
          'console_scripts': [
              'ebs-client-base = ebs.client.main:main'
          ]
    },
)
