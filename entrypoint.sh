#!/bin/bash

echo "Corriendo migraciones..."
python manage.py migrate

echo "Iniciando supervisor..."
exec supervisord -c /etc/supervisor/conf.d/supervisor.conf