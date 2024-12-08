#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

# Удаляем контейнеры старые
sudo docker image rm -f ngw_kpt-front:1.0.0
sudo docker image rm -f ngw_kpt-back:1.0.0

# Устанавливаем образы из архива
sudo docker load < ngw_kpt-back.tar.gz
sudo docker load < ngw_kpt-front.tar.gz

# Запускаем
sudo docker compose up -d
