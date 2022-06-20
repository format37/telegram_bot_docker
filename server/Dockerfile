FROM python:latest
WORKDIR /server
COPY requirements.txt /server
RUN pip3 install -r requirements.txt --no-cache-dir
COPY webhook_cert.pem /server
COPY webhook_pkey.pem /server
COPY server.py /server
ENTRYPOINT ["python"]
CMD ["server.py"]