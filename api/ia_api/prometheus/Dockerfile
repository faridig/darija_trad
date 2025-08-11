# api/ia_api/prometheus/Dockerfile - Version Corrigée

# Utiliser l'image officielle de Prometheus comme base
FROM prom/prometheus:latest

# ===================================================================
# SECTION DE GESTION DU SECRET ET DES CONFIGURATIONS
# ===================================================================
# 1. On passe temporairement à l'utilisateur 'root' pour avoir les droits d'écriture
USER root

# 2. On copie le fichier de configuration principal (en tant que root)
COPY prometheus.yml /etc/prometheus/prometheus.yml

# 3. On utilise une syntaxe RUN pour créer le fichier de secret à partir d'un secret de build
RUN --mount=type=secret,id=prometheus_password \
    cat /run/secrets/prometheus_password > /etc/prometheus/prometheus_password.secret

# 4. TRÈS IMPORTANT : On s'assure que l'utilisateur non-privilégié 'nobody'
#    est bien le propriétaire de tous les fichiers de configuration.
RUN chown -R nobody:nobody /etc/prometheus

# 5. On repasse à l'utilisateur non-privilégié 'nobody' pour la suite,
#    ce qui est une bonne pratique de sécurité.
USER nobody
# ===================================================================

# ===================================================================
# ===> CORRECTION APPLIQUÉE ICI <====================================
# ===================================================================
# 6. On expose le port sur lequel Prometheus écoute.
EXPOSE 9090

# 7. On définit la commande pour lancer le serveur Prometheus.
#    Ceci est l'instruction qui manquait et qui empêchait le conteneur de
#    tourner en continu.
CMD [ \
  "--config.file=/etc/prometheus/prometheus.yml", \
  "--storage.tsdb.path=/prometheus", \
  "--web.console.libraries=/usr/share/prometheus/console_libraries", \
  "--web.console.templates=/usr/share/prometheus/consoles" \
]
# ===================================================================