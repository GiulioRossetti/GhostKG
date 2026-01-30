from setuptools import setup, find_packages

setup(
    name="ghost_kg",
    version="0.1.0",
    description="Dynamic Knowledge Graph with FSRS-6 Forgetting for LLM Agents",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "networkx>=3.0",
        "fsrs>=1.0.0",
        "ollama>=0.1.6",
        "matplotlib>=3.5.0" # Optional for static plotting
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)