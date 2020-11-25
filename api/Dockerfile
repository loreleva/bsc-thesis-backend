FROM alpine:3

RUN apk add --no-cache curl

RUN apk add --no-cache python3 py3-psycopg2

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

RUN mkdir /code

CMD ["python3", "code/app.py"]