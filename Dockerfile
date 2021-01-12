FROM python:3.8-alpine
WORKDIR /bot
COPY bot_v2.py .
COPY Match.py .
COPY MatchManager.py .
COPY requirements.txt .
COPY sources.json .

RUN apk --update --no-cache add \
    build-base \
    py-pip \
    py-requests \
    zlib-dev \
    jpeg-dev \
    py-pillow
RUN pip install --no-cache-dir -r ./requirements.txt
RUN apk del build-base py-pip
CMD ["python", "./bot_v2.py"]