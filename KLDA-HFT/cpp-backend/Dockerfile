# KLDA-HFT C++ Backend - Docker Image
FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    git \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source files
COPY src/ /app/src/
COPY include/ /app/include/
COPY config.json /app/
COPY CMakeLists.txt /app/

# Create build directory
RUN mkdir -p build

# Configure and build
WORKDIR /app/build
RUN cmake .. && make

# Set working directory back to app
WORKDIR /app

# Expose API port (for future REST API)
EXPOSE 8081

# Run the live tracker
CMD ["./build/live_tracker"]
