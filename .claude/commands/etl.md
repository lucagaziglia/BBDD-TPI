# ETL Command

Ejecuta el pipeline ETL completo: extracción → transformación → carga.

## Uso
```
/etl
```

## Comportamiento
1. Ejecuta los extractors de MongoDB y Redis
2. Aplica las transformaciones correspondientes
3. Carga los datos transformados en Supabase/PostgreSQL
4. Reporta filas procesadas por cada paso
