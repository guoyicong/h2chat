from setuptools import setup


with open('requirements.txt') as f:
    content = f.readlines()


setup(
    name = 'h2chat',
    version = '0.1',
    packages = ['h2chat'],
    description = 'HTTP/2 chat program',
    url = 'https://github.com/guoyicong/h2chat',
    author = 'Yicong Guo',
    author_email = 'guoyicong100@163.com',
    license = 'MIT License',
    install_requires = content
    )
