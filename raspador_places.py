#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspador Google Places (Places API New) — versão linha de comando.

Pesquisa negócios no Google Maps e exporta para CSV e/ou JSON,
prontos para importar no seu app de prospecção.

Usa o endpoint ATUALIZADO da Places API (New):
    POST https://places.googleapis.com/v1/places:searchText

Exemplos:
    python raspador_places.py "salão de beleza na Penha, Rio de Janeiro"
    python raspador_places.py "barbearia em Niterói" --pages 3 --formato ambos
    python raspador_places.py "restaurante em SP" --formato json --saida leads

A chave da API pode vir de:
    1) variável de ambiente GOOGLE_PLACES_API_KEY   (recomendado)
    2) argumento --chave SUA_CHAVE
    3) editando a constante CHAVE_API abaixo
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from urllib import request, error

# ──────────────────────────────────────────────────────────────────
# 👉 COLE SUA CHAVE AQUI (opcional). O ideal é usar a variável de
#    ambiente GOOGLE_PLACES_API_KEY ou o argumento --chave.
CHAVE_API = ""
# ──────────────────────────────────────────────────────────────────

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

# Field Mask é OBRIGATÓRIO na API nova: define quais campos voltam.
# addressComponents traz o endereço estruturado (bairro, cidade) separado.
FIELD_MASK = ",".join([
    "places.displayName",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.primaryTypeDisplayName",
    "places.primaryType",
    "places.addressComponents",
    "places.formattedAddress",
    "nextPageToken",
])

REGIOES = {
    "br": {"regionCode": "BR", "languageCode": "pt-BR"},
    "pt": {"regionCode": "PT", "languageCode": "pt-PT"},
    "us": {"regionCode": "US", "languageCode": "en-US"},
}

COLUNAS = ["name", "phone", "category", "city", "county", "website"]


def obter_chave(arg_chave: str | None) -> str:
    chave = (arg_chave or os.environ.get("GOOGLE_PLACES_API_KEY") or CHAVE_API or "").strip()
    if not chave:
        sys.exit(
            "❌ Nenhuma chave encontrada.\n"
            "   Defina a variável GOOGLE_PLACES_API_KEY, use --chave, "
            "ou edite CHAVE_API no topo do arquivo."
        )
    return chave


def buscar(query: str, chave: str, paginas: int, regiao: str) -> list[dict]:
    reg = REGIOES.get(regiao, REGIOES["br"])
    coletados: list[dict] = []
    page_token = None

    for pagina in range(paginas):
        corpo = {
            "textQuery": query,
            "pageSize": 20,
            "languageCode": reg["languageCode"],
            "regionCode": reg["regionCode"],
        }
        if page_token:
            corpo["pageToken"] = page_token

        req = request.Request(
            ENDPOINT,
            data=json.dumps(corpo).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": chave,
                "X-Goog-FieldMask": FIELD_MASK,
            },
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            detalhe = e.read().decode("utf-8", "ignore")
            try:
                msg = json.loads(detalhe)["error"]["message"]
            except Exception:
                msg = detalhe or str(e)
            sys.exit(f"❌ Erro da API ({e.code}): {msg}")
        except error.URLError as e:
            sys.exit(f"❌ Falha de conexão com o Google: {e.reason}")

        lugares = dados.get("places", [])
        coletados.extend(lugares)
        print(f"   página {pagina + 1}: +{len(lugares)} (total {len(coletados)})")

        page_token = dados.get("nextPageToken")
        if not page_token:
            break
        if pagina < paginas - 1:
            time.sleep(1.8)  # o token novo leva um instante para ficar válido

    return coletados


def pegar_componente(componentes: list, tipos: list[str]) -> str:
    """Retorna o primeiro componente de endereço que casa com a prioridade de tipos."""
    if not componentes:
        return ""
    for t in tipos:
        for c in componentes:
            if t in (c.get("types") or []):
                return c.get("longText") or c.get("shortText") or ""
    return ""


def normalizar(p: dict) -> dict:
    comps = p.get("addressComponents") or []
    # county = só o bairro (não o endereço completo)
    bairro = pegar_componente(comps, ["sublocality_level_1", "sublocality", "neighborhood", "administrative_area_level_4"])
    cidade = pegar_componente(comps, ["locality", "administrative_area_level_2", "postal_town"])
    return {
        "name": (p.get("displayName") or {}).get("text", ""),
        "phone": p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber") or "",
        "category": (p.get("primaryTypeDisplayName") or {}).get("text") or p.get("primaryType", ""),
        "city": cidade,
        "county": bairro,
        "website": p.get("websiteUri", ""),
    }


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return (t[:50] or "resultados")


def salvar_csv(linhas: list[dict], caminho: str) -> None:
    # utf-8-sig grava o BOM para os acentos abrirem certos no Excel.
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)
    print(f"💾 CSV salvo: {caminho}")


def salvar_json(linhas: list[dict], caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON salvo: {caminho}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Raspa dados do Google Maps (Places API New) e exporta CSV/JSON."
    )
    parser.add_argument("query", help='O que pesquisar. Ex.: "salão de beleza na Penha"')
    parser.add_argument("--paginas", "--pages", type=int, default=3, dest="paginas",
                        help="Quantas páginas buscar (20 por página). Padrão: 3")
    parser.add_argument("--formato", choices=["csv", "json", "ambos"], default="ambos",
                        help="Formato de exportação. Padrão: ambos")
    parser.add_argument("--regiao", choices=["br", "pt", "us"], default="br",
                        help="Região/idioma. Padrão: br")
    parser.add_argument("--saida", default=None,
                        help="Nome base dos arquivos (sem extensão).")
    parser.add_argument("--chave", default=None, help="Chave da API (sobrepõe a variável de ambiente).")
    args = parser.parse_args()

    chave = obter_chave(args.chave)
    paginas = max(1, min(args.paginas, 3))  # a API entrega no máx. ~60 resultados (3 páginas)

    print(f"🔎 Pesquisando: {args.query!r}")
    brutos = buscar(args.query, chave, paginas, args.regiao)
    linhas = [normalizar(p) for p in brutos]

    if not linhas:
        print("🤷 Nenhum resultado encontrado.")
        return

    base = args.saida or slug(args.query)
    if args.formato in ("csv", "ambos"):
        salvar_csv(linhas, f"{base}.csv")
    if args.formato in ("json", "ambos"):
        salvar_json(linhas, f"{base}.json")

    print(f"✅ Concluído: {len(linhas)} negócio(s).")


if __name__ == "__main__":
    main()
