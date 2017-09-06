#!/bin/bash -e

if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
  docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

  if [ "$TRAVIS_BRANCH" == "master" ]; then
    tag=latest
  elif [ ! -z "$TRAVIS_TAG" ]; then
    tag="${TRAVIS_TAG}"
  elif [ ! -z "$TRAVIS_BRANCH" ]; then
    tag="${TRAVIS_BRANCH}"
  else
    echo "Not pushing image"
    exit 0
  fi

  echo "Pushing image to docker hub ${DOCKER_HUB_REPO}:${tag}"
  docker tag odoo-dump-bag-server "camptocamp/odoo-dump-bag-server:${tag}"
  docker push "camptocamp/odoo-dump-bag-server:${tag}"

  docker tag odoo-dump-bag-nginx "camptocamp/odoo-dump-bag-server:nginx"
  docker push "camptocamp/odoo-dump-bag-server:nginx"
fi
