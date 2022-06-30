FROM python:3.9.13-slim-buster
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
COPY calculate.py /app
COPY server.py /app
# no permissions user
RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app && \
    find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;
USER app:app
ENTRYPOINT ["python"]
CMD ["server.py"]