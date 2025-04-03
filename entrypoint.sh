#!/bin/sh -xe

set -e

# Check if an external node URL is provided
if [ -z "$REMOTE_NODE" ]; then
  echo "Error: REMOTE_NODE is not set."
  exit 1
fi

# Fetch the chain ID from the external node
CHAIN_ID=$(curl -s -X POST --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' -H "Content-Type: application/json" "$REMOTE_NODE" | jq -r '.result')

# Convert hex chain ID to decimal
CHAIN_ID=$((CHAIN_ID))

if [ -z "$CHAIN_ID" ] || [ "$CHAIN_ID" == "null" ]; then
  echo "Error: Failed to retrieve chain ID from $REMOTE_NODE"
  exit 1
fi

echo "Using Chain ID: $CHAIN_ID"

# Modify the genesis.json file to update the chain ID
jq --argjson chainId "$CHAIN_ID" '.config.chainId = $chainId' genesis.json > genesis_tmp.json && mv genesis_tmp.json genesis.json

# Initialize geth with the modified genesis file
geth init genesis.json

# Start geth in the background
geth --networkid "$CHAIN_ID" --dev --http --http.addr 0.0.0.0 --http.port 18545 --http.api debug,eth,net,web3 --ws --ws.addr 0.0.0.0 --ws.port 18546 --ws.api debug,eth,net,web3 --syncmode full --nodiscover --allow-insecure-unlock &


sleep 1

# Trigger _SOME_ transaction on this dev node (othersise, tracing fails)
LOCAL=http://localhost:18545
CT="Content-Type:application/json"

SENDER=$(curl -s -d '{"jsonrpc":"2.0","method":"eth_accounts","params":[],"id":1}' -H $CT $LOCAL| jq -r .result[0])
# | jq -r .result[0])

cat <<EOF | curl -s -d @- -H $CT $LOCAL
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "eth_sendTransaction",
  "params": [
    {
      "from": "$SENDER",
      "to": "0x0000000000000000000000000000000000000000"
    }
  ]
}
EOF

# Sanity: block number is not zero:
blocknum=$(curl -s -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' -H $CT $LOCAL | jq -r .result)

if [ "$blocknum" != "0x1" ]; then
  echo "Error: Failed to change local block number"
  exit 1
fi

# Start the proxy
exec python3 /proxy.py

