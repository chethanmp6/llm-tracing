#!/bin/bash

# Set variables
ECR_REPO="187135693153.dkr.ecr.ap-south-1.amazonaws.com/tracing-api"
TAG="latest"

echo "Building Docker image..."
docker build -t tracing-api:$TAG .

echo "Tagging image for ECR..."
docker tag tracing-api:$TAG $ECR_REPO:$TAG

echo "Pushing to ECR..."
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $ECR_REPO
docker push $ECR_REPO:$TAG

echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/tracing-api

echo "Getting ingress URL..."
kubectl get ingress tracing-api-ingress