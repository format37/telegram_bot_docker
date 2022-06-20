FROM python:latest
WORKDIR /server
COPY requirements.txt /server
RUN pip3 install -r requirements.txt --no-cache-dir
RUN bash -c 'apt-get install software-properties-common;add-apt-repository ppa:mc3man/trusty-media -y;apt-get update;apt-get install ffmpeg -y'
COPY server.py /server
ENTRYPOINT ["python"]
CMD ["server.py"]