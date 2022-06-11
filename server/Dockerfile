FROM python:3.10-slim

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.13

# RUN apk add --no-cache libffi-dev build-base musl-dev openssl-dev ffmpeg cargo
# RUN pip install cffi
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false
RUN poetry update
RUN poetry install --no-dev --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . /code

CMD [ "python", "server/main.py" ]
