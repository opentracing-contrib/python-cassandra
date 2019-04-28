from setuptools import setup

version = open("VERSION").read()
setup(
    name="cassandra_opentracing",
    version=version,
    url="",
    download_url="https://github.com/nicholasamorim/opentracing-python-cassandra/tarball/"
    + version,
    license="Apache License 2.0",
    author="Nicholas Amorim",
    author_email="nicholas@santos.ee",
    description="OpenTracing support for Cassandra Driver",
    long_description=open("README.md").read(),
    packages=["cassandra_opentracing"],
    platforms="any",
    install_requires=["cassandra-driver", "opentracing>=2.0,<2.1"],
    extras_require={
        "tests": [
            "mock<1.1.0",
            "pytest==4.4.1",
            "pytest-cov==2.6.1",
            "codecov",
        ]
    },
    classifiers=[
        "Intended Audience :: Developers",
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
