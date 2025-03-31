# langchain_sql
 Proyecto para practicar con la IA, transformar lenguaje humano a consultas SQL
# 🌐 **API de Consulta Inteligente** 🧠

¡Bienvenido a la **API de Consulta Inteligente**! Este proyecto es una herramienta que combina el poder de la Inteligencia Artificial con consultas SQL a bases de datos. Permite recibir un texto en lenguaje natural, procesarlo con IA para interpretar la solicitud, realizar una consulta SQL sobre una base de datos y devolver los resultados en formato JSON. ¡Perfecto para integrar funcionalidades inteligentes a tus aplicaciones!

<p align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzgxcmJ5a3NrbWh3d3ppZjF5Znc0cWszZDA1Zmo3ZWQyZm5saHU2biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/qgQUggAC3Pfv687qPC/giphy.gif" alt="Simulación de consulta IA" width="300" height="200">
</p>

## ✨ **Características Principales**

- **Interpretación de consultas en lenguaje natural**: Utiliza IA para procesar entradas de texto en lenguaje humano y convertirlas en consultas SQL.
- **Consultas SQL automáticas**: Una vez procesada la solicitud, se genera y ejecuta una consulta SQL en tu base de datos.
- **Respuesta en JSON**: Los resultados de la consulta se devuelven en formato JSON, listos para ser usados por aplicaciones frontend o para análisis.
- **Soporte multilingüe**: La API puede recibir texto en diferentes idiomas y adaptarse a ellos para generar las consultas correctas.

## 🛠️ **Stack Tecnológico**

- **Python**: Motor principal del servidor API con soporte para IA.
- **FastAPI**: Framework para la creación rápida de APIs, con rendimiento y facilidad de uso.
- **OpenAI**: API de procesamiento de lenguaje natural que interpreta las consultas.
- **SQLAlchemy**: ORM para interactuar con bases de datos SQL de manera eficiente.
- **SQLite / MySQL / PostgreSQL**: Compatible con distintas bases de datos SQL.


## 💻 **Guía de Instalación**

```bash
# 1. Clona el repositorio
git clone https://github.com/TuUsuario/ConsultaInteligenteAPI.git

# 2. Navega al directorio
cd ConsultaInteligenteAPI

# 3. Configura un entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 4. Instala dependencias
pip install -r requirements.txt

# 5. Iniciar el servicio
uvicorn main:app --reload
```
## 🤝 Colaboradores
Este proyecto ha sido desarrollado en colaboración con:

- [JoseAngelHub](https://github.com/JoseAngelHub)

## 📄 **Licencia**

Este proyecto está licenciado bajo la **Licencia GNU GPLv3** - consulta el archivo [LICENSE](LICENSE) para más detalles.

---

### 🌟 ¡Gracias por usar la API de Consulta Inteligente! 🚀🌍

