FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    supervisor \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Caddy
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && \
    apt-get install -y caddy && \
    rm -rf /var/lib/apt/lists/*

# Install Xray from GitHub releases (avoid systemd issues in container)
RUN mkdir -p /usr/local/bin && \
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep tag_name | cut -d'"' -f4) && \
        ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m) && \
        case "$ARCH" in \
            amd64) ASSET="Xray-linux-64.zip" ;; \
            x86_64) ASSET="Xray-linux-64.zip" ;; \
            arm64) ASSET="Xray-linux-arm64-v8a.zip" ;; \
            aarch64) ASSET="Xray-linux-arm64-v8a.zip" ;; \
            *) ASSET="Xray-linux-64.zip" ;; \
        esac && \
        echo "Downloading ${ASSET} for architecture ${ARCH}" && \
        curl -L "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/${ASSET}" -o /tmp/xray.zip && \
    cd /tmp && unzip -o xray.zip && \
    mv xray /usr/local/bin/ && \
    chmod +x /usr/local/bin/xray && \
    rm -f /tmp/xray.zip /tmp/geo* && \
    /usr/local/bin/xray -version

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directories and symlinks for easy access
RUN mkdir -p /app/data/xray \
             /app/data/caddy/conf.d \
             /app/data/logs && \
    # Create symlinks for compatibility with standard paths
    mkdir -p /etc/caddy/conf.d && \
    mkdir -p /var/log/supervisor

# Copy supervisord configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8000 443 80

# Set environment variable for container mode
ENV DEPLOYMENT_MODE=container \
    XRAY_CONFIG_PATH=/app/data/xray/config.json \
    CADDY_CONFIG_PATH=/app/data/caddy/Caddyfile \
    CADDY_CONF_D_PATH=/app/data/caddy/conf.d/xray-auto.caddy

# Start supervisord as the container's main process
# Uses the copied supervisord configuration at /etc/supervisor/conf.d/supervisord.conf
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
