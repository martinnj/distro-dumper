FROM python:3.10-alpine3.15

LABEL maintainer="hello@martinnj.dk"
LABEL version="###VERSION###"

# Elevate privilege level.
USER root

# Update any OS packages.
RUN apk update --no-cache 

# Update pip
RUN pip3 install --upgrade --no-cache-dir pip wheel

# Add normal user
RUN addgroup -g 998 -S appgroup && \
    adduser --uid 1000 -S appuser -G appgroup

# Copy our files.
WORKDIR /app
COPY --chown=appuser:appgroup dumper.py /app/dumper.py
COPY --chown=appuser:appgroup requirements.txt /app/requirements.txt

# Prepare cache and dump mountpoints.
RUN mkdir -p /dump /cache
RUN chown appuser:appgroup /cache
RUN chown appuser:appgroup /dump

# Drop to normal user.
USER appuser

# Install pip packages.
ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN pip3 install \
    --user \
    --ignore-installed \
    --no-cache-dir \
    -r requirements.txt

# Return to normal user, set configuration environment variables and run app.
USER appuser
ENV DUMP_INTERVAL=3600
ENV DUMP_DIRECTORY="/cache"
ENV CACHE_DIRECTORY="/dump"
ENTRYPOINT ["python3", "dumper.py"]
