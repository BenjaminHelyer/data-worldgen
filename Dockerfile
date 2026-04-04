FROM python:3.11.9-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /usr/local/bin/uv

WORKDIR /app

RUN useradd --system --uid 10001 --no-create-home appuser

COPY pyproject.toml README.md ./
RUN uv pip compile pyproject.toml -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt

COPY src ./src
RUN uv pip install --system --no-cache --no-deps .

USER appuser

# Default: S3 batch (Fargate). Override module for local batch, e.g.:
#   docker run ... data-worldgen-batch world_builder.batch_local --mode ecosystem --config /data/c.json --out /data/o.parquet
ENTRYPOINT ["python", "-m"]
CMD ["world_builder.batch_s3"]
