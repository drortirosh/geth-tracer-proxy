import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Fetch the environment variables
REMOTE_NODE = os.getenv("REMOTE_NODE")
NATIVE_TRACER = os.getenv("NATIVE_TRACER")
LOCAL_NODE="http://localhost:18545"

print("REMOTE_NODE=",REMOTE_NODE)
print("NATIVE_TRACER=", NATIVE_TRACER)

if not REMOTE_NODE or not NATIVE_TRACER:
    raise ValueError("Both REMOTE_NODE and NATIVE_TRACER must be set.")

def modify_trace_request(payload):
    debug=app.logger.debug
    """Modify the request by replacing the tracer and processing overrides."""
    try:
        method = payload.get("method")
        params = payload.get("params", [])
        debug("method=%s %s", method, params)

        # Determine options index (2nd for traceTransaction, 3rd for traceCall)
        options_index = 1 if method == "debug_traceTransaction" else 2

        if len(params) > options_index and isinstance(params[options_index], dict):
            options = params[options_index]

            if options.get("tracer") == NATIVE_TRACER:
                debug( "using native tracer")
                # Replace "tracer" with "prestateTracer"
                options["tracer"] = "prestateTracer"

                # Forward modified request to the remote node
                response = requests.post(REMOTE_NODE, json=payload).json()

                # Extract statesOverride from response
                states_override = response.get("result", {})

                # Modify statesOverride structure
                modified_states_override = {}
                for address, value in states_override.items():
                    if "nonce" in value:
                        value["nonce"] = hex(value["nonce"])  # Convert nonce to hex
                    if "storage" in value:
                        value["state"] = value.pop("storage")  # Rename "storage" to "state"
                    modified_states_override[address] = value

                new_options=dict(
                    tracer = NATIVE_TRACER,
                    stateOverrides=modified_states_override
                )

                tx = params[0]
                # Forward modified request to local geth
                newpayload=dict( jsonrpc=payload["jsonrpc"], id=payload["id"], 
                    method=payload["method"], params=[tx,"latest",new_options])
                return requests.post(LOCAL_NODE, json=newpayload).json()
    
    except Exception as e:
        return {"error": str(e)}

    return requests.post(REMOTE_NODE, json=payload).json()

@app.route("/", methods=["POST"])
def proxy():
    payload = request.get_json()
    if not payload:
        return {"error": "Invalid request"}, 400

    method = payload.get("method", "")
    if method in ["debug_traceCall", "debug_traceTransaction"]:
        return modify_trace_request(payload)

    # Forward all other requests to the remote node
    return requests.post(REMOTE_NODE, json=payload).json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8545, debug=True)

