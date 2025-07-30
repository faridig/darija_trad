# api/ia_api/grafana/Dockerfile (Version Corrigée)

FROM grafana/grafana:latest

# Copier le fichier de config de la datasource de production
COPY provisioning/datasources/prometheus.yaml /etc/grafana/provisioning/datasources/prometheus.yaml

# Copier le fichier de config des dashboards (celui qui liste les dashboards à charger)
COPY provisioning/dashboards/sample.yaml /etc/grafana/provisioning/dashboards/sample.yaml

# Copier le dashboard JSON lui-même
COPY provisioning/dashboards/nllb_darija_dashboard.json /etc/grafana/provisioning/dashboards/nllb_darija_dashboard.json