#!/bin/bash

echo "Corriendo migraciones..."
python manage.py migrate

echo "Iniciando supervisor..."
exec supervisor -h