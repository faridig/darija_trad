# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# Copier le fichier de configuration de Prometheus
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Copier le fichier contenant le mot de passe pour le basic_auth
# Note : assurez-vous que les permissions sont correctes si nécessaire.
COPY prometheus_password.secret /etc/prometheus/prometheus_password.secret