FROM python:3.9.13-slim-buster
WORKDIR /app
# COPY requirements.txt /app
# RUN pip3 install -r requirements.txt --no-cache-dir
RUN python3 -m pip install --upgrade openai
COPY server.py /app
COPY openai_test.py /app
ENTRYPOINT ["python"]
CMD ["server.py"]