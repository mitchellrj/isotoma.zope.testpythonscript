from setuptools import setup, find_packages

setup(name='isotoma.zope.testpythonscript',
    version="1.0.0",
    url="http://www.isotoma.com/",
    author="Richard Mitchell",
    author_email="richard.mitchell@isotoma.com",
    packages=find_packages(),
    dependency_links=['http://labs.freehackers.org/attachments/download/397/indent_finder-1.4.tgz'],
    install_requires=['mock', 'indent_finder'],
    zip_safe=False,
    include_package_data=True,
)