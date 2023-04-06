from setuptools import setup, find_packages

setup(
    name="silkflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
    ],
    author="Andrew Beck",
    author_email="esensible@users.noreply.github.com",
    description="Render reactive HTML pages targetting the Kindle's Silk browser, with Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/esensible/silkflow",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)
