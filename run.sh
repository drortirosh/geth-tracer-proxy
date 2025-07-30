#locally run docker:

./build.sh

remote=$1
debug=$2

docker run -p 8545:8545 -e DEBUG=$debug -e REMOTE_NODE=$remote --rm -ti geth-erc7562-proxy
