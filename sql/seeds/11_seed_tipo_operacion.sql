-- Generación de los tipos de operación agrícola
INSERT INTO tipo_operacion (id, operacion) VALUES 
(1, 'Siembra'),
(2, 'Cosecha'),
(3, 'Pulverización')
ON CONFLICT (id) DO NOTHING;