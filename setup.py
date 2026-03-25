"""
Inventory Tracker
A desktop application for tracking inventory items with status history.
"""

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 10):
    sys.exit("Python 3.10 or later is required.")

setup(
    name="inventory-tracker",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Inventory tracking application with status history and reports",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/inventory-tracker",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.5.0",
    ],
    entry_points={
        "console_scripts": [
            "inventory-tracker=inventory_tracker:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Inventory",
    ],
    keywords="inventory, tracking, gui, sqlite, pyqt6",
)
