# api/ia_api/prometheus/Dockerfile - VERSION AVEC GESTION DES PERMISSIONS

# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# ===================================================================
# ===> SECTION DE GESTION DU SECRET CORRIGÉE <===
# ===================================================================
# 1. On passe temporairement à l'utilisateur 'root' pour avoir les droits d'écriture
USER root

# 2. On copie le fichier de configuration principal (en tant que root)
COPY prometheus.yml /etc/prometheus/prometheus.yml

# 3. On exécute la commande de création du secret (toujours en tant que root)
RUN --mount=type=secret,id=prometheus_password \
    cat /run/secrets/prometheus_password > /etc/prometheus/prometheus_password.secret

# 4. TRÈS IMPORTANT : On change le propriétaire du fichier de configuration ET du
#    nouveau fichier de secret pour qu'ils appartiennent à l'utilisateur 'nobody',
#    qui est l'utilisateur par défaut de l'image Prometheus.
RUN chown nobody:nobody /etc/prometheus/prometheus.yml /etc/prometheus/prometheus_password.secret

# 5. On repasse à l'utilisateur non-privilégié 'nobody' pour la suite,
#    ce qui est une bonne pratique de sécurité.
USER nobody
# ===================================================================