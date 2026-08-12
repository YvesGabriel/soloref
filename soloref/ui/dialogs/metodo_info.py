"""Diálogo 'Estabilidade interna — Geometria e hipóteses'.

Replica a janela mostrada antes de rodar cada método no programa
original: abas de Coulomb, Rankine e Dois Blocos, com figura da
geometria da cunha de ruptura e texto das hipóteses.
"""
from __future__ import annotations

import math
from typing import Iterable

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPlainTextEdit, QCheckBox, QPushButton, QLabel,
)

from ...core.methods import (
    MetodoAnalise, MetodoCoulomb, MetodoRankine, MetodoDoisBlocos,
    MetodoBishop, MetodoGeossintetico,
)


# --------------------------------------------------------------------------- #
# Desenho genérico das figuras de cunha
# --------------------------------------------------------------------------- #
class _FiguraCunha(QWidget):
    """Desenho simples da cunha de ruptura de cada método."""

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind  # "coulomb" | "rankine" | "dois_blocos"
        self.setMinimumSize(340, 200)
        self.setStyleSheet("background:#fff; border:1px solid #888;")

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), Qt.white)

        w, h = self.width(), self.height()
        m = 20
        base_y = h - m - 20
        face_x = m + 60
        top_y = m + 20
        top_x = w - m - 30

        pen_solid = QPen(QColor("#000"), 1.8)
        pen_dash = QPen(QColor("#000"), 1, Qt.DashLine)
        p.setPen(pen_solid)

        # chão
        p.drawLine(m, base_y, w - m, base_y)

        if self.kind == "coulomb":
            # muro vertical, cunha única plana
            p.drawLine(face_x, base_y, face_x, top_y)            # face (parede)
            p.drawLine(face_x, top_y, top_x, top_y)              # topo
            p.drawLine(face_x, base_y, top_x, top_y)             # cunha
            self._setas_q(p, face_x, top_x, top_y)
            p.setPen(QPen(QColor("#000")))
            self._label(p, face_x - 30, (base_y + top_y)/2, "H")
            self._label(p, face_x - 10, top_y - 20, "Ht", italic=True)
            self._label(p, face_x - 14, base_y - 20, "β")
            self._label(p, face_x + 30, base_y - 10, "θ")
            self._label(p, face_x + 90, (base_y+top_y)/2 + 10, "Tf+Tc")
            # W (peso) / E (empuxo) / N
            p.drawText(QRectF(face_x + 36, base_y - 60, 20, 16), Qt.AlignCenter, "W")
            p.drawText(QRectF(face_x - 18, base_y - 50, 20, 16), Qt.AlignCenter, "E")
            p.drawText(QRectF(face_x + 50, base_y - 35, 20, 16), Qt.AlignCenter, "N")

        elif self.kind == "rankine":
            # camadas horizontais dentro da parede reforçada
            p.drawLine(face_x, base_y, face_x, top_y)
            p.drawLine(face_x, top_y, top_x, top_y)
            # cunha 45+phi/2 (representativa: usa 60°)
            ang = math.radians(60)
            dx = (base_y - top_y) / math.tan(ang)
            p.drawLine(face_x, base_y, face_x + dx, top_y)
            # camadas de reforço (linhas horizontais dentro da parede)
            n_camadas = 5
            p.setPen(pen_dash)
            for i in range(1, n_camadas + 1):
                y = base_y - i * (base_y - top_y) / (n_camadas + 1)
                p.drawLine(face_x, y, face_x + dx, y)
            p.setPen(pen_solid)
            self._setas_q(p, face_x, top_x, top_y)
            self._label(p, face_x - 26, (base_y + top_y)/2, "H")
            self._label(p, face_x + 3, top_y + 10, "i")
            self._label(p, face_x - 14, base_y - 20, "β")
            self._label(p, top_x - 10, base_y - 20, "βe")
            p.drawText(QRectF(face_x + dx + 4, top_y + 4, 30, 16),
                       Qt.AlignLeft, "Wa")
            p.drawText(QRectF(face_x + dx - 20, top_y + 20, 24, 16),
                       Qt.AlignCenter, "sv")

        else:  # dois_blocos
            # cunha bilinear
            p.drawLine(face_x, base_y, face_x + 40, top_y + 30)  # muro inclinado
            p.drawLine(face_x + 40, top_y + 30, top_x, top_y + 30)  # topo
            meio_x = face_x + 90
            topo_ruptura_x = face_x + 40
            p.drawLine(face_x, base_y, meio_x, base_y - 40)       # bloco 1
            p.drawLine(meio_x, base_y - 40, topo_ruptura_x, top_y + 30)  # bloco 2
            self._setas_q(p, face_x + 40, top_x, top_y + 30)
            self._label(p, face_x - 10, (base_y + top_y)/2, "H")
            self._label(p, face_x - 14, base_y - 16, "β")
            # pesos
            p.drawText(QRectF(face_x + 20, base_y - 40, 30, 16),
                       Qt.AlignCenter, "W1")
            p.drawText(QRectF(meio_x - 8, base_y - 60, 30, 16),
                       Qt.AlignCenter, "W2")
            # d1, L1, d2, L2
            p.drawText(QRectF(face_x + 10, base_y + 2, 30, 16),
                       Qt.AlignLeft, "d1")
            p.drawText(QRectF(meio_x - 4, base_y + 2, 30, 16),
                       Qt.AlignLeft, "d2")

        p.end()

    def _setas_q(self, p: QPainter, x1: int, x2: int, y: int):
        """Setinhas de sobrecarga q no topo."""
        n = 7
        p.setPen(QPen(QColor("#000"), 1))
        for k in range(n):
            x = x1 + (x2 - x1) * k / (n - 1)
            p.drawLine(int(x), y - 12, int(x), y - 1)
            p.drawLine(int(x), y - 1, int(x - 3), y - 5)
            p.drawLine(int(x), y - 1, int(x + 3), y - 5)
        p.drawText(QRectF(x2 + 2, y - 16, 14, 14), Qt.AlignLeft, "q")

    def _label(self, p: QPainter, x, y, txt, italic=False):
        font = QFont()
        font.setPointSize(9)
        font.setItalic(italic)
        p.setFont(font)
        p.drawText(QRectF(x, y, 40, 16), Qt.AlignLeft, txt)


# --------------------------------------------------------------------------- #
# Aba de um método
# --------------------------------------------------------------------------- #
class _AbaMetodo(QWidget):
    def __init__(self, metodo: MetodoAnalise, kind: str, descricao: str):
        super().__init__()
        grp_geo = QGroupBox("Geometria")
        fig = _FiguraCunha(kind)
        gl = QVBoxLayout(grp_geo)
        gl.addWidget(fig)

        desc = QLabel(descricao)
        desc.setWordWrap(True)

        grp_hip = QGroupBox("Hipóteses do método")
        hip = QPlainTextEdit()
        hip.setReadOnly(True)
        hip.setPlainText("\n".join(f"- {h}" for h in metodo.hipoteses))
        hip.setFixedHeight(110)
        hl = QVBoxLayout(grp_hip)
        hl.addWidget(hip)

        lay = QVBoxLayout(self)
        lay.addWidget(grp_geo, 1)
        lay.addWidget(desc)
        lay.addWidget(grp_hip)


# --------------------------------------------------------------------------- #
# Diálogo com as três (ou mais) abas
# --------------------------------------------------------------------------- #
class MetodoInfoDialog(QDialog):
    def __init__(self, parent=None, aba_inicial: int = 0,
                 incluir_novos: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Estabilidade interna - Geometria e hipóteses")
        self.resize(560, 560)

        tabs = QTabWidget()
        tabs.addTab(
            _AbaMetodo(
                MetodoCoulomb(), "coulomb",
                "O método de dimensionamento é o proposto por Coulomb, "
                "que considera simplesmente o equilíbrio de esforços na "
                "cunha de ruptura plana.",
            ),
            "Método de Coulomb",
        )
        tabs.addTab(
            _AbaMetodo(
                MetodoRankine(), "rankine",
                "Análise por estado ativo de Rankine: a inclinação da "
                "cunha de ruptura é fixada em 45° + φ/2, e as "
                "solicitações atuam na parede da estrutura.",
            ),
            "Método de Rankine",
        )
        tabs.addTab(
            _AbaMetodo(
                MetodoDoisBlocos(), "dois_blocos",
                "O método ajusta a cunha de ruptura através de uma proposta "
                "de cunha bi-linear, e, assim como no de Coulomb, analisa "
                "o equilíbrio de esforços sobre essa cunha.",
            ),
            "Método dos Dois Blocos",
        )
        if incluir_novos:
            tabs.addTab(
                _AbaMetodo(
                    MetodoBishop(), "dois_blocos",
                    "Análise por superfície de ruptura circular dividida "
                    "em fatias, com iteração do fator de segurança.",
                ),
                "Método de Bishop",
            )
            tabs.addTab(
                _AbaMetodo(
                    MetodoGeossintetico(), "rankine",
                    "Dimensionamento de camadas de reforço com "
                    "geossintéticos, compondo com os métodos de cunha plana.",
                ),
                "Reforço com geossintéticos",
            )
        tabs.setCurrentIndex(aba_inicial)

        self.chk = QCheckBox("Não mostrar esta tela no dimensionamento")

        btn_ok = QPushButton("&Continuar")
        btn_ok.setDefault(True)
        btn_cancel = QPushButton("&Fechar")
        btn_apoio = QPushButton("&Apoio")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_apoio.clicked.connect(lambda: None)

        row = QHBoxLayout()
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        row.addWidget(btn_apoio)
        row.addStretch()

        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addWidget(self.chk)
        lay.addLayout(row)
