"""Quadro resumo — tabela comparativa das últimas 8 situações analisadas.

Replica a janela 'Quadro resumo' do programa original, com os mesmos
rótulos. Por enquanto preenche as colunas a partir do projeto corrente;
quando os métodos estiverem implementados, basta chamar `set_situacao`
com o `Resultado` de cada um.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout,
)

from ...core.models import Projeto

LINHAS = [
    "situação",
    "altura da parte reforçada (m)",
    "inclinação da face (°)",
    "inclinação do topo (°)",
    "altura do topo (m)",
    "embutimento (m)",
    "ângulo de atrito (°)",
    "atrito entre blocos (°)",
    "coesão (kN/m²)",
    "peso espec. ap. total (kN/m³)",
    "sobrecarga uniforme (kN/m²)",
    "sobrecarga linear (kN/m)",
    "posição da carga (m)",
    "eixo (m)",
    "número de camadas",
    "solicit., Mét. Coulomb (kN/m)",
    "inclinação da cunha (°)",
    "solicit., Mét. Rankine (kN/m)",
    "inclinação da cunha (°)",
    "solicit., Mét. Dois Blocos (kN/m)",
    "ponto de inflexão (m)",
    "1ª inclinação da cunha (°)",
    "2ª inclinação da cunha (°)",
    "FS, Mét. Bishop",
    "FS deslizamento",
    "FS tombamento",
    "FS capacidade de carga",
]

N_SITUACOES = 8


class QuadroResumoWidget(QWidget):
    """Widget (não diálogo) para ser usado dentro da MDIArea."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quadro resumo")

        titulo = QLabel(
            "Quadro comparativo da análise da estabilidade interna "
            "nas últimas oito situações consideradas"
        )
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-weight: bold; padding: 4px;")

        self.tabela = QTableWidget(len(LINHAS), N_SITUACOES + 1)
        self.tabela.setHorizontalHeaderLabels(
            [""] + [str(i) for i in range(1, N_SITUACOES + 1)]
        )
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        for c in range(1, N_SITUACOES + 1):
            self.tabela.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.Stretch
            )

        for r, nome in enumerate(LINHAS):
            item = QTableWidgetItem(nome)
            item.setFlags(Qt.ItemIsEnabled)
            self.tabela.setItem(r, 0, item)

        # Barra de ações: apagar situações registradas.
        self.btn_remover = QPushButton("Remover última")
        self.btn_remover.setToolTip("Apaga a última situação registrada no quadro")
        self.btn_remover.clicked.connect(self.remover_ultima)
        self.btn_limpar = QPushButton("Limpar tudo")
        self.btn_limpar.setToolTip("Apaga todas as situações do quadro")
        self.btn_limpar.clicked.connect(self.limpar)
        barra = QHBoxLayout()
        barra.addStretch()
        barra.addWidget(self.btn_remover)
        barra.addWidget(self.btn_limpar)

        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addLayout(barra)
        lay.addWidget(self.tabela)

        self.situacoes: list[dict] = []

    # ------------------------------------------------------------------ #
    def adicionar_situacao(self, projeto: Projeto,
                           resultados: dict | None = None) -> None:
        """Adiciona uma nova situação à coluna disponível mais à esquerda.

        `resultados` é um dict opcional com chaves de cada método
        (ex.: 'coulomb_solicit', 'coulomb_cunha', ...). Pode vir vazio
        enquanto os cálculos não estão implementados.
        """
        resultados = resultados or {}
        self.situacoes.append({"projeto": projeto, "resultados": resultados})
        self.situacoes = self.situacoes[-N_SITUACOES:]
        self._repreencher()

    def limpar(self) -> None:
        """Esvazia todas as situações e as células de resultado (menu Novo /
        botão 'Limpar tudo')."""
        self.situacoes = []
        self._limpar_celulas()

    def remover_ultima(self) -> None:
        """Remove apenas a última situação registrada e redesenha o quadro."""
        if not self.situacoes:
            return
        self.situacoes.pop()
        self._limpar_celulas()
        self._repreencher()

    def _limpar_celulas(self) -> None:
        """Esvazia as células de resultado (colunas 1..N), preservando os
        rótulos das linhas na coluna 0."""
        for r in range(len(LINHAS)):
            for c in range(1, N_SITUACOES + 1):
                self.tabela.setItem(r, c, QTableWidgetItem(""))

    # ------------------------------------------------------------------ #
    def _repreencher(self):
        for col_idx, item in enumerate(self.situacoes, start=1):
            self._preencher_coluna(col_idx, item["projeto"], item["resultados"])

    def _preencher_coluna(self, col: int, projeto: Projeto, res: dict):
        g = projeto.geometria
        s = projeto.sobrecarga
        a = projeto.solo_aterro
        valores = [
            str(col),
            f"{g.altura_H_m:g}",
            f"{g.inclinacao_face_beta_g:g}",
            f"{g.inclinacao_topo_i_g:g}",
            f"{g.altura_topo_Ht_m:g}",
            f"{g.embutimento_m:g}",
            f"{a.angulo_atrito_g:g}",
            f"{a.angulo_atrito_blocos_g or 0:g}",
            f"{a.coesao_kN_m2:g}",
            f"{a.peso_especifico_kN_m3:g}",
            f"{s.uniforme_q_kN_m2:g}",
            f"{s.trem_tipo_P_kN_m:g}",
            f"{s.posicao_xo_m:g}",
            f"{s.eixo_e_m:g}",
            _fmt(res.get("n_camadas")),
            _fmt(res.get("coulomb_solicit")),
            _fmt(res.get("coulomb_cunha")),
            _fmt(res.get("rankine_solicit")),
            _fmt(res.get("rankine_cunha")),
            _fmt(res.get("db_solicit")),
            _fmt(res.get("db_inflexao")),
            _fmt(res.get("db_cunha1")),
            _fmt(res.get("db_cunha2")),
            _fmt(res.get("bishop_fs")),
            _fmt(res.get("ext_fs_desl")),
            _fmt(res.get("ext_fs_tomb")),
            _fmt(res.get("ext_fs_cap")),
        ]
        for row, val in enumerate(valores):
            it = QTableWidgetItem(val)
            it.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(row, col, it)


def _fmt(v) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return str(v)
