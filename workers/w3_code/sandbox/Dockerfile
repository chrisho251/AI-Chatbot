# Sandbox image for W3 code. It runs untrusted code with no network, see compose.yaml
FROM rocker/r-ver:4.4.2

RUN apt-get update \
    && apt-get install --yes --no-install-recommends python3 python3-numpy python3-scipy python3-pandas \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin runner
COPY runner.py /opt/sandbox/runner.py
USER runner
EXPOSE 8000
CMD ["python3", "/opt/sandbox/runner.py"]
