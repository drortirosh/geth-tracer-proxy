#locally run docker:

./build.sh

remote=$1
debug=$2
tracer="-e NATIVE_TRACER=*"
#fork="-e FORK=1"

docker run -p 18545:18545 -p 8545:8545 $tracer $fork -e PORT=$PORT -e DEBUG=$debug -e REMOTE_NODE=$remote --rm -ti geth-erc7562-proxy
