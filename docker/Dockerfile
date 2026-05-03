FROM ubuntu:24.04
LABEL description="RNAS — RADIUS Network Access Server Simulation Platform"

RUN apt-get update && apt-get install -y \
    python3 python3-pip accel-ppp dnsmasq iptables \
    strongswan wireguard-tools openvpn keepalived snmpd \
    isc-dhcp-server freeradius postgresql \
    && rm -rf /var/lib/apt/lists/*

COPY configs/ /etc/rnas/
COPY cmd/rnas-config/rnas_config.py /usr/bin/rnas-config
COPY web/ /opt/rnas-web/
COPY scripts/ /opt/rnas-scripts/
COPY systemd/ /etc/systemd/system/

RUN mkdir -p /var/run/rnas /var/log/accel-ppp /etc/rnas/ssl

EXPOSE 1812/udp 1813/udp 3799/udp 1701/udp 1723/tcp 443/tcp 8099/tcp

CMD ["/opt/rnas-scripts/entrypoint.sh"]
