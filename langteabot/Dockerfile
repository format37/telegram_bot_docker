#FROM python:latest
FROM python:3.9.16
WORKDIR /server
RUN bash -c 'apt-get install software-properties-common;add-apt-repository ppa:mc3man/trusty-media -y;apt-get update;apt-get install ffmpeg -y'
COPY requirements.txt /server
RUN pip3 install -r requirements.txt --no-cache-dir
RUN python3 -m pip install --upgrade openai
RUN mkdir user_conf
RUN mkdir data
# COPY granted_users.txt /server
COPY data/add_funds.wav /server/data
COPY server.py /server
ENTRYPOINT ["python3"]
CMD ["server.py"]