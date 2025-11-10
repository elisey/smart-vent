#!/bin/bash

# Скрипт быстрого запуска окружения разработки Smart Vent

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Smart Vent Dev Environment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    echo "Установи Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose не установлен!${NC}"
    echo "Установи docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker и docker-compose найдены${NC}"
echo ""

# Проверка структуры
if [ ! -f "docker-compose.yaml" ]; then
    echo -e "${RED}❌ docker-compose.yaml не найден!${NC}"
    echo "Запусти скрипт из папки ha-dev-environment"
    exit 1
fi

echo -e "${BLUE}📁 Создание необходимых папок...${NC}"
mkdir -p config custom_components/smart_vent

echo -e "${GREEN}✅ Папки созданы${NC}"
echo ""

# Проверка, запущен ли контейнер
if docker ps | grep -q ha-smart-vent-dev; then
    echo -e "${YELLOW}⚠️  Контейнер уже запущен${NC}"
    echo ""
    read -p "Хочешь перезапустить? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🔄 Перезапуск...${NC}"
        docker-compose restart
    fi
else
    echo -e "${BLUE}🚀 Запуск Home Assistant...${NC}"
    docker-compose up -d
    
    echo ""
    echo -e "${YELLOW}⏳ Ожидание запуска HA (это может занять 1-2 минуты)...${NC}"
    
    # Ждём запуска
    MAX_ATTEMPTS=60
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if docker-compose logs | grep -q "Home Assistant initialized"; then
            echo -e "${GREEN}✅ Home Assistant запущен!${NC}"
            break
        fi
        
        echo -n "."
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo ""
        echo -e "${RED}⚠️  HA не запустился за ожидаемое время${NC}"
        echo "Проверь логи: docker-compose logs"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Всё готово!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}🌐 Web UI:${NC} http://localhost:8123"
echo ""
echo -e "${YELLOW}📝 Полезные команды:${NC}"
echo -e "  ${BLUE}Логи:${NC}           docker-compose logs -f"
echo -e "  ${BLUE}Перезапуск:${NC}     docker-compose restart"
echo -e "  ${BLUE}Остановка:${NC}      docker-compose down"
echo -e "  ${BLUE}Статус:${NC}         docker-compose ps"
echo ""
echo -e "${YELLOW}🔧 Разработка:${NC}"
echo -e "  1. Создай компонент в: ${BLUE}custom_components/smart_vent/${NC}"
echo -e "  2. Перезапусти HA: ${BLUE}docker-compose restart${NC}"
echo -e "  3. Проверь логи на ошибки"
echo ""
echo -e "${YELLOW}📚 Документация:${NC} README.md"
echo ""

# Открыть браузер (опционально)
read -p "Открыть браузер? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8123
    elif command -v open &> /dev/null; then
        open http://localhost:8123
    else
        echo "Открой вручную: http://localhost:8123"
    fi
fi

echo -e "${GREEN}Удачи в разработке! 🚀${NC}"
