"""Salvar / carregar projetos em JSON.

Formato simples e legível — melhor que um binário proprietário e permite
versionamento por git se o usuário quiser.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import (
    Projeto,
    Identificacao,
    Geometria,
    FaceEstrutura,
    Solo,
    Sobrecarga,
)

EXTENSAO = ".soloref.json"


def salvar(projeto: Projeto, caminho: str | Path) -> None:
    caminho = Path(caminho)
    if caminho.suffix != ".json":
        caminho = caminho.with_suffix(EXTENSAO)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(asdict(projeto), f, indent=2, ensure_ascii=False)


def carregar(caminho: str | Path) -> Projeto:
    with Path(caminho).open(encoding="utf-8") as f:
        data = json.load(f)
    return Projeto(
        identificacao=Identificacao(**data["identificacao"]),
        geometria=Geometria(**data["geometria"]),
        face=FaceEstrutura(**data["face"]),
        solo_aterro=Solo(**data["solo_aterro"]),
        solo_encosta=Solo(**data["solo_encosta"]),
        solo_fundacao=Solo(**data["solo_fundacao"]),
        sobrecarga=Sobrecarga(**data["sobrecarga"]),
    )
