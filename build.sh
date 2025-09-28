#!/bin/bash -xe

#build docker image:

# 1. build geth:
#docker build -t erc7562-geth go-ethereum

# 2. build proxy - references the above "erc7562-geth"
docker build -t geth-erc7562-proxy .
