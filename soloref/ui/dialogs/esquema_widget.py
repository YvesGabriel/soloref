"""Widget que desenha o 'Esquema ilustrativo' do muro de solo reforçado.

Reproduz a figura que aparece à direita em todas as abas do diálogo de
Entrada de Dados do programa original (parte reforçada vertical, talude
de topo, encosta, sobrecargas q e P). Os parâmetros vêm do `Projeto`,
então o desenho é vivo: muda conforme o usuário edita os campos.

Além do muro, quando um método já foi calculado (`mostrar_resultado`), o
widget desenha por cima a **superfície crítica** que aquele método
encontrou — reta da cunha (Rankine/Coulomb), bilinear (Dois Blocos),
círculo (Bishop) ou camadas de reforço (Geossintético) — lendo os campos
já presentes em `Resultado`/`extras`, sem repetir nenhum cálculo.
"""
from __future__ import annotations

import logging
import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QPainterPath
)
from PySide6.QtWidgets import QWidget

from ...core.methods.base import Resultado
from ...core.models import Projeto
from ..geometria_segura import cotg_segura

logger = logging.getLogger(__name__)

# Cor do overlay de resultado por sigla de método (distinta da cor do muro).
_COR_OVERLAY = {
    "Rank": QColor("#1565c0"),
    "Coul": QColor("#1565c0"),
    "DB": QColor("#6a1b9a"),
    "Bish": QColor("#2e7d32"),
    "Ref": QColor("#e65100"),
}


class EsquemaWidget(QWidget):
    """Desenho vetorial 2D do muro. Sem dependências externas (puro Qt)."""

    def __init__(self, projeto: Projeto, parent=None):
        super().__init__(parent)
        self.projeto = projeto
        self._sigla_resultado: str | None = None
        self._resultado: Resultado | None = None
        self.setMinimumSize(280, 220)
        self.setStyleSheet("background-color: #c8c8c8;")

    def atualizar(self, projeto: Projeto) -> None:
        self.projeto = projeto
        self.update()

    def mostrar_resultado(self, sigla: str, resultado: Resultado) -> None:
        """Guarda o resultado do método ativo (`sigla` = `metodo.sigla`) para
        desenhar a superfície crítica por cima do muro."""
        self._sigla_resultado = sigla
        self._resultado = resultado
        self.update()

    def limpar_resultado(self) -> None:
        """Remove o overlay de resultado — volta a mostrar só o muro."""
        self._sigla_resultado = None
        self._resultado = None
        self.update()

    # ------------------------------------------------------------------ #
    # Transformação mundo → tela, compartilhada pelo muro e pelos overlays
    # ------------------------------------------------------------------ #
    def _transformacao(self):
        """Calcula `(scale, x0, y0)`: escala (px/m) e origem em tela do pé
        do muro. Mundo em metros, origem no pé do muro, x cresce para
        dentro do maciço e y cresce para cima — a mesma convenção usada
        nas coordenadas de `extras` em `core/methods/bishop.py` e
        `dois_blocos.py`. Devolve `None` se a área de desenho for pequena
        demais para valer a pena desenhar.
        """
        g = self.projeto.geometria
        m = 30
        w = self.width() - 2 * m
        h = self.height() - 2 * m
        if w < 50 or h < 50:
            return None

        H = max(g.altura_H_m, 1.0)
        Ht = max(g.altura_topo_Ht_m, 0.0)
        B = max(g.largura_aterro_B_m, 0.5)
        total_h = H + Ht + 1.0
        total_w = B * 2.2
        scale = min(w / total_w, h / total_h)

        x0 = m + w * 0.30
        y0 = m + h * 0.85
        return scale, x0, y0

    @staticmethod
    def _w2s(x_m: float, y_m: float, scale: float, x0: float, y0: float) -> QPointF:
        """Converte um ponto do mundo (metros) em coordenadas de tela."""
        return QPointF(x0 + x_m * scale, y0 - y_m * scale)

    # ------------------------------------------------------------------ #
    def paintEvent(self, event):  # noqa: N802 (Qt API)
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self.rect(), QColor("#c8c8c8"))
            self._desenhar(p)
        except Exception:  # noqa: BLE001 — nenhum valor de entrada pode
            # derrubar a UI; o usuário continua livre para digitar
            # qualquer coisa nos campos, o desenho é que se vira.
            logger.exception("Falha ao desenhar o esquema ilustrativo")
            self._desenhar_erro(p)
        finally:
            p.end()

    def _desenhar_erro(self, p: QPainter) -> None:
        """Fallback de última linha quando `_desenhar` lança algo que nem
        `_cotg_segura` previu — mostra um aviso em vez de deixar o widget
        num estado de pintura quebrado (ou o app inteiro travando)."""
        p.setPen(QPen(QColor("#a00"), 1))
        font = QFont()
        font.setPointSize(9)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter,
                   "Não foi possível desenhar o esquema para estes valores.")

    def _desenhar(self, p: QPainter) -> None:
        transf = self._transformacao()
        if transf is None:
            return
        scale, x0, y0 = transf

        g = self.projeto.geometria
        s = self.projeto.sobrecarga

        beta = math.radians(g.inclinacao_face_beta_g)
        beta_e = math.radians(g.inclinacao_encosta_beta_e_g)
        i_topo = math.radians(g.inclinacao_topo_i_g)

        H = g.altura_H_m
        Ht = g.altura_topo_Ht_m
        B = g.largura_aterro_B_m

        # Pontos-chave em coordenadas de mundo (metros, origem no pé do muro).
        # x_face/x_enc dividem por tan(β)/tan(βe) — ambos os campos aceitam
        # 0° na entrada de dados (parede/encosta "deitada", degenerada, mas
        # o usuário pode digitar), o que faria tan()=0 e estouraria uma
        # ZeroDivisionError aqui sem a proteção de `cotg_segura`.
        avisos_desenho: list[str] = []
        x_face, saturou = cotg_segura(H, beta)
        if saturou:
            avisos_desenho.append(f"β={g.inclinacao_face_beta_g:g}°")
        x_topo = B * math.tan(i_topo)
        x_enc, saturou = cotg_segura(Ht, beta_e)
        if saturou:
            avisos_desenho.append(f"βe={g.inclinacao_encosta_beta_e_g:g}°")

        P0 = self._w2s(0.0, 0.0, *transf)
        P1 = self._w2s(x_face, H, *transf)
        P2 = self._w2s(x_face + B, H + x_topo, *transf)
        P3 = self._w2s(x_face + B + x_enc, H + x_topo + Ht, *transf)

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

        # Superfície crítica do método calculado (cunha/círculo/camadas);
        # se não houver resultado (ou faltar algum dado), cai na linha
        # tracejada genérica de sempre — fallback seguro, nunca quebra.
        if not self._desenhar_overlay_resultado(p, transf, H):
            pen_dash = QPen(QColor("#0066aa"), 1, Qt.DashLine)
            p.setPen(pen_dash)
            p.drawLine(P0, P2)

        # ---------- sobrecargas no topo ---------- #
        self._desenhar_setas_uniformes(p, P1, P2)
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

        if avisos_desenho:
            self._desenhar_aviso_geometria(p, avisos_desenho)

    def _desenhar_aviso_geometria(self, p: QPainter, avisos: list[str]) -> None:
        """Banner discreto quando algum ângulo teve que ser saturado para
        não quebrar o desenho (ver `_cotg_segura`) — o valor digitado
        continua exatamente o que o usuário pôs, só o desenho é aproximado.
        """
        texto = "⚠ Geometria degenerada (" + ", ".join(avisos) + ") — desenho aproximado"
        rect = QRectF(6, 6, max(self.width() - 12, 0), 18)
        p.fillRect(rect, QColor(255, 246, 218, 235))
        p.setPen(QPen(QColor("#b08600"), 1))
        p.drawRect(rect)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QPen(QColor("#8a6d00"), 1))
        p.drawText(rect, Qt.AlignCenter, texto)

    # ------------------------------------------------------------------ #
    # Overlay da superfície crítica (por método)
    # ------------------------------------------------------------------ #
    def _desenhar_overlay_resultado(self, p: QPainter, transf, H: float) -> bool:
        """Desenha a superfície crítica do método ativo. Devolve `True` se
        desenhou algo (para o chamador não cair no traço genérico) ou
        `False` se não houver resultado ainda ou faltar algum dado —
        nunca propaga exceção (é só desenho ilustrativo).
        """
        sigla = self._sigla_resultado
        resultado = self._resultado
        if not sigla or resultado is None:
            return False
        try:
            if sigla in ("Rank", "Coul"):
                return self._overlay_cunha_reta(p, transf, H, sigla, resultado)
            if sigla == "DB":
                return self._overlay_cunha_bilinear(p, transf, H, resultado)
            if sigla == "Bish":
                return self._overlay_circulo(p, transf, resultado)
            if sigla == "Ref":
                return self._overlay_camadas(p, transf, H, resultado)
        except Exception:  # noqa: BLE001 — desenho não pode derrubar a UI
            logger.exception("Falha ao desenhar overlay de resultado (%s)", sigla)
        return False

    def _overlay_cunha_reta(self, p: QPainter, transf, H: float, sigla: str,
                             resultado: Resultado) -> bool:
        """Rankine/Coulomb: reta da cunha a partir do pé do muro, na
        inclinação `inclinacao_cunha_g` (da horizontal)."""
        ang_g = resultado.inclinacao_cunha_g
        if not ang_g or not (0.0 < ang_g < 90.0):
            return False
        x_topo = H / math.tan(math.radians(ang_g))
        p0 = self._w2s(0.0, 0.0, *transf)
        p1 = self._w2s(x_topo, H, *transf)
        cor = _COR_OVERLAY[sigla]
        p.setPen(QPen(cor, 2))
        p.drawLine(p0, p1)
        self._rotulo(p, p1, f"cunha {ang_g:.1f}°", cor)
        return True

    def _overlay_cunha_bilinear(self, p: QPainter, transf, H: float,
                                 resultado: Resultado) -> bool:
        """Dois Blocos: pé → ponto de inflexão (xp_m, inflexao_m) → topo,
        com as inclinações `cunha1_g` e `cunha2_g`."""
        e = resultado.extras
        cunha1_g = e.get("cunha1_g")
        cunha2_g = e.get("cunha2_g")
        xp = e.get("xp_m")
        yn = e.get("inflexao_m")
        if None in (cunha1_g, cunha2_g, xp, yn) or not (0.0 < cunha2_g < 90.0):
            return False
        run2 = (H - yn) / math.tan(math.radians(cunha2_g))
        p0 = self._w2s(0.0, 0.0, *transf)
        pn = self._w2s(xp, yn, *transf)
        pc = self._w2s(xp + run2, H, *transf)
        cor = _COR_OVERLAY["DB"]
        p.setPen(QPen(cor, 2))
        p.drawLine(p0, pn)
        p.drawLine(pn, pc)
        self._rotulo(p, pn, f"{cunha1_g:.0f}° / {cunha2_g:.0f}°", cor)
        return True

    def _overlay_circulo(self, p: QPainter, transf, resultado: Resultado) -> bool:
        """Bishop: círculo crítico (centro `xc_m, yc_m`, raio `R_m`),
        construído para passar pelo pé do talude."""
        e = resultado.extras
        xc, yc, R = e.get("xc_m"), e.get("yc_m"), e.get("R_m")
        if xc is None or yc is None or not R or R <= 0:
            return False
        scale = transf[0]
        centro = self._w2s(xc, yc, *transf)
        r_px = R * scale
        cor = _COR_OVERLAY["Bish"]
        p.setPen(QPen(cor, 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(centro, r_px, r_px)
        fs = resultado.fator_seguranca
        rotulo_txt = f"FS = {fs:.3f}" if fs else "FS = —"
        self._rotulo(p, QPointF(centro.x() - 20, centro.y() - r_px), rotulo_txt, cor)
        return True

    def _overlay_camadas(self, p: QPainter, transf, H: float,
                          resultado: Resultado) -> bool:
        """Geossintético: uma linha horizontal por camada, na profundidade
        `z_m` (medida do topo), com comprimento `L_m` a partir da face."""
        e = resultado.extras
        camadas = e.get("camadas")
        n_camadas = e.get("n_camadas")
        if not camadas or not n_camadas:
            return False
        cor = _COR_OVERLAY["Ref"]
        p.setPen(QPen(cor, 1.5))
        limite = max(self.projeto.geometria.largura_aterro_B_m, 1.0) * 1.5
        topo = None
        for camada in camadas:
            z = camada.get("z_m")
            if z is None:
                continue
            comprimento = min(camada.get("L_m") or 0.0, limite)
            y_m = H - z
            p0 = self._w2s(0.0, y_m, *transf)
            p1 = self._w2s(comprimento, y_m, *transf)
            p.drawLine(p0, p1)
            if topo is None or y_m > topo:
                topo = y_m
        rotulo_pt = self._w2s(0.0, topo if topo is not None else H, *transf)
        self._rotulo(p, rotulo_pt, f"{int(n_camadas)} camadas", cor)
        return True

    @staticmethod
    def _rotulo(p: QPainter, ponto: QPointF, texto: str, cor: QColor) -> None:
        """Legenda curta perto de um ponto do overlay."""
        p.setPen(QPen(cor, 1))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(ponto.x() + 4, ponto.y() - 14, 130, 16),
                   Qt.AlignLeft, texto)

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
