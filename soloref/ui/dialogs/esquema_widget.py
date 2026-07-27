"""Widget que desenha o 'Esquema ilustrativo' do muro de solo reforçado.

Reproduz a figura que aparece à direita em todas as abas do diálogo de
Entrada de Dados do programa original (parte reforçada vertical, talude
de topo, encosta, sobrecargas q e P). Os parâmetros vêm do `Projeto`,
então o desenho é vivo: muda conforme o usuário edita os campos.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QPainterPath
)
from PySide6.QtWidgets import QWidget

from ...core.models import Projeto


class EsquemaWidget(QWidget):
    """Desenho vetorial 2D do muro. Sem dependências externas (puro Qt)."""

    def __init__(self, projeto: Projeto, parent=None):
        super().__init__(parent)
        self.projeto = projeto
        self.setMinimumSize(280, 220)
        self.setStyleSheet("background-color: #c8c8c8;")

    def atualizar(self, projeto: Projeto) -> None:
        self.projeto = projeto
        self.update()

    # ------------------------------------------------------------------ #
    def paintEvent(self, event):  # noqa: N802 (Qt API)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#c8c8c8"))

        g = self.projeto.geometria
        s = self.projeto.sobrecarga

        # Caixa de desenho com margens
        m = 30
        w = self.width() - 2 * m
        h = self.height() - 2 * m
        if w < 50 or h < 50:
            return

        # Escala adaptativa: pega a maior dimensão envolvida
        H = max(g.altura_H_m, 1.0)
        Ht = max(g.altura_topo_Ht_m, 0.0)
        B = max(g.largura_aterro_B_m, 0.5)
        total_h = H + Ht + 1.0
        total_w = B * 2.2
        scale = min(w / total_w, h / total_h)

        # Origem: pé do muro
        x0 = m + w * 0.30
        y0 = m + h * 0.85

        beta = math.radians(g.inclinacao_face_beta_g)
        beta_e = math.radians(g.inclinacao_encosta_beta_e_g)
        i_topo = math.radians(g.inclinacao_topo_i_g)

        # Pontos (em coordenadas de tela: y cresce p/ baixo, então
        # subimos invertendo o sinal de Δy)
        # P0 = pé do muro (frente); P1 = topo da face reforçada;
        # P2 = topo do talude (após Ht); pontos internos para encosta
        dy_face = H * scale
        dx_face = (H / math.tan(beta)) * scale if beta != math.pi / 2 else 0.0
        P0 = QPointF(x0, y0)
        P1 = QPointF(x0 + dx_face, y0 - dy_face)

        # Topo (segue inclinação i por largura B)
        dx_topo = B * scale
        dy_topo = -B * math.tan(i_topo) * scale  # sobe se i > 0
        P2 = QPointF(P1.x() + dx_topo, P1.y() + dy_topo)

        # Encosta atrás: sobe Ht com inclinação βe
        dy_enc = Ht * scale
        dx_enc = (Ht / math.tan(beta_e)) * scale if beta_e != math.pi / 2 else 0.0
        P3 = QPointF(P2.x() + dx_enc, P2.y() - dy_enc)

        # Linha do solo natural (base)
        base_left = QPointF(x0 - 30, y0)
        base_right = QPointF(P3.x() + 30, y0)

        # ---------- desenhar o solo natural / fundação ---------- #
        ground = QPainterPath()
        ground.moveTo(base_left)
        ground.lineTo(base_right)
        ground.lineTo(base_right.x(), y0 + 25)
        ground.lineTo(base_left.x(), y0 + 25)
        ground.closeSubpath()
        p.fillPath(ground, QBrush(QColor("#a89878")))

        # ---------- corpo do muro (face + topo + encosta) ---------- #
        muro = QPolygonF([P0, P1, P2, P3, QPointF(P3.x(), y0)])
        p.setBrush(QBrush(QColor("#d4c8a8")))
        p.setPen(QPen(QColor("#333"), 1.5))
        p.drawPolygon(muro)

        # Linha tracejada interna (cunha de ruptura, ilustrativa)
        pen_dash = QPen(QColor("#0066aa"), 1, Qt.DashLine)
        p.setPen(pen_dash)
        p.drawLine(P0, P2)

        # ---------- sobrecargas no topo ---------- #
        if s.uniforme_q_kN_m2 > 0 or True:  # sempre desenha as setinhas (didático)
            self._desenhar_setas_uniformes(p, P1, P2)
        # carga linear P (uma seta destacada)
        self._desenhar_carga_linear(p, P1, P2, s.posicao_xo_m, scale)

        # ---------- cotas / ângulos ---------- #
        p.setPen(QPen(QColor("#0a8"), 1))
        font = QFont()
        font.setPointSize(8)
        p.setFont(font)
        # H (altura)
        p.drawLine(QPointF(x0 - 15, y0), QPointF(x0 - 15, P1.y()))
        p.drawText(QRectF(x0 - 35, (y0 + P1.y()) / 2 - 8, 18, 16),
                   Qt.AlignCenter, "H")
        # Ht
        if Ht > 0:
            p.drawLine(QPointF(P3.x() + 12, P3.y()),
                       QPointF(P3.x() + 12, P2.y()))
            p.drawText(QRectF(P3.x() + 14, (P3.y() + P2.y()) / 2 - 8, 20, 16),
                       Qt.AlignLeft, "Ht")
        # B (largura aterro)
        p.drawLine(QPointF(P1.x(), y0 + 18),
                   QPointF(P2.x(), y0 + 18))
        p.drawText(QRectF((P1.x() + P2.x()) / 2 - 10, y0 + 18, 20, 14),
                   Qt.AlignCenter, "B")

        # ângulos β / βe
        p.drawText(QRectF(P0.x() + 4, P0.y() - 16, 14, 14),
                   Qt.AlignLeft, "β")
        p.drawText(QRectF(P3.x() - 14, y0 - 16, 14, 14),
                   Qt.AlignRight, "βe")

        p.end()

    # ------------------------------------------------------------------ #
    def _desenhar_setas_uniformes(self, p: QPainter, P1: QPointF, P2: QPointF):
        """Desenha setinhas verticais ao longo do topo (sobrecarga q)."""
        n = 6
        pen = QPen(QColor("#222"), 1.2)
        p.setPen(pen)
        for k in range(n + 1):
            t = k / n
            x = P1.x() + (P2.x() - P1.x()) * t
            y_top = min(P1.y(), P2.y()) - 14
            y_bot = (P1.y() + (P2.y() - P1.y()) * t)
            p.drawLine(QPointF(x, y_top), QPointF(x, y_bot - 1))
            # ponta de seta
            p.drawLine(QPointF(x, y_bot - 1),
                       QPointF(x - 3, y_bot - 5))
            p.drawLine(QPointF(x, y_bot - 1),
                       QPointF(x + 3, y_bot - 5))
        # rótulo q
        p.drawText(QRectF(P2.x() - 4, min(P1.y(), P2.y()) - 28, 14, 14),
                   Qt.AlignLeft, "q")

    def _desenhar_carga_linear(self, p: QPainter, P1: QPointF, P2: QPointF,
                                xo_m: float, scale: float):
        """Seta única (P) representando o trem-tipo."""
        # Posição relativa ao P1 (xo a partir da face)
        x = P1.x() + xo_m * scale
        if not (P1.x() <= x <= P2.x()):
            x = (P1.x() + P2.x()) / 2  # se fora, mostra no meio
        y_top = min(P1.y(), P2.y()) - 22
        y_bot = P1.y() + (x - P1.x()) / max(P2.x() - P1.x(), 1e-6) \
                * (P2.y() - P1.y()) - 1
        pen = QPen(QColor("#a00"), 1.8)
        p.setPen(pen)
        p.drawLine(QPointF(x, y_top), QPointF(x, y_bot))
        p.drawLine(QPointF(x, y_bot), QPointF(x - 4, y_bot - 7))
        p.drawLine(QPointF(x, y_bot), QPointF(x + 4, y_bot - 7))
        p.drawText(QRectF(x + 4, y_top - 4, 14, 14), Qt.AlignLeft, "P")
