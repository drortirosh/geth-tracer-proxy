FROM erc7562-geth

# Set working directory
WORKDIR /geth

# Install dependencies
RUN apk add --no-cache python3 py3-pip py3-requests py3-flask curl jq

# Install Python packages (requests)
#RUN pip3 install requests

# Copy the necessary files
COPY genesis.json ./
COPY entrypoint.sh /entrypoint.sh
COPY proxy.py /proxy.py
RUN chmod +x /entrypoint.sh

# Expose necessary ports
EXPOSE 8545 8546 30303 30303/udp

# Set environment variables for remote node and tracer
ENV REMOTE_NODE=""
ENV NATIVE_TRACER="erc7562Tracer"

# Start the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

