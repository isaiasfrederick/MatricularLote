#!/usr/bin/env python3
# ==============================================
# CONFIGURAÇÕES PRINCIPAIS – EDITE AQUI
# ==============================================
TOKEN = ""  # <<< TOKEN DA API REST DO MOODLE
MOODLE_URL = "https://ead.uftm.edu.br/webservice/rest/server.php"

COURSE_ID = 1375  # ID do curso no Moodle (mdl_course.id)
ROLE_ID = 5  # ID do papel (role) para estudante (geralmente 5)

campos_cpfs = """
"""

campos_cpfs = campos_cpfs.strip().split("\n")
campos_cpfs = [e for e in campos_cpfs if e != ""]

USER_IDNUMBERS = campos_cpfs  # Lista de idnumbers a serem inscritos
# ==============================================
# CÓDIGO
# ==============================================
import requests


def get_userid_by_idnumber(idnumber: str) -> int | None:
    """
    Busca o userid a partir do idnumber (campo mdl_user.idnumber)
    usando core_user_get_users_by_field.
    """
    params = {
        "wstoken": TOKEN,
        "wsfunction": "core_user_get_users_by_field",
        "moodlewsrestformat": "json",
        "field": "idnumber",
        "values[0]": idnumber,
    }
    resp = requests.get(MOODLE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and data.get("exception"):
        raise RuntimeError(f"Erro na API ao buscar usuário {idnumber}: {data}")

    if not data:
        print(f"[AVISO] Nenhum usuário encontrado com idnumber='{idnumber}'")
        return None

    return data[0].get("id")


def enrol_users(userids: list[int]) -> None:
    """
    Inscreve vários userids no curso definido em COURSE_ID
    com o papel ROLE_ID usando enrol_manual_enrol_users.
    """
    if not userids:
        print("[INFO] Nenhum userid válido para inscrição.")
        return

    params = {
        "wstoken": TOKEN,
        "wsfunction": "enrol_manual_enrol_users",
        "moodlewsrestformat": "json",
    }

    # Monta o payload enrolments[x][userid], [courseid], [roleid]
    data = {}
    for idx, uid in enumerate(userids):
        prefix = f"enrolments[{idx}]"
        data[f"{prefix}[userid]"] = uid
        data[f"{prefix}[courseid]"] = COURSE_ID
        data[f"{prefix}[roleid]"] = ROLE_ID

    resp = requests.post(MOODLE_URL, params=params, data=data, timeout=30)
    resp.raise_for_status()
    result = resp.json() if resp.content else None

    if isinstance(result, dict) and result.get("exception"):
        raise RuntimeError(f"Erro na API ao inscrever usuários: {result}")

    print(
        f"[OK] {len(userids)} usuário(s) enviados para inscrição no curso {COURSE_ID}."
    )


def main():
    # 1) Converte idnumbers -> userids
    userids: list[int] = []
    for idn in USER_IDNUMBERS:
        try:
            uid = get_userid_by_idnumber(idn)
            if uid is not None:
                userids.append(uid)
        except Exception as e:
            print(f"[ERRO] Falha ao buscar userid para '{idn}': {e}")

    print(f"[INFO] Total de userids encontrados: {len(userids)}")

    # 2) Inscreve todos os userids encontrados
    try:
        enrol_users(userids)
    except Exception as e:
        print(f"[ERRO] Falha ao inscrever usuários: {e}")


if __name__ == "__main__":
    main()
