# Smart Vent Development Environment

Полностью готовое окружение для разработки и тестирования компонента Smart Ventilation Controller.

## 📦 Что включено

- **Home Assistant в Docker** - изолированная среда для разработки
- **Эмулированные устройства** - датчик влажности, Shelly входы, вентилятор
- **Тестовые скрипты** - для быстрого переключения режимов
- **Автоматизации** - симуляция различных сценариев
- **Детальное логирование** - для отладки компонента

## 🚀 Быстрый старт

### 1. Запуск Home Assistant

```bash
# Находясь в папке ha-dev-environment
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### 2. Первая настройка

1. Открой браузер: http://localhost:8123
2. Пройди первичную настройку HA:
   - Создай аккаунт администратора
   - Укажи имя дома: "Smart Vent Dev"
   - Остальное можно пропустить

3. После настройки перезапусти контейнер:
```bash
docker-compose restart
```

### 3. Проверка тестовых устройств

В интерфейсе HA должны появиться:

**Sensors:**
- `sensor.temperature_humidity_sensor_9970_humidity` - датчик влажности

**Binary Sensors:**
- `binary_sensor.shelly_input_0` - вход 0 Shelly
- `binary_sensor.shelly_input_1` - вход 1 Shelly

**Fan:**
- `fan.real_fan` - эмулированный вентилятор

**Helpers:**
- `input_number.test_humidity` - контроль влажности
- `input_number.fan_speed` - текущая скорость вентилятора
- `input_boolean.shelly_input_0` - контроль входа 0
- `input_boolean.shelly_input_1` - контроль входа 1

## 🔧 Разработка компонента

### Структура проекта

```
ha-dev-environment/
├── docker-compose.yml
├── config/
│   ├── configuration.yaml
│   └── (другие файлы HA)
└── custom_components/
    └── smart_vent/          ← Твой компонент здесь
        ├── __init__.py
        ├── manifest.json
        ├── const.py
        ├── coordinator.py
        ├── fan.py
        └── ...
```

### Workflow разработки

1. **Редактируй код:**
```bash
# Создай файлы компонента в custom_components/smart_vent/
nano custom_components/smart_vent/__init__.py
```

2. **Перезапусти HA:**
```bash
docker-compose restart

# Или только reload конфига (быстрее, но не всегда работает):
# Developer Tools > YAML > Check Configuration
# Developer Tools > YAML > Restart
```

3. **Смотри логи:**
```bash
# Все логи
docker-compose logs -f

# Только твоего компонента
docker-compose logs -f | grep smart_vent

# Или в UI: Settings > System > Logs
```

4. **Проверь состояние:**
```bash
# Developer Tools > States
# Найди entity fan.smart_vent и посмотри его атрибуты
```

## 🧪 Тестовые сценарии

### Сценарий 1: Тест ручного управления переключателем

**Через UI:**
1. Settings > Automations & Scenes > Scripts
2. Запусти скрипт "Set Switch to LOW"
3. Проверь, что вентилятор на 30%
4. Запусти "Set Switch to MID" → 52%
5. Запусти "Set Switch to BOOST" → 100%

**Через Developer Tools:**
```yaml
service: script.set_switch_low
```

### Сценарий 2: Тест автоматического boost

1. Установи переключатель в MID:
```yaml
service: script.set_switch_mid
```

2. Установи высокую влажность:
```yaml
service: input_boolean.turn_on
target:
  entity_id: input_boolean.quick_high_humidity
```

3. Подожди 20 секунд (check_interval)
4. Проверь, что вентилятор перешёл на 100% (boost)
5. Проверь `binary_sensor.smart_vent_auto_boost` = on

### Сценарий 3: Симуляция постепенного роста влажности

1. Установи переключатель в MID
2. Включи симуляцию:
```yaml
service: input_boolean.turn_on
target:
  entity_id: input_boolean.simulate_high_humidity
```
3. Наблюдай, как влажность растёт каждые 2 секунды
4. Когда достигнет >80%, должен сработать auto-boost

### Сценарий 4: Тест недопустимого состояния

```yaml
service: script.set_switch_invalid
```
- Компонент должен переключиться в LOW
- В логах должна быть ERROR запись

### Сценарий 5: Тест отмены auto-boost

1. Активируй auto-boost (сценарий 2)
2. Переключи в LOW:
```yaml
service: script.set_switch_low
```
3. Auto-boost должен отмениться немедленно

## 📊 Мониторинг и отладка

### Просмотр логов компонента

```bash
# В реальном времени
docker-compose logs -f | grep -i "smart_vent\|custom_components"

# Последние 100 строк
docker-compose logs --tail=100 | grep smart_vent
```

### Проверка состояния в UI

**Developer Tools > States:**
- Найди все entity связанные со smart_vent
- Проверь их атрибуты и состояния

**Developer Tools > Services:**
- Тестируй сервисы напрямую:
  - `smart_vent.set_mode`
  - `smart_vent.set_speed`
  - `smart_vent.force_boost`

### Debugging в коде

Добавь в код компонента:
```python
import logging
_LOGGER = logging.getLogger(__name__)

# Используй в коде
_LOGGER.debug("Debug message")
_LOGGER.info("Info message")
_LOGGER.warning("Warning message")
_LOGGER.error("Error message")
```

## 🎛️ Контроль тестовых устройств

### Через UI (Lovelace)

Создай тестовую панель:

```yaml
# В UI: Settings > Dashboards > + Add Dashboard
# Добавь карточки:

type: entities
title: Test Controls
entities:
  - entity: input_number.test_humidity
  - entity: input_boolean.shelly_input_0
  - entity: input_boolean.shelly_input_1
  - entity: fan.real_fan
```

### Через Developer Tools > States

Можешь вручную изменить любое состояние:
1. Developer Tools > States
2. Найди нужную entity
3. Кликни на неё
4. Измени state или атрибуты

## 🔄 Полезные команды Docker

```bash
# Остановить HA
docker-compose down

# Остановить и удалить все данные (полный сброс)
docker-compose down -v
rm -rf config/*

# Перезапустить
docker-compose restart

# Пересобрать и запустить заново
docker-compose up -d --force-recreate

# Зайти внутрь контейнера
docker exec -it ha-smart-vent-dev bash

# Просмотр ресурсов
docker stats ha-smart-vent-dev
```

## 📝 Подключение реальных устройств

Когда будешь готов тестировать с реальным оборудованием:

### 1. Подключение Shelly Dimmer

В `configuration.yaml` замени template fan на:

```yaml
# Добавь интеграцию Shelly через UI:
# Settings > Devices & Services > Add Integration > Shelly

# Или через YAML (если у тебя Shelly Gen1):
shelly:
  host: 192.168.1.XXX  # IP твоего Shelly
```

### 2. Подключение Xiaomi BLE

```yaml
# В конфиге уже должен быть bluetooth:
bluetooth:

# Интеграция Xiaomi BLE добавляется автоматически
# Settings > Devices & Services > найди Xiaomi устройства
```

### 3. Обновление конфигурации smart_vent

```yaml
smart_vent:
  fan_entity: fan.shelly_dimmer_XXX  # Реальный Shelly
  humidity_sensor: sensor.XXXX_humidity  # Реальный датчик
  input_0: binary_sensor.shelly_dimmer_XXX_input_0
  input_1: binary_sensor.shelly_dimmer_XXX_input_1
  speeds:
    low: 30
    mid: 52
    boost: 100
  check_interval: 20
  max_boosts_per_day: 5
```

## 🐛 Решение проблем

### HA не запускается

```bash
# Проверь логи
docker-compose logs

# Проверь конфиг
docker exec ha-smart-vent-dev hass --script check_config -c /config

# Полный перезапуск
docker-compose down
docker-compose up -d
```

### Компонент не загружается

1. Проверь структуру файлов в `custom_components/smart_vent/`
2. Проверь `manifest.json` - должен быть валидный JSON
3. Смотри логи: `docker-compose logs | grep -i error`
4. Проверь: Developer Tools > YAML > Check Configuration

### Изменения в коде не применяются

```bash
# Полная перезагрузка HA
docker-compose restart

# Или через UI:
# Developer Tools > YAML > Restart (выбери "Restart Home Assistant")
```

### Port 8123 занят

```bash
# Найди что занимает порт
sudo lsof -i :8123

# Останови конфликтующий процесс или измени порт в docker-compose.yml
```

## 📚 Полезные ссылки

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Development](https://developers.home-assistant.io/docs/creating_integration)
- [Template Platform](https://www.home-assistant.io/integrations/template/)
- [Logger Component](https://www.home-assistant.io/integrations/logger/)

## ✅ Чеклист перед началом разработки

- [ ] Docker и docker-compose установлены
- [ ] Запущен `docker-compose up -d`
- [ ] HA доступен на http://localhost:8123
- [ ] Пройдена первичная настройка
- [ ] Видны тестовые устройства в UI
- [ ] Папка `custom_components/smart_vent/` создана
- [ ] Логи показывают успешный запуск

Готов к разработке! 🚀