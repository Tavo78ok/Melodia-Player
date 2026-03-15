from setuptools import setup, find_packages

setup(
    name='melodia',
    version='1.2.0',
    description='A beautiful music player for Linux (GTK4 + libadwaita)',
    author='Your Name',
    author_email='you@example.com',
    url='https://github.com/yourname/melodia',
    license='GPL-3.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.10',
    install_requires=[
        'mutagen',
    ],
    entry_points={
        'console_scripts': [
            'melodia=melodia.main:main',
        ],
    },
    data_files=[
        ('share/applications', ['data/com.github.melodia.desktop']),
        ('share/icons/hicolor/scalable/apps', ['data/icons/hicolor/scalable/apps/com.github.melodia.svg']),
    ],
    classifiers=[
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
