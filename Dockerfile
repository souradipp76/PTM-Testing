
FROM ubuntu:latest

ARG GITHUB_URL

# Install dependencies
RUN apt-get update && \
    apt-get install -y git python3 python3-pip && \
    pip3 install pytest && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone and setup repository
RUN git clone $GITHUB_URL ptm_repo && \
    cd ptm_repo && \
    pip3 install -e . \

CMD ["pytest", "ptm_repo/"]
