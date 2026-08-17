FROM python:slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4

WORKDIR /opt/loFunc/

RUN apt-get update -y
RUN apt-get install fluidsynth -y

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "src/main.py" ]
