FROM --platform=linux/amd64 debian:bullseye-slim

RUN apt-get update && \
    apt-get install -y wget apt-transport-https gnupg x11-apps x11-utils python3 && \
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | apt-key add - && \
    echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && apt-get install -y temurin-8-jdk && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

COPY jviewer-starter.py /usr/local/bin/
RUN chmod +x /usr/local/bin/jviewer-starter.py

ENV DISPLAY="host.docker.internal:0"
ENV JVIEWER_JAVA_HOME=""
ENV JVIEWER_JAVA_OPTIONS=""

ENTRYPOINT /usr/local/bin/jviewer-starter.py
