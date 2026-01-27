#!/bin/bash
# Быстрая синхронизация только директории /public/area на VPS

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

LOCAL_DIR="/Users/ivanussov/Desktop/Проекты/ps-b1/vsp_ps-b1_ubunta/pavel_sto/public/area/"
REMOTE_USER="ubuntu"
REMOTE_HOST="77.240.38.88"
REMOTE_AREA_DIR="/home/ubuntu/pavel_sto/public/area/"
REMOTE_WEB_AREA_DIR="/var/www/html/pavel_sto/area/"
SSH_KEY="/Users/ivanussov/Desktop/Проекты/ps-b1/vsp_ps-b1_ubunta/pavel_sto/public/area/z_door/ps_b1_key_new"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🚀 Синхронизация директории AREA на VPS${NC}"
echo -e "${BLUE}📁 Локально:${NC} ${LOCAL_DIR}"
echo -e "${BLUE}🌐 Удалённо:${NC} ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_AREA_DIR}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "${SSH_KEY}" ]; then
    echo -e "${RED}❌ SSH ключ не найден: ${SSH_KEY}${NC}"
    exit 1
fi

if [ ! -d "${LOCAL_DIR}" ]; then
    echo -e "${RED}❌ Локальная директория не найдена: ${LOCAL_DIR}${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Отправляю файлы в ${REMOTE_AREA_DIR}...${NC}"

rsync -avz --progress \
  --delete \
  --exclude='block/' \
  --exclude='area_settings.json' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='*.tmp' \
  -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
  "${LOCAL_DIR}" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_AREA_DIR}"

rsync -avz --progress \
  --delete \
  --exclude='area_settings.json' \
  -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
  "${LOCAL_DIR}block/test_1/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_AREA_DIR}block/test_1/"

echo -e "${YELLOW}🔁 Обновляю веб-копию в ${REMOTE_WEB_AREA_DIR}...${NC}"

ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo rsync -av --delete --exclude='block/' --exclude='area_settings.json' ${REMOTE_AREA_DIR} ${REMOTE_WEB_AREA_DIR} && \
   sudo rsync -av --delete ${REMOTE_AREA_DIR}block/test_1/ ${REMOTE_WEB_AREA_DIR}block/test_1/ && \
   sudo chown -R www-data:www-data ${REMOTE_WEB_AREA_DIR}"

echo -e "${YELLOW}🔁 Запускаю полный деплой через sync_to_www.sh...${NC}"
ssh -tt -i "${SSH_KEY}" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo bash /home/ubuntu/sync_to_www.sh"

echo -e "${GREEN}✅ Готово!${NC}"
echo -e "${BLUE}🕐 Время:${NC} $(date '+%Y-%m-%d %H:%M:%S')"

