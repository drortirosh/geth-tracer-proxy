import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Fetch the environment variables
REMOTE_NODE = os.getenv("REMOTE_NODE")
NATIVE_TRACER = os.getenv("NATIVE_TRACER")
DEBUG = len(os.getenv("DEBUG", "")) > 0
LOCAL_NODE="http://localhost:18545"

print("REMOTE_NODE=",REMOTE_NODE)
print("NATIVE_TRACER=", NATIVE_TRACER)

if not REMOTE_NODE or not NATIVE_TRACER:
    raise ValueError("Both REMOTE_NODE and NATIVE_TRACER must be set.")


#for debug: remove "code" entries
def debug_clean_code(data):
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "code":
                result[key] = "..."
            else:
                result[key] = debug_clean_code(value)
        return result
    elif isinstance(data, list):
        return [debug_clean_code(item) for item in data]
    else:
        return data

def noNulls(obj):
    return  {key: value for key, value in obj.items() if value is not None}

def modify_trace_request(payload):
    debug=app.logger.debug
    """Modify the request by replacing the tracer and processing overrides."""
    try:
        method = payload.get("method")
        params = payload.get("params", [])

        # Determine options index (2nd for traceTransaction, 3rd for traceCall)
        options_index = 1 if method == "debug_traceTransaction" else 2

        options= dict()

        if len(params) > options_index and isinstance(params[options_index], dict):
            options = params[options_index]
        else: 
            params.append(options)

        tracer = options.get("tracer")
        tracerConfig = options.get("tracerConfig")

        # on all tracers, not only "native"
        if options.get("tracer") == NATIVE_TRACER or NATIVE_TRACER == "*":
            debug( "using native tracer for %s", tracer)
            #only traceCall...
            prestatePayload=dict( jsonrpc=payload["jsonrpc"], id=payload["id"], 
                method=method, params= params[:2] + [dict(tracer="prestateTracer")] )

            debug("sending remote prestateTracer %s", prestatePayload)
            # Forward modified request to the remote node
            response = requests.post(REMOTE_NODE, json=prestatePayload).json()

            # debug("prestate result=%s", response)
            # Extract statesOverride from response
            states_override = response.get("result", {})

            # Modify original request's statesOverride structure
            orig_states_override = options.get("stateOverrides", {})
            # debug( "original stateOverrides %s", orig_states_override)
            for address, value in states_override.items():
                #don't state-override precompiles.
                if int(address,0) < 512:
                  continue

                entry = orig_states_override.get(address, {})
                # copy over values from prestate, but don't override existing values:
                # (nonce is converted first to hex, and "state" is named "storage" in the prestateTracer output)
                if "nonce" in value and not "nonce" in entry:
                    entry["nonce"] = hex(value["nonce"])  # prestate has nonce as number, convert to hex
                if "storage" in value and not "state" in entry:
                    entry["state"] = value["storage"]  # Rename "storage" to "state"
                if "code" in value and not "code" in entry:
                    entry["code"] = value["code"]
                if "balance" in value and not "balance" in entry:
                    entry["balance"] = value["balance"]
                orig_states_override[address] = entry

            new_options=noNulls(dict(
                stateOverrides = orig_states_override,
                tracer = tracer,
                tracerConfig = tracerConfig,
                blockoverrides = dict(number="0x878604")
            ))

            tx = params[0]
            # Forward modified request to local geth
            #only tracecall
            newpayload=dict( jsonrpc=payload["jsonrpc"], id=payload["id"], 
                method=method, params=[tx,"latest",new_options])
            # debug(">> %s", debug_clean_code(newpayload))
            resp = requests.post(LOCAL_NODE, json=newpayload).json()
            # debug("<< resp=%s", resp)
            return resp
    
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

@app.route("/local", methods=["POST"])
def local():
    payload = request.get_json()
    print("running locally")
    return requests.post(LOCAL_NODE, json=payload).json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8545, debug=DEBUG)

