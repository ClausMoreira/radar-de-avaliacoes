"""Testes do classificador. Nenhum deles usa rede: o Gemini é substituído."""

import pytest

from radar.classificador import (
    ESQUEMA, MARCA_AVALIACOES, MARCA_CATEGORIAS,
    carregar_prompt, classificar, extrair_motivos, montar_prompt,
)
from radar.config import CATEGORIAS
from radar.llm import RespostaInvalida


class GeminiDeMentira:
    """Responde "elogio" para tudo e guarda os prompts que recebeu."""

    def __init__(self):
        self.prompts = []

    def gerar_json(self, prompt, esquema, validar=None):
        self.prompts.append(prompt)
        quantidade = prompt.count('{"id":')
        dados = {"classificacoes": [{"id": n, "motivo": "elogio"} for n in range(1, quantidade + 1)]}
        if validar is not None:
            validar(dados)
        return dados


def test_prompt_v1_tem_as_duas_marcas():
    texto = carregar_prompt("v1")
    assert MARCA_CATEGORIAS in texto
    assert MARCA_AVALIACOES in texto


def test_prompt_inexistente_gera_erro_claro():
    with pytest.raises(FileNotFoundError):
        carregar_prompt("versao_que_nao_existe")


def test_prompt_montado_tem_todos_os_motivos_e_textos():
    prompt = montar_prompt(carregar_prompt("v1"), ["Não chegou", 'Veio "quebrado"'])
    for nome in CATEGORIAS:
        assert nome in prompt
    assert '{"id": 1, "texto": "Não chegou"}' in prompt
    assert '{"id": 2, "texto": "Veio \\"quebrado\\""}' in prompt  # aspas escapadas
    assert MARCA_CATEGORIAS not in prompt and MARCA_AVALIACOES not in prompt


def test_esquema_limita_o_motivo_a_lista():
    motivo = ESQUEMA["properties"]["classificacoes"]["items"]["properties"]["motivo"]
    assert motivo["enum"] == list(CATEGORIAS)


def test_extrai_motivos_na_ordem_do_lote_mesmo_se_vierem_fora_de_ordem():
    dados = {"classificacoes": [{"id": 2, "motivo": "atraso"}, {"id": 1, "motivo": "elogio"}]}
    assert extrair_motivos(dados, 2) == ["elogio", "atraso"]


@pytest.mark.parametrize(
    "dados",
    [
        {"classificacoes": [{"id": 1, "motivo": "elogio"}]},                                 # faltou a 2
        {"classificacoes": [{"id": 1, "motivo": "elogio"}, {"id": 1, "motivo": "atraso"}]},  # repetida
        {"classificacoes": [{"id": 1, "motivo": "elogio"}, {"id": 7, "motivo": "atraso"}]},  # número estranho
        {"classificacoes": [{"id": 1, "motivo": "elogio"}, {"id": 2, "motivo": "preço"}]},   # fora da lista
        {"resultado": []},                                                                   # sem a lista
        ["elogio", "atraso"],                                                                # formato errado
    ],
)
def test_resposta_errada_e_rejeitada(dados):
    with pytest.raises(RespostaInvalida):
        extrair_motivos(dados, 2)


def test_classifica_em_lotes_e_devolve_um_motivo_por_texto():
    gemini = GeminiDeMentira()
    textos = [f"avaliação {n}" for n in range(7)]
    andamento = []

    motivos = classificar(
        textos, "v1", gemini, por_lote=3,
        ao_concluir_lote=lambda feitas, total: andamento.append((feitas, total)),
    )

    assert motivos == ["elogio"] * 7
    assert len(gemini.prompts) == 3              # lotes de 3, 3 e 1
    assert andamento == [(3, 7), (6, 7), (7, 7)]
    assert "avaliação 6" in gemini.prompts[2]
    assert "avaliação 0" not in gemini.prompts[2]
