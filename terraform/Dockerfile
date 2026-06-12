FROM hashicorp/terraform:latest

RUN apk add --no-cache \
    bash \
    curl \
    git \
    ca-certificates

WORKDIR /workspace

ENTRYPOINT ["terraform"]
CMD ["--version"]
