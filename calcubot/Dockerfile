FROM python:3.9.13-slim-buster
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
COPY calculate_native.py /app
COPY calculate_inline.py /app
COPY user_defined.py /app
COPY server.py /app
# no permissions user
RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app && \
    find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;
# Give a write permission for user "app" to path "/app/logs/"
# RUN chown -R 1001:1001 /app/logs/
USER app:app
ENTRYPOINT ["python"]
CMD ["server.py"]