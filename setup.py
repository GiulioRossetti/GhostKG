from setuptools import setup, find_packages

# Read base requirements
with open("requirements/base.txt") as f:
    base_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read optional requirements
with open("requirements/llm.txt") as f:
    llm_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("requirements/fast.txt") as f:
    fast_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("requirements/dev.txt") as f:
    dev_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("requirements/docs.txt") as f:
    docs_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("requirements/database.txt") as f:
    database_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("requirements/viz.txt") as f:
    viz_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ghost_kg",
    version="0.2.0",  # Updated for Phase 2
    description="Dynamic Knowledge Graph with FSRS-6 Forgetting for LLM Agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Giulio Rossetti",
    author_email="giulio.rossetti@gmail.com",
    url="https://github.com/GiulioRossetti/GhostKG",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    install_requires=base_requires,
    extras_require={
        "llm": llm_requires,           # pip install ghost_kg[llm]
        "fast": fast_requires,         # pip install ghost_kg[fast]
        "postgres": [database_requires[0]],  # pip install ghost_kg[postgres]
        "mysql": [database_requires[1]],     # pip install ghost_kg[mysql]
        "database": database_requires,  # pip install ghost_kg[database] (all drivers)
        "viz": viz_requires,           # pip install ghost_kg[viz]
        "dev": dev_requires,           # pip install ghost_kg[dev]
        "docs": docs_requires,         # pip install ghost_kg[docs]
        "all": llm_requires + fast_requires + database_requires + viz_requires,  # pip install ghost_kg[all]
    },
    entry_points={
        'console_scripts': [
            'ghostkg=ghost_kg.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    keywords="knowledge-graph, llm, fsrs, spaced-repetition, memory, ai-agents",
)