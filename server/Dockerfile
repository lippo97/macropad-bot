FROM python:3.10-slim-buster

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y ffmpeg

COPY . /code
WORKDIR /code

RUN pip install -r requirements.txt

CMD [ "python", "server/main.py" ]
