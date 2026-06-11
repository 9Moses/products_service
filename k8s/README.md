Kubernetes quickstart

This `k8s/` folder contains Kubernetes deployment manifests for the project. Use these quick instructions to build container images and apply the manifests to a Kubernetes cluster.

1. Build the images locally and tag them (or set your CI to tag with the build number):

docker build -t ghcr.io/<your-org>/rest-api:latest ./api
docker build -t ghcr.io/<your-org>/rest-main:latest ./main

2. Push images to a registry accessible by your cluster (GitHub Container Registry example):

docker tag rest-api:latest ghcr.io/<your-org>/rest-api:latest
docker tag rest-main:latest ghcr.io/<your-org>/rest-main:latest
docker push ghcr.io/<your-org>/rest-api:latest
docker push ghcr.io/<your-org>/rest-main:latest

If you're using a local Kubernetes cluster (kind/minikube), load images directly instead of pushing:

# kind
kind load docker-image ghcr.io/<your-org>/rest-api:latest
kind load docker-image ghcr.io/<your-org>/rest-main:latest

# minikube
minikube image load rest-api:latest
minikube image load rest-main:latest

3. Apply the manifests (namespace + stacks):

kubectl apply -f k8s/namespace.yaml
kubectl apply -f api/k8s/api-deployment.yaml
kubectl apply -f main/k8s/main-deployment.yaml

4. Verify pods and services:

kubectl get pods -n rest-microservice
kubectl get svc -n rest-microservice

Notes
- The manifests reference images `rest-microservice-api:latest` and `rest-microservice-main:latest`. Replace tags to match your registry naming or update the manifests.
- DB passwords are provided in plain env vars in the manifests for simplicity — switch to `Secret`s for production.
- Adjust NodePort values or replace Services with an `Ingress` for production routing.
