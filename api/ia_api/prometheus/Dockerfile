# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# Copier le fichier de configuration de Prometheus
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Utiliser --mount=type=secret pour injecter le mot de passe de manière sécurisée
# Le 'id=prometheus_password' doit correspondre à ce qui sera passé par GitHub Actions
# Le contenu du secret sera temporairement disponible sous /run/secrets/prometheus_password
RUN --mount=type=secret,id=prometheus_password \
    cat /run/secrets/prometheus_password > /etc/prometheus/prometheus_password.secret

# Note : le fichier `prometheus_password.secret` original NE DOIT PAS être commité dans Git.