FROM python:3.11-slim

WORKDIR /package

COPY . .

RUN pip install .

WORKDIR /

RUN rm -r /package

ENTRYPOINT ["mbbank-mcp"]