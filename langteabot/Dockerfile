FROM python:latest
WORKDIR /server
RUN bash -c 'apt-get install software-properties-common;add-apt-repository ppa:mc3man/trusty-media -y;apt-get update;apt-get install ffmpeg -y'
COPY requirements.txt /server
RUN pip3 install -r requirements.txt --no-cache-dir
RUN mkdir user_conf
COPY granted_users.txt /server
COPY config.json /server/user_conf/
COPY server.py /server
ENTRYPOINT ["python"]
CMD ["server.py"]