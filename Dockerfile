FROM python:3.10-slim
ENV PYTHONUNBUFFERED 1
RUN apt-get update -y \
    && apt-get install -y git \
    && pip install pipenv
WORKDIR /app/
COPY ./Pipfile.lock ./Pipfile /app/
RUN pipenv install --system --deploy --ignore-pipfile
COPY ./main.py /app/
ENTRYPOINT ["python3", "/app/main.py"]