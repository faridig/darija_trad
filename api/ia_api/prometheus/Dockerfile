# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# Copier le fichier de configuration de Prometheus
COPY prometheus.yml /etc/prometheus/prometheus.yml

RUN --mount=type=secret,id=prometheus_password \
    cat /run/secrets/prometheus_password > /etc/prometheus/prometheus_password.secret