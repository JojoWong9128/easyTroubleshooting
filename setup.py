"""
The build/compilations setup

>> pip install -r requirements.txt
>> python setup.py install
"""
import pip
import logging
import pkg_resources
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def _parse_requirements(file_path):
    pip_ver = pkg_resources.get_distribution('pip').version
    pip_version = list(map(int, pip_ver.split('.')[:2]))

    try:  # for pip >= 10
        from pip._internal.req import parse_requirements
    except ImportError:  # for pip <= 9.0.3
        from pip.req import parse_requirements

    if pip_version >= [6, 0]:
        raw = parse_requirements(file_path, session=pip._internal.download.PipSession())
    else:
        raw = pip.req.parse_requirements(file_path)
    return [str(i.req) for i in raw]


# parse_requirements() returns generator of pip.req.InstallRequirement objects
try:
    install_reqs = _parse_requirements("requirements.txt")
except Exception:
    logging.warning('Fail load requirements file, so using default ones.')
    install_reqs = []

setup(
    name='easyTroubleshooting',
    version='0.2.1',
    url='',
    author='Yujiao Wang',
    author_email='wangyujiao@genomics.cn',
    license='MGI',
    description='Easy troubleshooting for Basecall offline images',
    packages=["easyTroubleshooting"],
    install_requires=install_reqs,
    include_package_data=True,
    python_requires='>=3.6',
    long_description="""This is an implementation of easyTroubleshooting on Python 3.Batch image enhancement, fov and 
    cycle statistics have been included in it.Additionally, defect detection and classification will be offered soon.""",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: BGI|MGI",
        "License :: OSI Approved :: MGI License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Basecall/OfflineTroubleshooting :: Artificial Intelligence",
        "Topic :: Basecall/OfflineTroubleshooting :: Image Recognition",
        "Topic :: Scientific/OfflineTroubleshooting :: Visualization",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords="easy troubleshooting  basecall  fov and cycle statistics  defect detection",
)
