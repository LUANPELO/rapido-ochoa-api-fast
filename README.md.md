# 📦 API de Rastreo Rápido Ochoa

API REST ultra rápida para consultar guías de Rápido Ochoa sin usar Selenium. Tiempo de respuesta: **1-3 segundos** ⚡

## 🚀 Características

- ✅ Sin Selenium (HTTP directo)
- ⚡ Respuestas en 1-3 segundos
- 📊 Información completa de la guía
- 🔄 Trazabilidad detallada
- 📝 Documentación interactiva (Swagger)

## 📋 Requisitos

- Python 3.11.0 (requerido)
- pip

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/rapido-ochoa-api.git
cd rapido-ochoa-api
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Iniciar el servidor

```bash
python main.py
```

O con uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://127.0.0.1:8000`

### Endpoints

#### 1. Consultar guía (GET)

```bash
GET http://127.0.0.1:8000/api/rastreo/E121101188
```

#### 2. Consultar guía (POST)

```bash
POST http://127.0.0.1:8000/api/rastreo
Content-Type: application/json

{
  "numero_guia": "E121101188"
}
```

#### 3. Documentación interactiva

```
http://127.0.0.1:8000/docs
```

#### 4. Health Check

```bash
GET http://127.0.0.1:8000/api/health
```

## 📄 Respuesta JSON

```json
{
  "numero_guia": "E121101188",
  "documento_anexo": "Numero",
  "fecha_admision": "2025/10/03 13:07",
  "origen": "MEDELLIN (ANTIOQUIA)",
  "destino": "BARRANQUILLA (ATLANTICO)",
  "remitente_nombre": "CRISTIAN GIL",
  "destinatario_nombre": "EDGARDO HERNANDEZ TAMAYO",
  "productos": [
    {
      "empaque": "Paquetes",
      "dice_contener": "009980 - MENSAJERIA DE 1-5 KG X UND",
      "unidades": "1",
      "peso_cobrar": "5"
    }
  ],
  "total_unidades": "1",
  "trazabilidad": [
    {
      "fecha": "2025/10/03 13:07",
      "detalle": "GUIA ELABORADA",
      "sede": "TERMINAL NORTE PASAJES(...)",
      "estado": "GUIA ELABORADA"
    }
  ],
  "estado_actual": "LISTA PARA FACTURAR",
  "fecha_consulta": "2025-10-17T23:45:57.955902"
}
```

## 🔧 Configuración

Para desactivar el modo debug (recomendado en producción):

En `main.py`, línea 78:
```python
self.debug_mode = False
```

## 📝 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **Requests** - Cliente HTTP
- **BeautifulSoup4** - Parser HTML
- **Uvicorn** - Servidor ASGI

## 📄 Licencia

MIT License

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 👤 Autor

Tu Nombre - [@tu_usuario](https://github.com/tu_usuario)

## 📞 Soporte

Si tienes algún problema o pregunta, abre un [issue](https://github.com/TU_USUARIO/rapido-ochoa-api/issues).