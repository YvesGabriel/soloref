"""Smoke-test do core (sem precisar de Qt)."""
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
