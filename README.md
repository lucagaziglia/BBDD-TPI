# AgTech Datawarehouse - TP Final BBDD

Bienvenido al repositorio del Trabajo Práctico Final de la materia Bases de Datos (UNSAM).

## Setup e Instrucciones

1. **Clonar repositorio e instalar dependencias:**
   ```bash
   git clone <repo_url>
   cd BBDD-TPI
   pip install -r requirements.txt
   ```

2. **Configuración de Variables de Entorno:**
   Copia el archivo `.env.example` a `.env` y completa con las credenciales de los diferentes motores:
   - Supabase (PostgreSQL)
   - MongoDB Atlas
   - Redis Cloud
   ```bash
   cp .env.example .env
   ```

3. **Ejecutar el Pipeline:**
   Puedes utilizar Claude Code con los comandos definidos en `.claude/commands/` o ejecutar directamente Python:
   ```bash
   python etl/pipeline.py
   ```

Para más contexto y convenciones, lee el archivo `CLAUDE.md`.
