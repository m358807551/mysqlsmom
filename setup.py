from setuptools import setup, find_packages


install_requires = """appnope==0.1.0
APScheduler==3.5.1
asn1crypto==0.24.0
backports.shutil-get-terminal-size==1.0.0
blinker==1.4
certifi==2018.4.16
cffi==1.11.5
chardet==3.0.4
click==6.7
cryptography==2.2.2
decorator==4.3.0
elasticsearch==2.4.0
enum34==1.1.6
funcsigs==1.0.2
futures==3.2.0
idna==2.7
ipaddress==1.0.22
ipython==5.0.0
ipython-genutils==0.2.0
mysql-replication==0.18
pathlib2==2.3.2
peewee==3.5.2
pexpect==4.6.0
pickleshare==0.7.4
prompt-toolkit==1.0.15
ptyprocess==0.6.0
pycparser==2.18
Pygments==2.2.0
PyMySQL==0.9.2
pytz==2018.5
redis==2.10.6
requests==2.19.1
scandir==1.7
simplegeneric==0.8.1
six==1.11.0
traitlets==4.3.2
tzlocal==1.5.1
urllib3==1.23
wcwidth==0.1.7
yolk==0.4.3
"""

setup(
    name='mysqlsmom',
    version='0.1.6',
    keywords='mysql elasticsearch es sync',
    description='sync data from mysql to elasticsearch',
    license='MIT License',
    url='https://github.com/m358807551/mysqlsmom',
    author='MCTW',
    author_email='m358807551@163.com',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    install_requires=install_requires.split("\n"),
    entry_points={
        'console_scripts': ['mom = mysqlsmom.mysqlsmom:cli'],
    }
)
