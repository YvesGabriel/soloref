"""Smoke-test do core (sem precisar de Qt)."""
import json
from dataclasses import asdict

from soloref.core import Projeto
from soloref.core.persistence import salvar, carregar


def test_projeto_default(tmp_path):
    p = Projeto()
    assert p.geometria.altura_H_m == 4.0
    assert p.solo_aterro.angulo_atrito_g == 30.0


def test_round_trip(tmp_path):
    p = Projeto()
    f = tmp_path / "x.json"
    salvar(p, f)
    p2 = carregar(f)
    assert p2.geometria.altura_H_m == p.geometria.altura_H_m


def test_carregar_ignora_secoes_e_campos_desconhecidos(tmp_path):
    """Projetos antigos tinham as abas "face" e "identificacao" (removidas
    do modelo) e podem ter campos que já saíram de uma dataclass ainda
    existente (ex.: "solo_aterro" com uma chave que não existe mais) —
    `carregar()` deve ignorar tudo isso em vez de quebrar."""
    p = Projeto()
    f = tmp_path / "antigo.json"
    dados = {
        "geometria": {**asdict(p.geometria), "campo_removido": 1},
        "solo_aterro": asdict(p.solo_aterro),
        "solo_encosta": asdict(p.solo_encosta),
        "solo_fundacao": asdict(p.solo_fundacao),
        "sobrecarga": asdict(p.sobrecarga),
        "reforco": asdict(p.reforco),
        "face": {"considera_blocos": False},
        "identificacao": {"identificacao": "Projeto antigo", "empresa": "X"},
    }
    f.write_text(json.dumps(dados), encoding="utf-8")

    p2 = carregar(f)
    assert p2.geometria.altura_H_m == p.geometria.altura_H_m
    assert p2.solo_aterro.angulo_atrito_g == p.solo_aterro.angulo_atrito_g
