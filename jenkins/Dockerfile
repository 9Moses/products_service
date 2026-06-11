FROM jenkins/jenkins:lts

USER root

# Install Docker CLI
RUN apt-get update \
  && apt-get install -y ca-certificates curl gnupg lsb-release apt-transport-https \
  && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg || true \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends docker-ce-cli \
  && rm -rf /var/lib/apt/lists/*

# Install Docker Pipeline plugin so Declarative docker agent works
RUN jenkins-plugin-cli --plugins docker-workflow

USER jenkins
