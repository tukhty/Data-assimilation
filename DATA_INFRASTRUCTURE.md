# DATA_INFRASTRUCTURE.md: Инфраструктура данных MVP

## 1. Архитектура БД (PostgreSQL Snowflake Schema)

Для обеспечения масштабируемости и чистоты данных используется схема Snowflake (Снежинка). 

### Слой 1: Raw / Landing (ODS)
Здесь хранятся сырые данные в формате "as is" от датчиков и лаборатории.
- `stg_measurements`: (timestamp, sensor_id, raw_value).

### Слой 2: Normalized / Core (SCD)
Данные, очищенные и приведенные к единым единицам измерения.
- `dim_batches`: (batch_id, start_time, end_time, status).
- `fact_measurements`: (measurement_id, batch_id, timestamp, x_val, s_val).
- `dim_params`: (param_id, param_name, unit).

### Слой 3: Analytical / Marts (Processed)
Результаты работы модулей (Цифрового двойника).
- `fact_assimilated_trajectories`: (trajectory_id, batch_id, time, s_hat, x_hat, y_hat, a_hat, b_hat).
- `fact_optimal_regimes`: (opt_id, batch_id, coeff_vector, expected_npv).
- `fact_financial_reports`: (report_id, opt_id, cost_per_kg, margin, revenue).

## 2. Коммутация потоковых данных (Выбор вариантов)

Для обеспечения обмена данными между шлюзами (Ассимилятор $\leftrightarrow$ Оптимизатор $\leftrightarrow$ Финмодель) предлагаю два варианта реализации:

### Вариант А: "Легкий" (PostgreSQL + Polling)
- **Стек:** PostgreSQL $\rightarrow$ Python (Pandas/SQLAlchemy).
- **Механика:** Модули пишут результаты в таблицы-очереди (Status Tables). Следующий модуль опрашивает БД на наличие новых записей с флагом `ready`.
- **Плюсы:** Простота реализации, надежность, прозрачность.
- **Минусы:** Задержка (latency) из-за опроса БД.

### Вариант Б: "Событийный" (Redis + Pub/Sub)
- **Стек:** Redis (as Message Broker) $\rightarrow$ Python.
- **Механика:** Каждый модуль является Producer/Consumer. Ассимилятор публикует событие `batch.assimilated`, Оптимизатор подписывается на него и начинает расчет.
- **Плюсы:** Минимальная задержка, высокая скорость обмена, событийная архитектура.
- **Минусы:** Дополнительный компонент в инфраструктуре (Redis контейнер).

**Моя рекомендация для MVP:** Вариант А (PostgreSQL), так как он полностью закрывает потребности текущих темпов расчета и обеспечивает максимальную надежность данных.

## 3. Развертывание (Docker)
Развертывание будет осуществляться через `docker-compose.yml`, поднимающий:
- Контейнер PostgreSQL (с предустановленной схемой Snowflake).
- Контейнер Python-App (с установленным окружением и `requirements.txt`).
- (Опционально) Redis, если будет выбран Вариант Б.
