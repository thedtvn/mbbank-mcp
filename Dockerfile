# Slim instade of alpine to avoid dependency issues with musl vs glibc in wasmtime
FROM astral/uv:python3.11-bookworm-slim

WORKDIR /package

COPY . .

RUN uv pip install . --system

WORKDIR /

RUN rm -r /package

ENTRYPOINT ["mbbank-mcp"]