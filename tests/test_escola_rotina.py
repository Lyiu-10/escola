from escola import rotina


def b(inicio, fim, tipo, titulo, **mais):
    return {"inicio": inicio, "fim": fim, "tipo": tipo, "titulo": titulo, **mais}


SEMANA_UTIL = {"nome": "Segunda a sexta", "dias": [0, 1, 2, 3, 4], "blocos": [
    b("10:45", "13:00", "casa", "Acordar e almoço"),
    b("13:00", "19:30", "trabalho", "Trabalho"),
    b("19:30", "21:00", "casa", "Banho e janta"),
    b("21:00", "22:30", "estudo", "Estudo", nota="40 min, pausa, 40 min"),
    b("22:30", "1:00", "livre", "Livre, sem culpa", nota="Jogo, amigos."),
    b("1:00", "10:45", "sono", "Dormir")]}
SABADO = {"nome": "Sábado", "dias": [5], "blocos": [
    b("10:45", "12:20", "casa", "Almoço"),
    b("12:20", "23:00", "fora", "Compromisso"),
    b("23:00", "1:00", "livre", "Livre, sem culpa"),
    b("1:00", "10:45", "sono", "Dormir")]}
DOMINGO = {"nome": "Domingo", "dias": [6], "blocos": [
    b("10:45", "14:00", "livre", "Livre", nota="O almoço entra aqui."),
    b("14:00", "16:00", "estudo", "Estudo: o simulado"),
    b("16:00", "18:00", "livre", "Livre"),
    b("18:00", "22:00", "fora", "Culto"),
    b("22:00", "1:00", "livre", "Livre, sem culpa"),
    b("1:00", "10:45", "sono", "Dormir")]}
ROTINA = {"resumo": "A semana.", "regras": [], "grades": [SEMANA_UTIL, SABADO, DOMINGO]}


def blocos(r, dia):
    g = next(g for g in r["grades"] if dia in g["dias"])
    return [(x["inicio"], x["fim"], x["tipo"]) for x in g["blocos"]]


def cobre_o_dia(r):
    for g in r["grades"]:
        bs = g["blocos"]
        assert all(a["fim"] == p["inicio"] for a, p in zip(bs, bs[1:])) and bs[-1]["fim"] == bs[0]["inicio"], g["nome"]


def test_o_estudo_do_cronograma_no_lugar_da_rotina_deixa_o_dia_igual():
    r = rotina.montar(ROTINA, {d: ("", 90) for d in range(5)})
    assert blocos(r, 0) == [("10:45", "13:00", "casa"), ("13:00", "19:30", "trabalho"), ("19:30", "21:00", "casa"),
                            ("21:00", "22:30", "estudo"), ("22:30", "01:00", "livre"), ("01:00", "10:45", "sono")]
    assert r["grades"][0]["nome"] == "Segunda a sexta" and r["avisos"] == []
    estudo = next(x for x in r["grades"][0]["blocos"] if x["tipo"] == "estudo")
    assert estudo["rota"] == "#/" and "pausa" not in estudo["nota"]  # o texto do estudo é do Cronograma, sem Pomodoro
    assert r["estudo"][0] == {"dia": 0, "inicio": "21:00", "fim": "22:30", "minutos": 90, "marcada": False}
    cobre_o_dia(r)


def test_mais_tempo_encolhe_o_livre_e_o_dia_sem_estudo_devolve_o_lugar():
    r = rotina.montar(ROTINA, {0: ("", 150), 1: ("", 90)})
    assert ("21:00", "23:30", "estudo") in blocos(r, 0) and ("23:30", "01:00", "livre") in blocos(r, 0)
    assert ("21:00", "01:00", "livre") in blocos(r, 2)  # quarta é folga: o lugar do estudo volta a ser livre
    assert ("10:45", "14:00", "livre") in blocos(r, 6) and ("14:00", "18:00", "livre") in blocos(r, 6)
    assert [g["nome"] for g in r["grades"]] == ["Segunda", "Terça", "Quarta a sexta", "Sábado", "Domingo"]
    cobre_o_dia(r)


def test_hora_marcada_no_cronograma_manda():
    r = rotina.montar(ROTINA, {0: ("23:00", 60), 6: ("11:00", 120)})
    assert blocos(r, 0)[3:7] == [("21:00", "23:00", "livre"), ("23:00", "00:00", "estudo"), ("00:00", "01:00", "livre"),
                                 ("01:00", "10:45", "sono")]
    assert ("11:00", "13:00", "estudo") in blocos(r, 6)
    assert {e["dia"]: e["marcada"] for e in r["estudo"]} == {0: True, 6: True}
    cobre_o_dia(r)


def test_estudo_que_bate_num_compromisso_fica_de_fora_e_vira_aviso_com_propostas():
    semana = {d: ("", 150) for d in range(6)}  # o Cronograma dele em 26/10: segunda a sábado, 2h30, sem hora
    r = rotina.montar(ROTINA, semana)
    assert all(t != "estudo" for *_, t in blocos(r, 5))
    [aviso] = r["avisos"]
    assert aviso["dia"] == 5 and aviso["tipo"] == "conflito" and "2h30" in aviso["texto"]
    rotulos = [p["rotulo"] for p in aviso["propostas"]]
    assert rotulos == ["Passar para domingo, das 14h às 16h30", "Folga no sábado"]
    assert [x["dia"] for x in aviso["propostas"][0]["semana"]] == [0, 1, 2, 3, 4, 6]


def test_hora_que_bate_no_trabalho_propoe_outra_hora_no_mesmo_dia():
    r = rotina.montar(ROTINA, {1: ("14:00", 60), 2: ("", 90)})
    [aviso] = r["avisos"]
    assert aviso["texto"] == "Terça: o estudo das 14h às 15h (1h) bate com “Trabalho”, das 13h às 19h30."
    primeira = aviso["propostas"][0]
    assert primeira["rotulo"] == "Estudar na terça das 21h às 22h"
    assert {x["dia"]: x["inicio"] for x in primeira["semana"]}[1] == ""  # no lugar da Rotina: segue a Rotina


def test_estudo_que_come_o_lazer_avisa_e_propoe_menos_tempo():
    r = rotina.montar(ROTINA, {0: ("21:00", 240)})
    assert ("21:00", "01:00", "estudo") in blocos(r, 0)  # cabe: o aviso não tira o estudo
    [aviso] = r["avisos"]
    assert aviso["tipo"] == "atencao" and "não sobra tempo livre" in aviso["texto"]
    assert aviso["propostas"][0]["rotulo"] == "Estudar 3h na segunda"
    assert aviso["propostas"][0]["semana"] == [{"dia": 0, "inicio": "21:00", "minutos": 180}]


def test_sem_lugar_algum_propoe_menos_tempo_e_a_frase_fala_certo():
    so_sabado = {**ROTINA, "grades": [SABADO]}
    [aviso] = rotina.montar(so_sabado, {5: ("", 150)})["avisos"]
    assert aviso["texto"] == "Sábado: a Rotina não tem 2h30 livres seguidas; das 12h20 às 23h é “Compromisso”."
    assert [p["rotulo"] for p in aviso["propostas"]] == ["Estudar 1h no sábado, das 23h à meia-noite"]


def test_rotina_sem_grades_passa_inteira():
    assert rotina.montar({"grades": [], "regras": []}, {0: ("", 60)}) == {"grades": [], "regras": [], "estudo": [],
                                                                           "avisos": []}


CORINGA = {**ROTINA, "coringa": {"minutos": 30, "titulo": "Coringa", "nota": "Para o imprevisto."}}


def test_o_coringa_vem_logo_depois_do_estudo_e_o_dia_sem_estudo_nao_tem():
    r = rotina.montar(CORINGA, {0: ("", 150), 6: ("", 150)})
    assert blocos(r, 0)[3:6] == [("21:00", "23:30", "estudo"), ("23:30", "00:00", "coringa"), ("00:00", "01:00", "livre")]
    assert ("16:30", "17:00", "coringa") in blocos(r, 6)
    assert all(t != "coringa" for *_, t in blocos(r, 2))  # quarta é folga: sem estudo, sem coringa
    coringa = next(x for x in r["grades"][0]["blocos"] if x["tipo"] == "coringa")
    assert coringa["titulo"] == "Coringa" and coringa["nota"] == "Para o imprevisto."
    assert r["avisos"] == [] and r["estudo"][0]["fim"] == "23:30"  # o fim do estudo não conta o coringa
    cobre_o_dia(r)


def test_o_coringa_encolhe_quando_falta_lugar_e_nao_conta_como_lazer():
    r = rotina.montar(CORINGA, {0: ("21:00", 180), 1: ("21:00", 225), 2: ("21:00", 240)})
    assert ("00:00", "00:30", "coringa") in blocos(r, 0)
    assert ("00:45", "01:00", "coringa") in blocos(r, 1)  # só sobram 15 min antes de desligar
    assert all(t != "coringa" for *_, t in blocos(r, 2))
    segunda = next(a for a in r["avisos"] if a["dia"] == 0)
    assert segunda["tipo"] == "atencao" and "sobram só 30 min livres" in segunda["texto"]
    assert segunda["propostas"][0]["rotulo"] == "Estudar 2h30 na segunda"  # 2h30 + coringa ainda deixa 1h livre
    cobre_o_dia(r)
