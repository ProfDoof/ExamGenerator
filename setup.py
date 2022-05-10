from setuptools import setup

setup( 
    name="mcgen",
    version="0.0.0",
    py_modules=['mcgen'],
    install_requires=['Click',],
    entry_points={
        'console_scripts': [
            'mcgen=mcgen:convert',
        ],
    },
)