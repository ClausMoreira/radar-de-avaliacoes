"""Testes do classificador. Nenhum deles usa rede: o Gemini é substituído."""

import hashlib

import pytest

from radar.classificador import (
    ESQUEMA, MARCA_AVALIACOES, carregar_prompt, classificar, extrair_motivos, montar_prompt,
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


VERSOES = ["v1", "v2"]


@pytest.mark.parametrize("versao", VERSOES)
def test_cada_prompt_define_todos_os_motivos(versao):
    texto = carregar_prompt(versao)
    assert MARCA_AVALIACOES in texto
    for nome in CATEGORIAS:
        assert f"{nome}:" in texto, f"O prompt {versao} não define {nome}"


def test_prompt_v1_continua_identico_ao_que_foi_medido():
    # Impressão digital do v1 calculada em 14/11/2026, logo depois da medição.
    # Se este teste falhar, o v1 mudou: o resultado medido deixa de valer
    # para o arquivo atual e o cache deixa de ser usado.
    prompt = montar_prompt(carregar_prompt("v1"), ["Ainda não chegou.", 'Veio "quebrado", quero devolver.'])
    impressao = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    assert impressao == "f7d56a0fd0e5d9d2ea7e970363fed8fb9ef2ac959c14294052f4e3a0e9b7069e"


def test_prompt_sem_a_marca_de_avaliacoes_e_recusado(tmp_path, monkeypatch):
    (tmp_path / "classificacao_quebrado.md").write_text("Sem marca nenhuma.", encoding="utf-8")
    monkeypatch.setattr("radar.classificador.PASTA_PROMPTS", tmp_path)
    with pytest.raises(ValueError):
        carregar_prompt("quebrado")


def test_prompt_inexistente_gera_erro_claro():
    with pytest.raises(FileNotFoundError):
        carregar_prompt("versao_que_nao_existe")


def test_prompt_montado_tem_os_textos_numerados():
    prompt = montar_prompt(carregar_prompt("v2"), ["Não chegou", 'Veio "quebrado"'])
    assert '{"id": 1, "texto": "Não chegou"}' in prompt
    assert '{"id": 2, "texto": "Veio \\"quebrado\\""}' in prompt  # aspas escapadas
    assert MARCA_AVALIACOES not in prompt


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


class GeminiQueFalhaEmLotesGrandes(GeminiDeMentira):
    """Recusa lotes com mais de 2 avaliações, como um modelo que se perde."""

    def gerar_json(self, prompt, esquema, validar=None):
        if prompt.count('{"id":') > 2:
            self.prompts.append(prompt)
            raise RespostaInvalida("simulado")
        return super().gerar_json(prompt, esquema, validar)


def test_lote_que_falha_e_dividido_ao_meio_sem_perder_avaliacoes():
    gemini = GeminiQueFalhaEmLotesGrandes()
    motivos = classificar([f"avaliação {n}" for n in range(5)], "v2", gemini, por_lote=5)
    assert motivos == ["elogio"] * 5
    # 5 falha, divide em 2 + 3; o 3 falha e vira 1 + 2.
    assert [p.count('{"id":') for p in gemini.prompts] == [5, 2, 3, 1, 2]


def test_avaliacao_que_falha_sozinha_interrompe_com_erro():
    class SempreFalha(GeminiDeMentira):
        def gerar_json(self, prompt, esquema, validar=None):
            raise RespostaInvalida("simulado")

    with pytest.raises(RespostaInvalida):
        classificar(["a", "b"], "v2", SempreFalha(), por_lote=2)
