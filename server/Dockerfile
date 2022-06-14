FROM python:3.10-slim-buster

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.13


RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y build-essential libssl-dev libffi-dev \
                       python3-dev cargo \
                       ffmpeg

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false
RUN poetry update
RUN poetry install --no-dev --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY ./server /code/server

CMD [ "python", "server/main.py" ]
