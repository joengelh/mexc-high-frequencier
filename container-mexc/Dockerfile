FROM python:3.9

RUN mkdir /src

WORKDIR /src

COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ADD ./src/ /src/

CMD ["python", "main.py"]