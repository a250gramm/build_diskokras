#!/bin/bash
# Скрипт для быстрой синхронизации локальных изменений на VPS
# Использование: bash sync_to_server.sh

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Пути
LOCAL_DIR="/Users/ivanussov/Desktop/Проекты/ps-b1/vsp_ps-b1_ubunta/pavel_sto/"
REMOTE_USER="ubuntu"
REMOTE_HOST="77.240.38.88"
REMOTE_DIR="/home/ubuntu/pavel_sto/"
SSH_KEY="/Users/ivanussov/Desktop/Проекты/ps-b1/vsp_ps-b1_ubunta/pavel_sto/ps_b1_key_new"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🚀 Синхронизация локальных изменений на VPS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📁 Локальная директория:${NC} $LOCAL_DIR"
echo -e "${BLUE}🌐 Удаленная директория:${NC} $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Проверка существования SSH ключа
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ Ошибка: SSH ключ не найден: $SSH_KEY${NC}"
    exit 1
fi

# Проверка существования локальной директории
if [ ! -d "$LOCAL_DIR" ]; then
    echo -e "${RED}❌ Ошибка: Локальная директория не найдена: $LOCAL_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Начинаю синхронизацию...${NC}"
echo ""

# Синхронизация с rsync
rsync -avz --progress \
  --delete \
  --exclude='node_modules/' \
  --exclude='.git/' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='.cache/' \
  --exclude='*.tmp' \
  --exclude='ps_b1_key_new' \
  --exclude='ps_b1_key_new.pub' \
  --exclude='sync_to_server.sh' \
  --exclude='sync_from_server.sh' \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  "$LOCAL_DIR" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"

# Проверка результата
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Синхронизация завершена успешно!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Показываем время последней синхронизации
    echo -e "${BLUE}🕐 Время синхронизации:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Ошибка при синхронизации!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi

