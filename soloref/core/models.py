"""Modelos de dados do projeto SoloRef.

Cada classe corresponde a uma das abas do diálogo de Entrada de Dados
do programa original. Mantemos as unidades originais (kN/m², kN/m³, m,
graus) nos nomes dos campos para fidelidade ao programa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------- #
# Aba: Identificação do projeto
# --------------------------------------------------------------------------- #
@dataclass
class Identificacao:
    identificacao: str = "(não especificado)"
    empresa: str = "(não especificada)"
    numero_dimensionamento: int = 1


# --------------------------------------------------------------------------- #
# Aba: Geometria da estrutura
# --------------------------------------------------------------------------- #
@dataclass
class Geometria:
    altura_H_m: float = 4.0          # Altura da parte reforçada, H (m)
    inclinacao_face_beta_g: float = 90.0   # Inclinação da face, β (graus)
    largura_aterro_B_m: float = 5.0  # Largura do aterro, B (m)
    inclinacao_encosta_beta_e_g: float = 90.0  # Inclinação da encosta, βe (graus)
    inclinacao_topo_i_g: float = 0.0   # Inclinação do talude de topo, i (graus)
    altura_topo_Ht_m: float = 0.0      # Altura do talude de topo, Ht (m)


# --------------------------------------------------------------------------- #
# Aba: Face da estrutura
# --------------------------------------------------------------------------- #
@dataclass
class FaceEstrutura:
    considera_blocos: bool = False
    altura_blocos_cm: Optional[float] = None
    largura_blocos_cm: Optional[float] = None
    recuo_blocos_cm: Optional[float] = None


# --------------------------------------------------------------------------- #
# Abas: Solo de aterro / encosta / fundação
# --------------------------------------------------------------------------- #
@dataclass
class Solo:
    """Parâmetros geotécnicos de um solo.

    `angulo_atrito_blocos_g` só faz sentido para o solo de aterro
    (os outros podem deixar como None).
    """
    peso_especifico_kN_m3: float = 20.0
    coesao_kN_m2: float = 0.0
    angulo_atrito_g: float = 30.0
    angulo_atrito_blocos_g: Optional[float] = None  # só p/ aterro


# --------------------------------------------------------------------------- #
# Aba: Sobrecarga
# --------------------------------------------------------------------------- #
@dataclass
class Sobrecarga:
    uniforme_q_kN_m2: float = 0.0
    trem_tipo_P_kN_m: float = 0.0     # carga linear (trem-tipo)
    posicao_xo_m: float = 0.0
    eixo_e_m: float = 0.0


# --------------------------------------------------------------------------- #
# Projeto inteiro
# --------------------------------------------------------------------------- #
@dataclass
class Projeto:
    """Agrega tudo que o usuário preenche em Entrada de Dados."""
    identificacao: Identificacao = field(default_factory=Identificacao)
    geometria: Geometria = field(default_factory=Geometria)
    face: FaceEstrutura = field(default_factory=FaceEstrutura)
    solo_aterro: Solo = field(
        default_factory=lambda: Solo(
            peso_especifico_kN_m3=20.0,
            coesao_kN_m2=0.0,
            angulo_atrito_g=30.0,
            angulo_atrito_blocos_g=30.0,
        )
    )
    solo_encosta: Solo = field(default_factory=Solo)
    solo_fundacao: Solo = field(
        default_factory=lambda: Solo(
            peso_especifico_kN_m3=20.0,
            coesao_kN_m2=15.0,
            angulo_atrito_g=30.0,
        )
    )
    sobrecarga: Sobrecarga = field(default_factory=Sobrecarga)
