FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake make g++ gcc \
    python3 python3-dev python3-pip \
    bison flex libfl-dev swig \
    libpcap-dev libssl-dev zlib1g-dev \
    libmagic-dev libjemalloc-dev \
    libkrb5-dev libcurl4-openssl-dev \
    libunwind-dev libmaxminddb-dev \
    libc-ares-dev libc-ares2 \
    libprotobuf-dev protobuf-compiler \
    libzmq3-dev libbroker-dev \
    libreadline-dev \
    git wget curl pkg-config \
    ca-certificates \
    vim \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/zeek-src /opt/zeek/logs

WORKDIR /opt/zeek-src

RUN wget https://download.zeek.org/zeek-6.0.2.tar.gz && \
    tar -xzf zeek-6.0.2.tar.gz --strip-components=1

RUN ./configure --prefix=/usr/local/zeek && \
    make -j$(nproc) && \
    make install && \
    ldconfig

ENV PATH="/usr/local/zeek/bin:${PATH}"

COPY zeek /usr/local/zeek/share/zeek/site
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/zeek

ENTRYPOINT ["/entrypoint.sh"]
