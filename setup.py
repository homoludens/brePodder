from setuptools import setup

requirements = [
    'feedparser',
    'PyQt5',
    'requests',
    'favicon'

]

setup(
    name='brePodder',
    version='0.23',
    description="PyQt Podcast client",
    author="homoludnes",
    author_email='marko _at_ droopia.net',
    url='https://github.com/homoludens/brePodder',
    packages=['brepodder', 'brepodder.images', 'brepodder.tests'],
    package_data={'brepodder.images': ['*.png']},
    entry_points={
        'console_scripts': [
            'brepodder=brepodder.brePodder:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='brepodder',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
    ],
)
