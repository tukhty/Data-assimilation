# ARCHITECTURE.md: Архитектура MVP системы подбора режимов ферментации

## 1. Общая схема потоков данных
Поток данных представляет собой замкнутый цикл от измерений к операционным рекомендациям:

`Измерения (Digital Twin/Lab)` $\rightarrow$ `PostgreSQL (Raw Data)` $\rightarrow$ `MND-Ассимилятор` $\rightarrow$ `Траектории (Assimilated)` $\rightarrow$ `Bayesian Optimizer (skopt)` $\rightarrow$ `Профиль D(t)` $\rightarrow$ `Финмодель` $\rightarrow$ `Рекомендация` $\rightarrow$ `n8n` $\rightarrow$ `Оператор`

## 2. Схема базы данных (PostgreSQL)

### ER-диаграмма (Mermaid)
```mermaid
erDiagram
    BATCH ||--o{ MEASUREMENT : "has"
    BATCH ||--o{ TRAJECTORY : "produces"
    BATCH ||--|| PARAM_ESTIMATE : "estimated_by"
    BATCH ||--|| OPTIMIZATION_RESULT : "optimized_to"
    OPTIMIZATION_RESULT ||--|| FINANCIAL_METRICS : "evaluates"

    BATCH {
        uuid id PK
        string batch_id "External ID"
        timestamp start_time
        timestamp end_time
        string status "active/completed/failed"
    }

    MEASUREMENT {
        bigint id PK
        uuid batch_id FK
        timestamp timestamp
        float biomass_x "Measured X"
        float substrate_s "Measured S"
        float other_val "Other lab metrics"
    }

    TRAJECTORY {
        bigint id PK
        uuid batch_id FK
        float time_offset "t from start"
        float x_hat "Assimilated X"
        float s_hat "Assimilated S"
        float y_hat "Assimilated Y"
        float a_hat "Assimilated A"
        float b_hat "Assimilated B"
    }

    PARAM_ESTIMATE {
        uuid batch_id PK, FK
        float y0
        float a0
        float b0
        float c0
        float c1
        float c2
        float c3
        float c4
        float c5
    }

    OPTIMIZATION_RESULT {
        uuid batch_id PK, FK
        jsonb optimal_d_profile "Hyperbola params"
        float expected_npv
        timestamp created_at
    }

    FINANCIAL_METRICS {
        uuid opt_id PK, FK
        float cost_per_kg "Rub/kg protein"
        float electricity_cost
        float methane_cost
        float margin
        float break_even_point
    }
```

## 3. Интерфейсы модулей (API)

### 3.1. `ode_model.py`
- **Input:** `(t, initial_state, params)`
- **Output:** `trajectories (ndarray)`
- **Responsibility:** Чистое решение системы ОДУ.

### 3.2. `mnd_assimilation.py`
- **Input:** `measurements (CSV/SQL) + initial_guess`
- **Output:** `best_params (dict), assimilated_trajectories (ndarray)`
- **Responsibility:** Поиск параметров $\theta$, минимизирующих RMSE между моделью и измерениями с использованием MND.

### 3.3. `regime_optimizer.py`
- **Input:** `current_params (dict), constraints`
- **Output:** `optimal_d_params (list), predicted_reward (NPV)`
- **Responsibility:** Поиск оптимального профиля $D(t)$ через `skopt.gp_minimize`.

### 3.4. `financial_model.py`
- **Input:** `trajectories, optimal_d, pricing_config`
- **Output:** `FinancialReport (object)`
- **Responsibility:** Перевод биохимических показателей в денежный эквивалент (NPV, OPEX).

## 4. Роль Claude Code в системе
Я выступаю в роли **Агент-Оркестратора**:
1. **Запуск:** Через n8n вызываю `run_pipeline.py`.
2. **Контроль:** Мониторю логи выполнения каждого модуля.
3. **Интерпретация:** Анализирую `FinancialReport` и сравниваю его с текущим режимом.
4. **Генерация:** Формирую финальный текстовый отчет для оператора:
   - "Рекомендую изменить профиль разбавления на [X], так как это снизит себестоимость на [Y] руб/кг при сохранении стабильности биомассы."
5. **Архивация:** Обеспечиваю запись всех результатов в PostgreSQL.
