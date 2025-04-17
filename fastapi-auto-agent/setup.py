from setuptools import setup, find_packages

setup(
    name="fastapi-auto-agent",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "fastapi-auto-agent=fastapi_auto_agent.cli:main",
        ],
    },
    install_requires=[
        "opentelemetry-api>=1.11.0",
        "opentelemetry-sdk>=1.11.0",
        "opentelemetry-exporter-otlp>=1.11.0",
        "opentelemetry-instrumentation-fastapi>=0.30b0",
        "opentelemetry-instrumentation-sqlalchemy>=0.30b0",
        "opentelemetry-instrumentation-requests>=0.30b0",
        "wrapt>=1.14.0",
    ],
)
