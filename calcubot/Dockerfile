FROM python:3.10-slim-buster
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
COPY server.py /app
ENTRYPOINT ["python"]
CMD ["server.py"]