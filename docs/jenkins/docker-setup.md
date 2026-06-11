Docker CLI for Jenkins node

If your Jenkins pipelines use `docker` commands, ensure the Jenkins agent/node has the Docker CLI installed and access to the Docker daemon socket (`/var/run/docker.sock`). Two options:

1) Install docker CLI in an existing Jenkins container (quick, not persistent)

  docker exec -it jenkins bash
  apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release
  curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
  echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
  apt-get update && apt-get install -y docker-ce-cli

2) Build a custom Jenkins image with docker CLI preinstalled (recommended for reproducibility)

  FROM jenkins/jenkins:lts
  USER root
  RUN apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release \
      && curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
      && echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
      && apt-get update && apt-get install -y docker-ce-cli && rm -rf /var/lib/apt/lists/*
  RUN jenkins-plugin-cli --plugins docker-workflow
  USER jenkins

  Build and run:

  docker build -t custom-jenkins:latest -f Dockerfile.jenkins .
  docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
    -v jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock \
    -v "/c/Users/TECH GIANTS PLUS/.kube:/root/.kube:ro" custom-jenkins:latest

Notes:
- Mounting `/var/run/docker.sock` gives the container access to the host Docker daemon — be aware of security implications.
- Installing `docker-workflow` plugin enables Declarative `agent { docker { ... } }` if you later want to use that form.
