# Schema Command

Ejecuta las migraciones DDL del directorio `sql/schema/` contra la base de datos Supabase.

## Uso
```
/schema
```

## Comportamiento
1. Lee todos los archivos `.sql` en `sql/schema/` en orden alfabético
2. Ejecuta cada DDL contra la conexión Supabase
3. Reporta tablas creadas/modificadas
