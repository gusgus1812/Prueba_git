# Reservas de hidrocarburos de México · 477 campos (corte 01-01-2024)

Análisis y dashboard interactivo de las reservas 1P, 2P y 3P por campo (CNH/SENER).

## Estructura
```
data/raw/        CSV original, sin modificar
data/processed/  CSV/JSON limpios + resumen.json (generados por script)
data/external/   coordenadas_campos.csv (referencial) y, si los consigues, pozos.csv
scripts/         01_limpieza_analisis.py · 02_build_web.py
web/             template.html (fuente) e index.html (generado, un solo archivo)
docs/            glosario, hallazgos, fuente del mapa, plan de commits
```

## Uso
```bash
pip install -r requirements.txt
python3 scripts/01_limpieza_analisis.py   # limpia y calcula
python3 scripts/02_build_web.py           # genera web/index.html
# abre web/index.html en el navegador
```

## Qué incluye el dashboard
Pastel y dona, barras (simples, agrupadas, apiladas), histograma, dispersión log-log, Pareto, tabla ordenable con descarga CSV/JSON, mapa (Leaflet), glosario y calidad de datos. Todo reacciona a los filtros (1P/2P/3P, ubicación, búsqueda, clic en gráficas) y se maneja con teclado (ver pestaña Ayuda: `P`, `U`, `/`, `Esc`, `1`-`7`, flechas, Enter).

## Limitaciones
- El CSV no trae coordenadas ni pozos. El mapa usa 7 ubicaciones **referenciales**; carga tu CSV `nombre,lat,lon` desde la pestaña Mapa o ponlo en `data/external/` y vuelve a ejecutar el paso 2. Ver `docs/fuente_mapa.md`.
- El mapa base necesita internet (OpenStreetMap vía Leaflet en cdnjs).
