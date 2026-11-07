#!/usr/bin/env python3
"""
02_build_web.py
Inserta los datos limpios en web/template.html y genera web/index.html
(un solo archivo, funciona abriéndolo con doble clic).

Opcionales (si existen se incrustan en el mapa):
  data/external/coordenadas_campos.csv   columnas: nombre,lat,lon[,nota]
  data/external/pozos.csv                columnas: pozo,lat,lon[,campo]

Uso:  python3 scripts/02_build_web.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ / "data" / "processed"
EXT = RAIZ / "data" / "external"
WEB = RAIZ / "web"


def leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in fila.items()} for fila in csv.DictReader(f)]


datos = (PROC / "campos_limpio.json").read_text(encoding="utf-8")
resumen = (PROC / "resumen.json").read_text(encoding="utf-8")
coords = leer_csv(EXT / "coordenadas_campos.csv")
pozos = leer_csv(EXT / "pozos.csv")

html = (WEB / "template.html").read_text(encoding="utf-8")
# evita que "</script>" dentro de los datos rompa la página
seguro = lambda s: s.replace("</", "<\\/")
html = html.replace("/*__DATA__*/[]", seguro(datos))
html = html.replace("/*__RESUMEN__*/{}", seguro(resumen))
html = html.replace("/*__COORDS__*/[]", seguro(json.dumps(coords, ensure_ascii=False)))
html = html.replace("/*__POZOS__*/[]", seguro(json.dumps(pozos, ensure_ascii=False)))

(WEB / "index.html").write_text(html, encoding="utf-8")
print(f"OK -> web/index.html  ({len(html)/1024:.0f} KB) · campos con coordenadas: {len(coords)} · pozos: {len(pozos)}")
