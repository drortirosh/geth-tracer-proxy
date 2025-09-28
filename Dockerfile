FROM ghcr.io/foundry-rs/foundry:latest AS foundry

RUN mkdir /tmp/gnu-libs
RUN mkdir /tmp/bin
RUN cp /lib/x86_64-linux-gnu/*.so* /tmp/gnu-libs
RUN cp /usr/local/bin/cast /usr/local/bin/anvil /tmp/bin

FROM ethereum/client-go:release-1.16
#when built locally:
#FROM erc7562-geth

# Set working directory
WORKDIR /geth

# Install dependencies
RUN apk add --no-cache python3 py3-pip py3-requests py3-flask curl jq py3-gunicorn

# Install Python packages (requests)
#RUN pip3 install requests

# Copy the necessary files
COPY genesis.json.templ ./
COPY entrypoint.sh /entrypoint.sh
COPY gunicorn.conf.py /gunicorn.conf.py
COPY proxy.py /proxy.py
RUN chmod +x /entrypoint.sh

#copy anvil,cast
COPY --from=foundry /tmp/bin/ /usr/local/bin/
COPY --from=foundry /lib64/ld-linux-x86-64.so.2 /lib64/
COPY --from=foundry /tmp/gnu-libs/ /lib/x86_64-linux-gnu/

# Expose necessary ports
#EXPOSE 8545 8546 30303 30303/udp

# Set environment variables for remote node and tracer
ENV REMOTE_NODE=""
ENV NATIVE_TRACER="erc7562Tracer"

# Start the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

