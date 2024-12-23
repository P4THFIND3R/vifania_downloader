FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get clean
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY . /app

CMD ["python", "-m", "src.main"]