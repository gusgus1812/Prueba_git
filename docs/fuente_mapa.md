# Fuente del mapa de hidrocarburos
Sitio: https://mapa-hidrocarburos.energia.gob.mx/ (CNH/SENER). Al consultarlo (07-11-2026) mostraba aviso de mantenimiento, sin descarga ni API documentada, y desde aquí no pude leer sus capas.

## Cómo obtener coordenadas tú mismo
1. Abre el mapa en tu navegador y la pestaña Red (F12 → Network).
2. Activa las capas de campos y pozos y busca peticiones JSON/GeoJSON o servicios de mapas (suelen terminar en `/query`).
3. Exporta a CSV con columnas `nombre,lat,lon` (campos) y `pozo,lat,lon,campo` (pozos). Respeta los términos de uso del sitio.
4. Guarda en `data/external/coordenadas_campos.csv` y `data/external/pozos.csv`, y ejecuta `python3 scripts/02_build_web.py`. También puedes cargarlos desde la pestaña Mapa sin reconstruir.
Los nombres deben coincidir con los del CSV de reservas (en mayúsculas, sin acentos).

## Nota
`data/external/coordenadas_campos.csv` incluido tiene 7 posiciones aproximadas puestas de memoria (±50 km o más). Sirven solo para probar el mapa; reemplázalas.
