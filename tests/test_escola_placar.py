from datetime import date, datetime

from escola.placar import Registros, pontos_da_semana, pontos_por_dia, segunda_de, sequencia, semanas, vencedores

SEG = date(2026, 10, 26)  # uma segunda


def test_aula_vale_os_minutos_e_questao_vale_2_uma_vez_por_semana():
    r = Registros(aulas=[(datetime(2026, 10, 27, 20), 30)],
                  questoes=[(datetime(2026, 10, 27, 21), "aula1#0"), (datetime(2026, 10, 27, 21), "aula1#1"),
                            (datetime(2026, 10, 29, 21), "aula1#0"),  # refez a lista: não soma de novo
                            (datetime(2026, 10, 29, 21), "aq:2026-10-29#0")])  # o aquecimento é outro alvo
    assert pontos_da_semana(r, SEG) == 30 + 2 * 3
    assert pontos_da_semana(r, date(2026, 11, 2)) == 0


def test_a_semana_vira_na_segunda_as_4h():
    r = Registros(aulas=[(datetime(2026, 11, 2, 3, 30), 20), (datetime(2026, 11, 2, 4, 30), 10)], questoes=[])
    assert pontos_da_semana(r, SEG) == 20  # a madrugada de segunda ainda é do domingo
    assert pontos_da_semana(r, date(2026, 11, 2)) == 10
    assert segunda_de(date(2026, 11, 1)) == SEG


def test_no_dia_a_questao_conta_uma_vez_por_dia():
    r = Registros(aulas=[], questoes=[(datetime(2026, 10, 27, 9), "a#0"), (datetime(2026, 10, 27, 10), "a#0"),
                                      (datetime(2026, 10, 28, 9), "a#0")])
    assert pontos_por_dia(r) == {date(2026, 10, 27): 2, date(2026, 10, 28): 2}


def test_sequencia_pula_folga_e_hoje_pendente_nao_quebra():
    dias_de_estudo = {0, 1, 2, 3, 4}  # segunda a sexta
    por_dia = {date(2026, 10, 23): 20,  # sexta
               date(2026, 10, 26): 15,  # segunda (sábado e domingo são folga)
               date(2026, 10, 27): 40}
    assert sequencia(por_dia, date(2026, 10, 28), dias_de_estudo) == 3  # quarta ainda sem estudo: não quebrou
    assert sequencia(por_dia, date(2026, 10, 29), dias_de_estudo) == 0  # quarta passou em branco
    assert sequencia({**por_dia, date(2026, 10, 25): 30}, date(2026, 10, 27), dias_de_estudo) == 4  # estudou na folga


def test_dia_com_menos_de_15_nao_conta():
    assert sequencia({date(2026, 10, 27): 14}, date(2026, 10, 27), {0, 1, 2, 3, 4, 5, 6}) == 0


def test_semanas_e_vencedores_com_empate():
    ana = Registros(aulas=[(datetime(2026, 10, 20, 9), 30), (datetime(2026, 10, 27, 9), 50)], questoes=[])
    bia = Registros(aulas=[(datetime(2026, 10, 21, 9), 30)], questoes=[])
    s = semanas({"ana": ana, "bia": bia}, date(2026, 10, 30))
    assert s == {date(2026, 10, 19): {"ana": 30, "bia": 30}}  # só as semanas que já acabaram
    assert vencedores(s[date(2026, 10, 19)]) == {"ana", "bia"}
    assert vencedores({"ana": 0, "bia": 0}) == set()
    assert vencedores({"ana": 90, "bia": 0}) == set()  # estudou sozinha: não houve disputa
    assert vencedores({"ana": 90, "bia": 10, "caio": 0}) == {"ana"}
