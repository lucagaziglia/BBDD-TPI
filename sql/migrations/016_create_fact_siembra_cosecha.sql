CREATE TABLE fact_siembra_cosecha (
    id SERIAL PRIMARY KEY,
    maquinaria_id INTEGER REFERENCES dim_maquinaria(maquinaria_id),
    cultivo_id INTEGER REFERENCES dim_cultivo(cultivo_id),
    lote_id INTEGER REFERENCES dim_lote(lote_id),
    rendimiento_kg_ha NUMERIC,
    superficie_sembrada_cosechada_ha NUMERIC,
    costo_total NUMERIC,
    precio_venta_tn_prom NUMERIC,
    fecha DATE,
    id_tipo_operacion INTEGER REFERENCES tipo_operacion(id)
);