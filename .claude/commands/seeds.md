# Seeds Command

Genera y carga datos sintéticos para poblar el datawarehouse.

## Uso
```
/seeds
```

## Comportamiento
1. Genera datos sintéticos con Faker + datos reales MAGYP
2. Inserta datos en las dimensiones y tabla de hechos
3. Pobla las colecciones MongoDB con lecturas de sensores
4. Configura keys Redis con estado inicial
