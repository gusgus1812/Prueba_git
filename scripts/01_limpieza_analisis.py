#!/usr/bin/env python3
"""
01_limpieza_analisis.py
Limpia el CSV de reservas de campos (CNH/SENER, 01-01-2024), crea variables
derivadas y exporta: CSV limpio, JSON para el dashboard y un resumen de hallazgos.

Uso:  python3 scripts/01_limpieza_analisis.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw" / "Campos_Reservas_01-01-2024.csv"
OUT = RAIZ / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["nombre", "superficie_km2", "ubicacion", "comentario",
        "pce_1p", "crudo_1p", "gas_1p", "cond_1p", "vo_crudo_1p", "vo_gas_1p",
        "pce_2p", "crudo_2p", "gas_2p", "cond_2p", "vo_crudo_2p", "vo_gas_2p",
        "pce_3p", "crudo_3p", "gas_3p", "cond_3p", "vo_crudo_3p", "vo_gas_3p"]

# ---------------------------------------------------------------- 1. Carga
df = pd.read_csv(RAW, encoding="utf-8-sig")
assert df.shape[1] == len(COLS), "El CSV cambió de estructura"
df.columns = COLS

# ---------------------------------------------------------------- 2. Limpieza
df["nombre"] = df["nombre"].str.strip().str.upper()
df["ubicacion"] = df["ubicacion"].str.strip().str.capitalize()
df["comentario"] = df["comentario"].fillna("").str.strip()

# Superficie: 0 o vacío = sin dato (no es un campo de área cero)
df["sin_superficie"] = df["superficie_km2"].isna() | (df["superficie_km2"] <= 0)
df.loc[df["sin_superficie"], "superficie_km2"] = np.nan

# Tipo de comentario y clúster
def tipo_comentario(c):
    if not c:
        return "Sin comentario"
    if c.startswith("NUEVOS CAMPOS"):
        return "Nuevo campo"
    if "CLUSTER" in c:
        return "Reserva asociada a clúster"
    if "EVALUACI" in c:
        return "Campo en evaluación"
    return "Otro"

def cluster(c):
    m = re.search(r"CLUSTER (.+)$", c)
    return m.group(1) if m else ""

df["tipo_comentario"] = df["comentario"].apply(tipo_comentario)
df["cluster"] = df["comentario"].apply(cluster)

# ---------------------------------------------------------------- 3. Derivadas
# Factor de conversión gas -> crudo equivalente, estimado por mínimos cuadrados
factores = {}
for p in ("1p", "2p", "3p"):
    X = np.c_[df[f"crudo_{p}"] + df[f"cond_{p}"], df[f"gas_{p}"]]
    f = np.linalg.lstsq(X, df[f"pce_{p}"], rcond=None)[0]
    factores[p] = {"liquidos": round(float(f[0]), 3), "gas_mmmpc_a_mmbpce": round(float(f[1]), 3)}

df["probables"] = (df["pce_2p"] - df["pce_1p"]).clip(lower=0).round(2)   # 2P - 1P
df["posibles"] = (df["pce_3p"] - df["pce_2p"]).clip(lower=0).round(2)    # 3P - 2P
df["certeza_1p_3p"] = np.where(df["pce_3p"] > 0, df["pce_1p"] / df["pce_3p"], np.nan).round(4)
df["densidad_2p"] = np.where(df["superficie_km2"] > 0, df["pce_2p"] / df["superficie_km2"], np.nan).round(4)

def fluido(r):
    base = r["pce_2p"] if r["pce_2p"] > 0 else r["pce_3p"]
    p = "2p" if r["pce_2p"] > 0 else "3p"
    if base <= 0:
        return "Sin reserva"
    liq = (r[f"crudo_{p}"] + r[f"cond_{p}"]) / base
    return "Aceite" if liq >= 0.7 else ("Gas" if liq <= 0.3 else "Mixto")

df["fluido_dominante"] = df.apply(fluido, axis=1)

def tamano(v):
    if v <= 0:
        return "Sin reserva 2P"
    if v < 1:
        return "< 1"
    if v < 10:
        return "1 - 10"
    if v < 50:
        return "10 - 50"
    if v < 200:
        return "50 - 200"
    return "> 200"

df["tamano_2p"] = df["pce_2p"].apply(tamano)
df["sin_reserva_2p"] = df["pce_2p"] <= 0
df["sin_reserva_total"] = (df[["pce_1p", "pce_2p", "pce_3p"]].sum(axis=1) <= 0)

df = df.sort_values("pce_2p", ascending=False).reset_index(drop=True)
df.insert(0, "rank_2p", np.arange(1, len(df) + 1))
tot2 = df["pce_2p"].sum()
df["pct_acum_2p"] = (df["pce_2p"].cumsum() / tot2 * 100).round(2)

# ---------------------------------------------------------------- 4. Calidad
calidad = {
    "filas": int(len(df)),
    "columnas_origen": len(COLS),
    "duplicados_nombre": int(df["nombre"].duplicated().sum()),
    "sin_superficie": int(df["sin_superficie"].sum()),
    "sin_superficie_por_ubicacion": df[df.sin_superficie].ubicacion.value_counts().to_dict(),
    "con_comentario": int((df.comentario != "").sum()),
    "sin_reserva_1p": int((df.pce_1p <= 0).sum()),
    "sin_reserva_2p": int((df.pce_2p <= 0).sum()),
    "sin_reserva_3p": int((df.pce_3p <= 0).sum()),
    "sin_reserva_total": int(df.sin_reserva_total.sum()),
    "viola_1p_le_2p": int((df.pce_1p > df.pce_2p + 0.01).sum()),
    "viola_2p_le_3p": int((df.pce_2p > df.pce_3p + 0.01).sum()),
    "factores_conversion": factores,
}

# ---------------------------------------------------------------- 5. Resumen
def suma(g, c):
    return round(float(g[c].sum()), 2)

por_ubic = {}
for u, g in df.groupby("ubicacion"):
    por_ubic[u] = {"campos": int(len(g)), "pce_1p": suma(g, "pce_1p"), "pce_2p": suma(g, "pce_2p"),
                   "pce_3p": suma(g, "pce_3p"), "superficie": suma(g, "superficie_km2")}

top10 = df.head(10)
resumen = {
    "totales": {c: suma(df, c) for c in ["pce_1p", "pce_2p", "pce_3p", "crudo_1p", "crudo_2p", "crudo_3p",
                                         "gas_1p", "gas_2p", "gas_3p", "cond_1p", "cond_2p", "cond_3p"]},
    "por_ubicacion": por_ubic,
    "top10_participacion_2p": round(float(top10["pce_2p"].sum() / tot2 * 100), 1),
    "campos_para_80pct_2p": int((df["pct_acum_2p"] < 80).sum() + 1),
    "mediana_pce_2p": round(float(df["pce_2p"].median()), 3),
    "media_pce_2p": round(float(df["pce_2p"].mean()), 2),
    "por_fluido": df.groupby("fluido_dominante")["pce_2p"].agg(["count", "sum"]).round(2).to_dict("index"),
    "por_comentario": df.groupby("tipo_comentario")[["pce_1p", "pce_2p", "pce_3p"]].sum().round(2).assign(
        campos=df.groupby("tipo_comentario").size()).to_dict("index"),
    "calidad": calidad,
}

# ---------------------------------------------------------------- 6. Exportar
df.to_csv(OUT / "campos_limpio.csv", index=False, encoding="utf-8-sig")
registros = json.loads(df.replace({np.nan: None}).to_json(orient="records", force_ascii=False))
(OUT / "campos_limpio.json").write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")
(OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

print("OK ->", OUT)
print(json.dumps({k: resumen[k] for k in ("totales", "por_ubicacion", "top10_participacion_2p",
                                          "campos_para_80pct_2p", "por_fluido", "por_comentario")},
                 ensure_ascii=False, indent=1))
print(json.dumps(calidad, ensure_ascii=False, indent=1))
