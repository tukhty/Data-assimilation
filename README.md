# Биопротеин MVP — Автоматизация подбора режимов ферментации

MVP-система для оптимизации процесса культивирования метанотрофных бактерий (*Methylococcus capsulatus*) в струйном ферментере. Система восстанавливает текущее состояние процесса, подбирает оптимальный профиль протока $D(t)$ и оценивает экономическую эффективность партии.

## Архитектура

Измерения (Digital Twin / Lab)
│
▼
PostgreSQL (Raw Data)
│
▼
MND-Ассимилятор ───► Траектории X, S, A, B, Y
│
▼
Bayesian Optimizer (skopt) ───► Оптимальный профиль D(t)
│
▼
Финансовая модель (BatchEconomics) ───► NPV, себестоимость
│
▼
Redis Pub/Sub ───► Уведомление оператору (n8n)


### Ключевые модули

| Модуль | Файл | Назначение |
|--------|------|------------|
| ODE-модель | `ode_model.py` | Система 5 ОДУ: биомасса X, субстрат S, спутник Y, метаболиты A, B |
| Ассимиляция | `mnd_assimilation.py` | Восстановление параметров по измерениям (MND-алгоритм) |
| Оптимизатор | `regime_optimizer.py` | Байесовский поиск оптимального профиля протока $D(t)$ |
| Финмодель | `financial_model.py` | Расчёт NPV, себестоимости руб/кг белка, маржинальности |
| Экспорт | `export_finance.py` | Выгрузка результатов в формат Google Sheets (.xlsx) |
| Пайплайн | `run_pipeline_redis.py` | Основной пайплайн: ассимиляция → оптимизация → финмодель (через Redis) |
| Пайплайн | `run_pipeline_postgres.py` | Альтернативный пайплайн (через PostgreSQL polling) |

### Варианты коммутации данных

- **Вариант Б (основной, `variant-b-redis`):** Redis Pub/Sub — минимальная задержка, событийная модель. Рекомендован для production.
- **Вариант А (`variant-a-postgres`):** PostgreSQL polling — проще в отладке, не требует Redis.

## Быстрый старт

### Требования
- Windows 11 / Ubuntu Server 26.04
- Python 3.10+
- Docker Desktop
- n8n (опционально, для уведомлений)

### 1. Клонирование и установка

git clone https://github.com/tukhty/Data-assimilation.git
cd Data-assimilation
pip install -r requirements.txt

### 2. Запуск инфраструктуры (PostgreSQL + Redis)

docker-compose up -d

### 3. Проверка модулей

python test_ode.py        # Верификация ODE-модели
python test_mnd.py        # Проверка ассимиляции данных
python test_finmodel.py   # Проверка финансовой модели
python test_optimizer.py  # Проверка оптимизатора

### 4. Сквозной тест (E2E)

python test_e2e.py

### 5. Запуск полного пайплайна

python run_pipeline_redis.py # Основной вариант (Redis)

python run_pipeline_postgres.py # Альтернативный вариант (PostgreSQL)

### 6. Экспорт в Google Sheets (опционально)

python export_finance.py # Сгенерированный файл financial_report.xlsx импортируется в Google Sheets: Файл → Импортировать → Загрузить.

Результаты тестов (v0.6-opt)
Метрика	Базовый режим (D=0.25)	Оптимизированный режим
Прибыль (NPV батча)	-51 542 руб	+779 291 руб
Себестоимость белка	4 177 руб/кг	149 руб/кг
Выход белка	19.26 кг	зависит от профиля D(t)

Конкуренты и бенчмарки
Компания	Технология	OPEX (оценка)
Unibio (Дания/РФ)	Петлевой U-Loop	~$800-1000/т
Calysta (США)	Петлевой	~$900-1100/т
Биопротеин (мы)	Струйный	потенциально ниже за счёт энергоэффективности

### 7. Метрики скорости пайплайна

Все переходы между шлюзами фиксируются в Redis с тайм-стемпами:
pipeline:timestamp:assimilation_start
pipeline:timestamp:optimization_start
pipeline:timestamp:finance_start
pipeline:timestamp:done

95% времени цикла — расчёт ОДУ в оптимизаторе. Передача через Redis — миллисекунды.

### 8. Журналы проекта

WORKLOG.md — хронология разработки
DECISIONS.md — реестр архитектурных решений
DESIGN.md — допущения и принципы
AUDIT.md — карта исходного кода
ARCHITECTURE.md — схема БД Snowflake и потоки данных
DATA_INFRASTRUCTURE.md — инфраструктура данных
USER_GUIDE.md — инструкция пользователя

### 9. Лицензия и ссылки

Исходный репозиторий коллег: https://github.com/Run4rest/Data-assimilation
Форк проекта: https://github.com/tukhty/Data-assimilation
Контакты: ershovsv@yandex.ru







