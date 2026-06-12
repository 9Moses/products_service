FROM docker:latest

RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    curl \
    git \
    ca-certificates

RUN pip install --no-cache-dir \
    ansible \
    docker \
    pyyaml \
    --break-system-packages

WORKDIR /workspace

ENTRYPOINT ["ansible-playbook"]
CMD ["--version"]
