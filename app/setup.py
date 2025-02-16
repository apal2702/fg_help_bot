from setuptools import setup, find_packages

long_description = """
FG Assistant
"""
setup(
    name="FG Assistant",
    version="1",
    description="FG Analysis APP",
    author="Ashish Pal",
    author_email="apal@twilio.com",
    packages=find_packages(),
    long_description="Long description goes here",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
