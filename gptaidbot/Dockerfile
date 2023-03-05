# FROM python:3.9.13-slim-buster
FROM python:3.9.16
WORKDIR /app
COPY requirements.txt /app
RUN python3 -m pip install -r requirements.txt --no-cache-dir
RUN python3 -m pip install --upgrade openai
COPY server.py /app
COPY openai_test.py /app
ENTRYPOINT ["python3"]
CMD ["server.py"]