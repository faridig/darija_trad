# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# Copier le fichier de configuration de Prometheus
COPY prometheus.yml /etc/prometheus/prometheus.yml

RUN --mount=type=secret,id=prometheus_password \
    install -m 0400 /run/secrets/prometheus_password /etc/prometheus/prometheus_password.secret && \
    chown prometheus:prometheus /etc/prometheus/prometheus_password.secret || true