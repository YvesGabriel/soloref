"""Painéis vivos da janela única (layout de três painéis).

Reaproveitam integralmente os widgets já existentes:
    - As abas de entrada (`_Aba*`) de `dialogs/entrada_dados.py` — mesma
      validação, mesmos ranges, mesmos rótulos.
    - `EsquemaWidget` continua desenhando o muro (usado no painel central
      pela MainWindow, não aqui).

`PainelDados` substitui o antigo diálogo modal de Entrada de Dados: as
mesmas abas, agora sempre visíveis e emitindo `dadosAlterados` a cada
edição relevante. `PainelResultados` mostra o resultado do método ativo
(inclusive Bishop e Geossintéticos, que antes não apareciam em lugar
nenhum da tela).
"""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QFrame,
)

from ..core.models import Projeto
from ..core.methods.base import MetodoAnalise, Resultado
from .dialogs.entrada_dados import (
    _AbaSolo, _AbaGeometria, _AbaFace, _AbaSobrecarga, _AbaReforco,
    _AbaIdentificacao,
)


# --------------------------------------------------------------------------- #
# Painel de dados (substitui o diálogo modal, mesmas abas)
# --------------------------------------------------------------------------- #
class PainelDados(QWidget):
    """As oito abas de entrada, sempre visíveis, com atualização ao vivo."""

    dadosAlterados = Signal()

    def __init__(self, projeto: Projeto, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        # Nomes completos das abas sempre visíveis: nunca abreviar/elidir,
        # usar setas de rolagem se a largura do painel não for suficiente.
        self.tabs.setElideMode(Qt.ElideNone)
        self.tabs.setUsesScrollButtons(True)
        lay.addWidget(self.tabs)
        self._construir(projeto)

    # ------------------------------------------------------------------ #
    def _construir(self, projeto: Projeto) -> None:
        self.tabs.clear()
        self.aba_geometria = _AbaGeometria(projeto.geometria)
        self.aba_aterro = _AbaSolo(projeto.solo_aterro, com_atrito_blocos=True)
        self.aba_encosta = _AbaSolo(
            projeto.solo_encosta, com_atrito_blocos=False,
            observacoes="Obs. Os parâmetros do solo de encosta não são "
                        "necessários no dimensionamento.",
        )
        self.aba_fundacao = _AbaSolo(projeto.solo_fundacao, com_atrito_blocos=False)
        self.aba_face = _AbaFace(projeto.face)
        self.aba_sobrecarga = _AbaSobrecarga(projeto.sobrecarga)
        self.aba_reforco = _AbaReforco(projeto.reforco)
        self.aba_identif = _AbaIdentificacao(projeto.identificacao)

        for widget, rotulo in (
            (self.aba_geometria, "Geometria"),
            (self.aba_aterro, "Solo aterro"),
            (self.aba_encosta, "Solo encosta"),
            (self.aba_fundacao, "Solo fundação"),
            (self.aba_face, "Face"),
            (self.aba_sobrecarga, "Sobrecarga"),
            (self.aba_reforco, "Reforço"),
            (self.aba_identif, "Identificação"),
        ):
            self.tabs.addTab(widget, rotulo)

        self._ligar_live_update()

    def _ligar_live_update(self) -> None:
        """Edição de geometria/sobrecarga sinaliza `dadosAlterados`."""
        for spin in (
            self.aba_geometria.altura_H,
            self.aba_geometria.inclinacao_beta,
            self.aba_geometria.largura_B,
            self.aba_geometria.inclinacao_betae,
            self.aba_geometria.inclinacao_i,
            self.aba_geometria.altura_Ht,
            self.aba_sobrecarga.uniforme,
            self.aba_sobrecarga.trem,
            self.aba_sobrecarga.posicao,
        ):
            spin.valueChanged.connect(self.dadosAlterados)

    # ------------------------------------------------------------------ #
    def set_projeto(self, projeto: Projeto) -> None:
        """Recarrega todas as abas com um novo projeto (abrir / novo)."""
        self._construir(projeto)
        self.dadosAlterados.emit()

    def resultado(self) -> Projeto:
        """Projeto consolidado com os valores atuais de todas as abas."""
        return Projeto(
            identificacao=self.aba_identif.valores(),
            geometria=self.aba_geometria.valores(),
            face=self.aba_face.valores(),
            solo_aterro=self.aba_aterro.valores(),
            solo_encosta=self.aba_encosta.valores(),
            solo_fundacao=self.aba_fundacao.valores(),
            sobrecarga=self.aba_sobrecarga.valores(),
            reforco=self.aba_reforco.valores(),
        )


# --------------------------------------------------------------------------- #
# Painel de resultados (por método)
# --------------------------------------------------------------------------- #
def _cartoes(resultado: Resultado) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) a exibir, adaptados ao tipo de resultado."""
    e = resultado.extras
    if e.get("n_camadas") is not None:  # geossintético
        return [
            ("Nº de camadas", f"{int(e['n_camadas'])}"),
            ("Espaçamento Sv", f"{e.get('Sv_m', 0.0):.3f} m"),
            ("Tadm", f"{e.get('Tadm_kN_m', 0.0):.1f} kN/m"),
            ("ΣTmax", f"{e.get('Tmax_total_kN_m', 0.0):.1f} kN/m"),
        ]
    if resultado.fator_seguranca and not resultado.solicitacao_kN_m:  # Bishop
        return [
            ("Fator de segurança", f"{resultado.fator_seguranca:.3f}"),
            ("Raio crítico", f"{e.get('R_m', 0.0):.2f} m"),
            ("Centro (x, y)", f"({e.get('xc_m', 0.0):.1f}, {e.get('yc_m', 0.0):.1f})"),
        ]
    # métodos de empuxo (Rankine, Coulomb, Dois Blocos)
    cartoes = [("Empuxo Ea", f"{resultado.solicitacao_kN_m:.1f} kN/m")]
    if "Ka" in e:
        cartoes.append(("Ka", f"{e['Ka']:.3f}"))
    cartoes.append(("Inclinação da cunha", f"{resultado.inclinacao_cunha_g:.1f}°"))
    if "cunha2_g" in e:
        cartoes.append(("2ª cunha", f"{e['cunha2_g']:.1f}°"))
    return cartoes


class PainelResultados(QWidget):
    """Mostra o resultado do método ativo + hipóteses; botões de ação."""

    calcularSolicitado = Signal()
    registrarSolicitado = Signal()
    verHipoteses = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)

        self.titulo = QLabel("Resultado")
        self.titulo.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.titulo)

        self._grade_host = QWidget()
        self._grade = QGridLayout(self._grade_host)
        self._grade.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._grade_host)

        btns = QHBoxLayout()
        self.btn_calcular = QPushButton("Calcular")
        self.btn_registrar = QPushButton("Registrar no quadro")
        self.btn_hip = QPushButton("Hipóteses / figura")
        self.btn_calcular.clicked.connect(self.calcularSolicitado)
        self.btn_registrar.clicked.connect(self.registrarSolicitado)
        self.btn_hip.clicked.connect(self.verHipoteses)
        btns.addWidget(self.btn_calcular)
        btns.addWidget(self.btn_registrar)
        lay.addLayout(btns)
        lay.addWidget(self.btn_hip)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        lay.addWidget(sep)

        lay.addWidget(QLabel("Hipóteses do método:"))
        self.hipoteses = QPlainTextEdit()
        self.hipoteses.setReadOnly(True)
        lay.addWidget(self.hipoteses, 1)

    # ------------------------------------------------------------------ #
    def mostrar(self, metodo: MetodoAnalise, resultado: Resultado) -> None:
        self.titulo.setText(f"Resultado — {metodo.nome}")
        # limpar grade
        while self._grade.count():
            item = self._grade.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        # recriar cartões
        for idx, (rotulo, valor) in enumerate(_cartoes(resultado)):
            card = QWidget()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            lab = QLabel(rotulo)
            lab.setStyleSheet("color: #666; font-size: 11px;")
            val = QLabel(valor)
            val.setStyleSheet("font-size: 16px; font-weight: bold;")
            cl.addWidget(lab)
            cl.addWidget(val)
            card.setStyleSheet(
                "background: palette(base); border: 1px solid palette(mid);"
                " border-radius: 6px;"
            )
            self._grade.addWidget(card, idx // 2, idx % 2)

        self.hipoteses.setPlainText(
            "\n".join(f"• {h}" for h in metodo.hipoteses)
        )
