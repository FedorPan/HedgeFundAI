from setuptools import setup, find_packages

setup(
    name="hedgefundai",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi==0.103.2",
        "uvicorn==0.23.2",
        "pydantic==2.4.2",
        "alpaca-trade-api==3.0.2",
        "finnhub-python==2.4.18",
        "openai==1.2.3",
        "pandas==2.0.3",
        "numpy==1.24.4",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "python-multipart==0.0.6",
    ],
    python_requires=">=3.9,<3.12",
) 