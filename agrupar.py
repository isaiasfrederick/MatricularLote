#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import requests
import time
import sys

if len(sys.argv) != 3:
    print("Uso: python agrupar.py <TOKEN_DO_WEBSERVICE> <CAMINHO_DO_CSV>")
    sys.exit(1)


# ====== CONFIGURAÇÕES ======
MOODLE_BASE = "https://ead.uftm.edu.br"

TOKEN = sys.argv[1]  # token do webservice
CSV_PATH = sys.argv[2]  # caminho do CSV

TIME_BETWEEN_CALLS = 0.2  # segundos entre chamadas para evitar throttle
DRY_RUN = False  # True: não chama a API, só imprime o que faria
# ===========================

WS_URL = f"{MOODLE_BASE}/webservice/rest/server.php"
WS_FUNCTION = "core_group_add_group_members"
FORMAT = "json"


def add_user_to_group(session, userid: int, groupid: int) -> dict:
    """
    Chama core_group_add_group_members para 1 par (userid, groupid).
    Retorna dict com resultado ou erro da API.
    """
    params = {
        "wstoken": TOKEN,
        "moodlewsrestformat": FORMAT,
        "wsfunction": WS_FUNCTION,
    }
    # Estrutura esperada: members[0][groupid], members[0][userid]
    data = {
        "members[0][groupid]": int(groupid),
        "members[0][userid]": int(userid),
    }

    if DRY_RUN:
        print(f"[DRY_RUN] Adicionaria userid={userid} ao groupid={groupid}")
        return {"dry_run": True, "userid": userid, "groupid": groupid}

    resp = session.post(WS_URL, params=params, data=data, timeout=30)
    resp.raise_for_status()
    out = resp.json()

    # A API retorna {} em sucesso; erros vêm como {"exception": "...", "message": "..."}
    if isinstance(out, dict) and out.get("exception"):
        return {"ok": False, "userid": userid, "groupid": groupid, "error": out}
    return {"ok": True, "userid": userid, "groupid": groupid, "response": out}


def main():
    df = pd.read_csv(
        CSV_PATH, dtype={"userid": "Int64", "courseid": "Int64", "polo_id": "Int64"}
    )
    required_cols = {"userid", "courseid", "polo_id"}
    missing = required_cols - set(df.columns.str.lower())
    if missing:
        raise ValueError(
            f"CSV precisa conter as colunas: {required_cols}. Faltando: {missing}"
        )

    # Normaliza nomes (caso as colunas venham com capitalização diferente)
    df.columns = [c.lower() for c in df.columns]

    results = []
    with requests.Session() as s:
        for idx, row in df.iterrows():
            userid = int(row["userid"])
            groupid = int(row["polo_id"])  # id do group
            # courseid está disponível (row["courseid"]), mas a chamada não exige; pode ser útil p/ logs
            r = add_user_to_group(s, userid=userid, groupid=groupid)
            results.append({**r, "courseid": int(row["courseid"])})
            print(
                f"[{idx+1}/{len(df)}] userid={userid} -> groupid={groupid} :: {('OK' if r.get('ok', True) else 'ERRO')}"
            )
            time.sleep(TIME_BETWEEN_CALLS)

    # Relatório simples
    ok = sum(1 for r in results if r.get("ok", True))
    fail = len(results) - ok
    print(f"\nConcluído. Sucessos: {ok} | Falhas: {fail}")
    if fail:
        print("Falhas detalhadas:")
        for r in results:
            if not r.get("ok", True):
                print(
                    f"- userid={r['userid']} groupid={r['groupid']} courseid={r['courseid']} erro={r.get('error')}"
                )


if __name__ == "__main__":
    main()
