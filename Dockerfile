FROM python:3.9.0

WORKDIR /

ADD . .

RUN pip3 install -r requirements.txt

CMD ["flask", "run", "--host", "0.0.0.0"]