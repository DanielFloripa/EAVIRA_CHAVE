FROM python:3.6.6
ENV PYTHONUNBUFFERED 1

WORKDIR /code
ADD . /code

VOLUME /code

CMD ["python", "tests/ssc_test.py"]
