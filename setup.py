from setuptools import setup, find_packages

requires = []

setup(
    name='DissBot',
    version='1.0.0',
    author="Dissimulate",
    author_email="mistradam@icloud.com",
    package_dir={'': 'src'},
    packages=find_packages("src"),
    install_requires=requires,
    zip_safe=False,
)
