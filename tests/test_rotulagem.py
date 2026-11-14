import pandas as pd

from radar.rotulagem import montar_planilha, validar


def test_planilha_nao_mostra_nota_nem_resposta_do_modelo():
    amostra = pd.DataFrame({"review_id": ["a", "b"], "texto": ["Chegou rápido", "Não chegou"]})
    aba = montar_planilha(amostra)["rotular"]
    cabecalho = [celula.value for celula in aba[1]]
    assert cabecalho == ["review_id", "texto", "motivo", "duvida", "observacao"]
    assert aba["C2"].value is None and aba["C3"].value is None


def test_validar_aponta_linhas_vazias_motivo_invalido_e_repeticao():
    planilha = pd.DataFrame(
        {"review_id": ["a", "b", "b"], "motivo": ["elogio", "", "preco"], "texto": ["", "", ""]}
    )
    problemas = validar(planilha)
    assert len(problemas) == 3
    assert "Linhas da planilha: 3" in problemas[0]   # a linha 1 é o cabeçalho


def test_validar_aceita_planilha_completa():
    planilha = pd.DataFrame({"review_id": ["a", "b"], "motivo": ["elogio", "atraso"]})
    assert validar(planilha) == []
