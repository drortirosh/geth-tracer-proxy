#!/bin/bash -xe

echo 'must have "./run.sh sepolia" active in another window'

TRACER='{"tracer":"erc7562Tracer"}'
#debug: use callTracer, to compare same tracing of real and local nodes
TRACER='{"tracer":"callTracer"}'
#TRACER='{}'

#an ep7 tx:
tx=0xe597ac9c9b13fe13a22dbb1a779b5d51306b5b05d4d2b978ce1b3119538fc202
echo tx = $tx
#ep8 tx
#tx=0x9e0fc69a69a4a48b276da45f258b28ef0726108acb7c919c612c49ada62a7ec0
#determine block number:
block=$(cast tx $tx -r sepolia --json | jq -r .blockNumber)
#on this block the nonce is already consumed, so run against previous block:
prevBlock=$(cast to-hex $(($(cast to-dec $block)-1)))
to=$(cast tx $tx --json | jq -r .to)
input=$(cast tx $tx --json | jq -r .input)

#run against latest block. should abort with "nonce" error

REQ="{\"gas\":\"0x100000\",\"to\":\"$to\",\"input\":\"$input\"}" 
err=$( cast rpc debug_traceCall $REQ latest $TRACER | jq -r .output )

err1=$(cast 4d $err)

echo "expected error: 'AA25 invalid account nonce', got: $err1"

echo tx block=$block
echo checking against prevBlock=$prevBlock

#now run against previous block. should succeed:
err=$( cast rpc debug_traceCall $REQ $prevBlock $TRACER | jq -r .output )

if [ "$err" == "null" ]; then

    echo success - traced with no error
else 

    err2=$(cast 4d $err)
    echo "expected success: got: $err2"
fi
