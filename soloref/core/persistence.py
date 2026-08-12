"""Salvar / carregar projetos em JSON.

Formato simples e legível — melhor que um binário proprietário e permite
versionamento por git se o usuário quiser.
"""
from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Type, TypeVar

from .models import (
    Projeto,
    Geometria,
    Solo,
    Sobrecarga,
    Reforco,
)

EXTENSAO = ".soloref.json"

_T = TypeVar("_T")


def _filtra_campos(cls: Type[_T], dados: dict) -> dict:
    """Mantém só as chaves de `dados` que correspondem a campos de `cls`.

    Protege `carregar()` contra seções/campos que existiram no passado (ex.:
    "face", "identificacao") e ainda aparecem em arquivos `.soloref.json`
    salvos por versões antigas do programa — em vez de quebrar com
    `TypeError: unexpected keyword argument`, o campo desconhecido é
    simplesmente ignorado.
    """
    campos = {f.name for f in fields(cls)}
    return {k: v for k, v in dados.items() if k in campos}


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
        geometria=Geometria(**_filtra_campos(Geometria, data.get("geometria", {}))),
        solo_aterro=Solo(**_filtra_campos(Solo, data.get("solo_aterro", {}))),
        solo_encosta=Solo(**_filtra_campos(Solo, data.get("solo_encosta", {}))),
        solo_fundacao=Solo(**_filtra_campos(Solo, data.get("solo_fundacao", {}))),
        sobrecarga=Sobrecarga(**_filtra_campos(Sobrecarga, data.get("sobrecarga", {}))),
        reforco=Reforco(**_filtra_campos(Reforco, data.get("reforco", {}))),
    )
