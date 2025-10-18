"""
API REST para rastreo de encomiendas de Rápido Ochoa
VERSIÓN DEFINITIVA - HTTP Directo al servidor
Tiempo de respuesta: 1-3 segundos ⚡
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import re
from datetime import datetime
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rápido Ochoa Rastreo API",
    description="API ultra rápida usando HTTP directo",
    version="6.0.0 FINAL"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos actualizados según estructura requerida
class Producto(BaseModel):
    empaque: str
    dice_contener: str
    unidades: str
    peso_cobrar: str

class EventoTrazabilidad(BaseModel):
    fecha: str
    detalle: str
    sede: str
    estado: str

class DatosEncomienda(BaseModel):
    numero_guia: str
    documento_anexo: Optional[str] = "Numero"
    fecha_admision: Optional[str] = None
    origen: Optional[str] = None
    destino: Optional[str] = None
    remitente_nombre: Optional[str] = None
    destinatario_nombre: Optional[str] = None
    productos: List[Producto] = []
    total_unidades: Optional[str] = None
    trazabilidad: List[EventoTrazabilidad] = []
    estado_actual: Optional[str] = None
    fecha_consulta: str

class ConsultaRequest(BaseModel):
    numero_guia: str

class RapidoOchoaAPI:
    
    def __init__(self):
        self.base_url = "https://rapidoochoa.tmsolutions.com.co/tmland/faces/public/tmland-carga/cotizador_envios.xhtml?parametroInicial=cmFwaWRvb2Nob2E="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        })
        self.view_state = None
        self.debug_mode = True
    
    def _obtener_view_state(self):
        """Obtiene el ViewState inicial de la página"""
        try:
            logger.info("📡 Obteniendo ViewState inicial...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            response = self.session.get(
                self.base_url,
                headers=headers,
                timeout=20,
                verify=True
            )
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Error HTTP {response.status_code}")
                raise HTTPException(status_code=502, detail=f"Error al conectar: HTTP {response.status_code}")
            
            logger.info(f"✅ Página cargada ({len(response.text)} bytes)")
            
            match = re.search(r'name="javax\.faces\.ViewState"[^>]+value="([^"]+)"', response.text)
            if match:
                self.view_state = match.group(1)
                logger.info(f"✅ ViewState obtenido: {self.view_state[:30]}...")
                return True
            
            logger.error("❌ No se encontró ViewState en el HTML")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error: {type(e).__name__}: {e}")
            return False
    
    def consultar_guia(self, numero_guia: str) -> DatosEncomienda:
        """Consulta directa usando HTTP"""
        
        try:
            if not self.view_state:
                if not self._obtener_view_state():
                    raise HTTPException(status_code=500, detail="No se pudo inicializar sesión")
            
            logger.info(f"🔍 Consultando guía: {numero_guia}")
            
            form_data = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'tabpane:form_entrega:codigoguia',
                'javax.faces.partial.execute': 'tabpane:form_entrega:codigoguia',
                'javax.faces.partial.render': 'tabpane:form_entrega',
                'javax.faces.behavior.event': 'keyup',
                'javax.faces.partial.event': 'keyup',
                'tabpane:form_entrega:codigoguia': numero_guia,
                'javax.faces.ViewState': self.view_state,
                'tabpane:form_entrega': 'tabpane:form_entrega',
            }
            
            headers = {
                'Faces-Request': 'partial/ajax',
                'Referer': self.base_url,
            }
            
            logger.info("📡 Enviando petición...")
            response = self.session.post(
                self.base_url,
                data=form_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Error del servidor: {response.status_code}")
            
            logger.info(f"✅ Respuesta recibida ({len(response.text)} bytes)")
            
            return self._parsear_respuesta(response.text, numero_guia)
            
        except HTTPException:
            raise
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Timeout")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _parsear_respuesta(self, xml_response: str, numero_guia: str) -> DatosEncomienda:
        """Parsea la respuesta XML del servidor"""
        
        # Crear objeto con fecha_consulta
        datos = DatosEncomienda(
            numero_guia=numero_guia,
            fecha_consulta=datetime.now().isoformat()
        )
        
        try:
            logger.info("🔍 Parseando XML...")
            
            cdata_content = ""
            cdata_matches = re.findall(r'<!\[CDATA\[(.*?)\]\]>', xml_response, re.DOTALL)
            if cdata_matches:
                cdata_content = ' '.join(cdata_matches)
                logger.info(f"✅ CDATA extraído ({len(cdata_content)} bytes)")
                
                if self.debug_mode:
                    with open('debug_response.html', 'w', encoding='utf-8') as f:
                        f.write(cdata_content)
                    logger.info("🐛 HTML guardado en debug_response.html")
            
            if not cdata_content:
                raise HTTPException(status_code=404, detail=f"No se encontró información para la guía {numero_guia}")
            
            soup = BeautifulSoup(cdata_content, 'html.parser')
            all_labels = soup.find_all('label')
            
            # Extraer Número de guía
            for label in all_labels:
                text = label.get_text(strip=True)
                if re.match(r'^E\d+', text):
                    datos.numero_guia = text
                    logger.info(f"✅ Número: {datos.numero_guia}")
                    break
            
            # Extraer Fecha de admisión
            for i, label in enumerate(all_labels):
                text = label.get_text(strip=True)
                if re.search(r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}', text):
                    if not datos.fecha_admision:
                        datos.fecha_admision = text
                        logger.info(f"✅ Fecha admisión: {datos.fecha_admision}")
                        break
            
            # Extraer Origen y Destino desde "Origen - Destino"
            for label in all_labels:
                text = label.get_text(strip=True)
                if ' - ' in text and '(' in text and ')' in text:
                    partes = text.split(' - ')
                    if len(partes) == 2:
                        datos.origen = partes[0].strip()
                        datos.destino = partes[1].strip()
                        logger.info(f"✅ Origen: {datos.origen}")
                        logger.info(f"✅ Destino: {datos.destino}")
                    break
            
            # Extraer Remitente y Destinatario
            panels = soup.find_all('div', class_='ui-panel-content')
            for panel in panels:
                h5 = panel.find('h5')
                if h5:
                    titulo = h5.get_text(strip=True).lower()
                    
                    if 'remitente' in titulo:
                        nombre_label = panel.find('label', string=re.compile(r'Nombre:', re.I))
                        if nombre_label:
                            match = re.search(r'Nombre:\s*(.+)', nombre_label.get_text())
                            if match:
                                datos.remitente_nombre = match.group(1).strip()
                                logger.info(f"✅ Remitente: {datos.remitente_nombre}")
                    
                    elif 'destinatario' in titulo:
                        nombre_label = panel.find('label', string=re.compile(r'Nombre:', re.I))
                        if nombre_label:
                            match = re.search(r'Nombre:\s*(.+)', nombre_label.get_text())
                            if match:
                                datos.destinatario_nombre = match.group(1).strip()
                                logger.info(f"✅ Destinatario: {datos.destinatario_nombre}")
            
            # Extraer Productos y Total Unidades - identificar tabla correcta
            all_tables = soup.find_all('table')
            productos_procesados = False
            
            for table in all_tables:
                rows = table.find_all('tr')
                
                if len(rows) > 0:
                    # Identificar headers
                    header_cells = rows[0].find_all(['th', 'td'])
                    headers = [cell.get_text(strip=True).lower() for cell in header_cells]
                    logger.info(f"🐛 Tabla encontrada con headers: {headers}")
                    
                    # Verificar si es la tabla de PRODUCTOS (tiene "empaque" o "dice contener")
                    es_tabla_productos = any(h in ['empaque', 'dice contener', 'unidades', 'peso cobrar'] for h in headers)
                    
                    # Verificar si es tabla de TRAZABILIDAD (tiene "fecha" y "detalle")
                    es_tabla_trazabilidad = 'fecha' in headers and 'detalle' in headers
                    
                    if es_tabla_productos and not es_tabla_trazabilidad and not productos_procesados:
                        logger.info("✅ Tabla de PRODUCTOS identificada")
                        
                        # Mapear índices de columnas
                        col_map = {}
                        for idx, header in enumerate(headers):
                            if 'empaque' in header:
                                col_map['empaque'] = idx
                            elif 'contener' in header or 'dice' in header:
                                col_map['dice_contener'] = idx
                            elif header == 'unidades':
                                col_map['unidades'] = idx
                            elif 'peso' in header and 'cobrar' in header:
                                col_map['peso_cobrar'] = idx
                        
                        # Procesar filas de productos
                        for row in rows[1:]:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                first_cell = cells[0].get_text(strip=True)
                                
                                # Fila TOTAL - buscar el primer número después de "Total"
                                if first_cell.lower() == 'total':
                                    cell_values = [c.get_text(strip=True) for c in cells]
                                    logger.info(f"🐛 Fila Total encontrada: {cell_values}")
                                    
                                    # Buscar el primer número que sea pequeño (< 100)
                                    for i, val in enumerate(cell_values[1:], 1):  # Empezar desde índice 1
                                        if val.isdigit():
                                            num = int(val)
                                            if num < 100:  # Asumimos que unidades < 100
                                                datos.total_unidades = val
                                                logger.info(f"✅ Total unidades: {datos.total_unidades}")
                                                break
                                
                                # Fila de producto (no es "Total")
                                elif first_cell and first_cell.lower() != 'total':
                                    try:
                                        producto = Producto(
                                            empaque=cells[col_map.get('empaque', 0)].get_text(strip=True),
                                            dice_contener=cells[col_map.get('dice_contener', 1)].get_text(strip=True),
                                            unidades=cells[col_map.get('unidades', 2)].get_text(strip=True),
                                            peso_cobrar=cells[col_map.get('peso_cobrar', 3)].get_text(strip=True) if len(cells) > 3 else ""
                                        )
                                        datos.productos.append(producto)
                                        logger.info(f"✅ Producto agregado: {producto.empaque}")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Error procesando producto: {e}")
                        
                        productos_procesados = True
            
            # Extraer Trazabilidad - buscar en TODAS las tablas
            trazabilidad_encontrada = False
            
            for table in all_tables:
                if trazabilidad_encontrada:
                    break
                    
                rows = table.find_all('tr')
                
                if len(rows) > 1:
                    # Verificar si es tabla de trazabilidad por el contenido
                    # La primera fila de datos debería tener una fecha en formato YYYY/MM/DD
                    primera_fila_data = rows[1] if len(rows) > 1 else None
                    
                    if primera_fila_data:
                        cells = primera_fila_data.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            # Obtener texto de primera celda
                            primera_celda = cells[0].find('label')
                            if primera_celda:
                                primer_texto = primera_celda.get_text(strip=True)
                            else:
                                primer_texto = cells[0].get_text(strip=True)
                            
                            # Si la primera celda tiene formato de fecha, es tabla de trazabilidad
                            if re.search(r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}', primer_texto):
                                logger.info(f"✅ Tabla de TRAZABILIDAD identificada por contenido")
                                logger.info(f"🐛 Total de filas a procesar: {len(rows) - 1}")
                                
                                # Procesar TODAS las filas de datos (saltar header)
                                for idx, row in enumerate(rows[1:], 1):
                                    cells = row.find_all(['td', 'th'])
                                    
                                    if len(cells) >= 3:
                                        # Extraer fecha (columna 0)
                                        label = cells[0].find('label')
                                        fecha_text = label.get_text(strip=True) if label else cells[0].get_text(strip=True)
                                        
                                        # Extraer detalle (columna 1)
                                        label = cells[1].find('label')
                                        detalle_text = label.get_text(strip=True) if label else cells[1].get_text(strip=True)
                                        
                                        # Extraer sede (columna 2)
                                        label = cells[2].find('label')
                                        sede_text = label.get_text(strip=True) if label else cells[2].get_text(strip=True)
                                        
                                        logger.info(f"🐛 Fila {idx}: Fecha='{fecha_text}', Detalle='{detalle_text}'")
                                        
                                        # Validar que tenga formato de fecha correcto
                                        if re.search(r'\d{4}/\d{2}/\d{2}', fecha_text) and detalle_text:
                                            evento = EventoTrazabilidad(
                                                fecha=fecha_text,
                                                detalle=detalle_text,
                                                sede=sede_text,
                                                estado=detalle_text
                                            )
                                            datos.trazabilidad.append(evento)
                                            logger.info(f"✅ Evento {idx} agregado: {detalle_text}")
                                        else:
                                            logger.warning(f"⚠️ Fila {idx} descartada: formato inválido")
                                
                                trazabilidad_encontrada = True
                                
                                # El estado actual es el último evento
                                if datos.trazabilidad:
                                    datos.estado_actual = datos.trazabilidad[-1].estado
                                    logger.info(f"✅ Estado actual: {datos.estado_actual}")
                                
                                logger.info(f"✅ Trazabilidad: {len(datos.trazabilidad)} eventos capturados")
            
            if not trazabilidad_encontrada:
                logger.warning("⚠️ No se encontró tabla de trazabilidad")
            
            # Validar datos mínimos
            if not datos.fecha_admision and not datos.origen:
                logger.warning("⚠️ Datos incompletos. Revisa debug_response.html")
            
            logger.info("✅ Datos extraídos exitosamente")
            return datos
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error parseando: {e}")
            raise HTTPException(status_code=500, detail="Error al procesar respuesta")

# Instancia global
api = RapidoOchoaAPI()

# Endpoints
@app.get("/")
def root():
    return {
        "servicio": "Rápido Ochoa Rastreo API",
        "version": "6.0.0 FINAL",
        "descripcion": "API ultra rápida sin Selenium",
        "tiempo_respuesta": "1-3 segundos ⚡",
        "endpoints": {
            "docs": "/docs",
            "rastreo": "/api/rastreo/{numero_guia}",
            "health": "/api/health"
        }
    }

@app.get("/api/rastreo/{numero_guia}", response_model=DatosEncomienda)
def consultar_guia_get(numero_guia: str):
    """
    Consulta una guía de Rápido Ochoa
    
    Ejemplo: GET /api/rastreo/E121101188
    
    Respuesta en 1-3 segundos ⚡
    """
    logger.info(f"📦 Consulta GET: {numero_guia}")
    return api.consultar_guia(numero_guia)

@app.post("/api/rastreo", response_model=DatosEncomienda)
def consultar_guia_post(consulta: ConsultaRequest):
    """
    Consulta una guía de Rápido Ochoa
    
    Body: {"numero_guia": "E121101188"}
    """
    logger.info(f"📦 Consulta POST: {consulta.numero_guia}")
    return api.consultar_guia(consulta.numero_guia)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "6.0.0",
        "motor": "HTTP Directo (Sin Selenium)",
        "velocidad": "1-3 segundos"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Usar PORT de Render o 8000 en local
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)