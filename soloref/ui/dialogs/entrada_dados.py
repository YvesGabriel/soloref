"""Diálogo 'Entrada de dados' com as 7 abas do programa original.

Abas (na mesma ordem da tela original):
    Solo de aterro | Solo de encosta | Solo de fundação
    Geometria da estrutura | Face da estrutura
    Sobrecarga | Identificação do projeto

À direita fica o Esquema ilustrativo, que se atualiza ao vivo conforme
o usuário edita os valores.
"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QFormLayout, QLineEdit, QDoubleSpinBox,
    QCheckBox, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox,
    QSpinBox, QFrame,
)

from ...core.models import (
    Projeto, Identificacao, Geometria, FaceEstrutura, Solo, Sobrecarga, Reforco,
)
from .esquema_widget import EsquemaWidget


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _spin(val: float, decimals: int = 2, maximum: float = 1e6,
          minimum: float = -1e6) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setDecimals(decimals)
    s.setRange(minimum, maximum)
    s.setValue(val)
    s.setFixedWidth(90)
    return s


# --------------------------------------------------------------------------- #
# Abas individuais
# --------------------------------------------------------------------------- #
class _AbaIdentificacao(QWidget):
    def __init__(self, ident: Identificacao):
        super().__init__()
        self.identificacao = QLineEdit(ident.identificacao)
        self.empresa = QLineEdit(ident.empresa)
        self.numero = QSpinBox()
        self.numero.setRange(1, 9999)
        self.numero.setValue(ident.numero_dimensionamento)
        self.numero.setEnabled(False)
        self.numero.setFixedWidth(90)

        form = QFormLayout(self)
        form.addRow("Identificação do projeto", self.identificacao)
        form.addRow("Empresa", self.empresa)
        form.addRow("Número do dimensionamento", self.numero)

    def valores(self) -> Identificacao:
        return Identificacao(
            identificacao=self.identificacao.text(),
            empresa=self.empresa.text(),
            numero_dimensionamento=self.numero.value(),
        )


class _AbaGeometria(QWidget):
    def __init__(self, g: Geometria):
        super().__init__()
        self.altura_H = _spin(g.altura_H_m)
        self.inclinacao_beta = _spin(g.inclinacao_face_beta_g, minimum=0, maximum=90)
        self.largura_B = _spin(g.largura_aterro_B_m)
        self.inclinacao_betae = _spin(g.inclinacao_encosta_beta_e_g, minimum=0, maximum=90)
        self.inclinacao_i = _spin(g.inclinacao_topo_i_g, minimum=-45, maximum=45)
        self.altura_Ht = _spin(g.altura_topo_Ht_m, minimum=0)

        form = QFormLayout(self)
        form.addRow("Altura da parte reforçada, H (m)", self.altura_H)
        form.addRow("Inclinação da face, β (graus)", self.inclinacao_beta)
        # Em vermelho como no original (indica campo crítico)
        lab_B = QLabel("Largura do aterro, B (m)")
        lab_B.setStyleSheet("color: #b00;")
        form.addRow(lab_B, self.largura_B)
        form.addRow("Inclinação da encosta, βe (graus)", self.inclinacao_betae)
        form.addRow("Inclinação do talude de topo, i (graus)", self.inclinacao_i)
        form.addRow("Altura do talude de topo, Ht (m)", self.altura_Ht)

    def valores(self) -> Geometria:
        return Geometria(
            altura_H_m=self.altura_H.value(),
            inclinacao_face_beta_g=self.inclinacao_beta.value(),
            largura_aterro_B_m=self.largura_B.value(),
            inclinacao_encosta_beta_e_g=self.inclinacao_betae.value(),
            inclinacao_topo_i_g=self.inclinacao_i.value(),
            altura_topo_Ht_m=self.altura_Ht.value(),
        )


class _AbaFace(QWidget):
    def __init__(self, f: FaceEstrutura):
        super().__init__()
        self.considera = QCheckBox("O projeto considera blocos de face")
        self.considera.setChecked(f.considera_blocos)

        self.altura = _spin(f.altura_blocos_cm or 0)
        self.largura = _spin(f.largura_blocos_cm or 0)
        self.recuo = _spin(f.recuo_blocos_cm or 0)

        grp = QGroupBox()
        form = QFormLayout(grp)
        form.addRow("Altura dos blocos (cm)", self.altura)
        form.addRow("Largura dos blocos (cm)", self.largura)
        form.addRow("Recuo entre blocos (cm)", self.recuo)

        obs = QLabel(
            "Obs. Os blocos de face não são considerados elementos de contenção."
        )
        obs.setStyleSheet("color: #b00;")
        obs.setWordWrap(True)

        lay = QVBoxLayout(self)
        lay.addWidget(self.considera)
        lay.addWidget(grp)
        lay.addWidget(obs)
        lay.addStretch()

        self.considera.toggled.connect(grp.setEnabled)
        grp.setEnabled(f.considera_blocos)

    def valores(self) -> FaceEstrutura:
        on = self.considera.isChecked()
        return FaceEstrutura(
            considera_blocos=on,
            altura_blocos_cm=self.altura.value() if on else None,
            largura_blocos_cm=self.largura.value() if on else None,
            recuo_blocos_cm=self.recuo.value() if on else None,
        )


class _AbaSolo(QWidget):
    def __init__(self, solo: Solo, *, com_atrito_blocos: bool,
                 observacoes: str | None = None):
        super().__init__()
        self.peso = _spin(solo.peso_especifico_kN_m3)
        self.coesao = _spin(solo.coesao_kN_m2, minimum=0)
        self.atrito = _spin(solo.angulo_atrito_g, minimum=0, maximum=60)
        self.atrito_blocos = None

        form = QFormLayout(self)
        form.addRow("Peso específico aparente total (kN/m³)", self.peso)
        form.addRow("Coesão (kN/m²)", self.coesao)
        form.addRow("Ângulo de atrito (graus)", self.atrito)
        if com_atrito_blocos:
            v = solo.angulo_atrito_blocos_g if solo.angulo_atrito_blocos_g is not None else 30.0
            self.atrito_blocos = _spin(v, minimum=0, maximum=60)
            form.addRow("Ângulo de atrito entre blocos (graus)",
                        self.atrito_blocos)

        if observacoes:
            obs = QLabel(observacoes)
            obs.setStyleSheet("color: #b00;")
            obs.setWordWrap(True)
            form.addRow(obs)

        disc = QLabel("-> Discussão sobre parâmetros do solo")
        disc.setStyleSheet("color: #b00; text-decoration: underline;")
        form.addRow(disc)

    def valores(self) -> Solo:
        return Solo(
            peso_especifico_kN_m3=self.peso.value(),
            coesao_kN_m2=self.coesao.value(),
            angulo_atrito_g=self.atrito.value(),
            angulo_atrito_blocos_g=(self.atrito_blocos.value()
                                     if self.atrito_blocos else None),
        )


class _AbaSobrecarga(QWidget):
    def __init__(self, s: Sobrecarga):
        super().__init__()
        self.uniforme = _spin(s.uniforme_q_kN_m2, minimum=0)
        self.trem = _spin(s.trem_tipo_P_kN_m, minimum=0)
        self.posicao = _spin(s.posicao_xo_m, minimum=0)
        self.eixo = _spin(s.eixo_e_m, minimum=0)

        lay = QFormLayout(self)
        lab_q = QLabel("Sobrecarga uniforme, q (kN/m²)")
        lab_q.setStyleSheet("color: #b00;")
        lay.addRow(lab_q, self.uniforme)

        grp = QGroupBox("Trem-tipo (sobrecarga linear)")
        sub = QFormLayout(grp)
        sub.addRow("Valor da carga, P (kN/m)", self.trem)
        sub.addRow("Posição, xo (m)", self.posicao)
        sub.addRow("Eixo, e (m)", self.eixo)
        lay.addRow(grp)

    def valores(self) -> Sobrecarga:
        return Sobrecarga(
            uniforme_q_kN_m2=self.uniforme.value(),
            trem_tipo_P_kN_m=self.trem.value(),
            posicao_xo_m=self.posicao.value(),
            eixo_e_m=self.eixo.value(),
        )


class _AbaReforco(QWidget):
    def __init__(self, r: Reforco):
        super().__init__()
        self.tult = _spin(r.tult_kN_m, minimum=0)
        self.rf_fluencia = _spin(r.rf_fluencia, minimum=1)
        self.rf_dano = _spin(r.rf_dano_instalacao, minimum=1)
        self.rf_degradacao = _spin(r.rf_degradacao, minimum=1)
        self.ci = _spin(r.ci_interacao, minimum=0, maximum=1)
        self.fs_alvo = _spin(r.fs_alvo, minimum=1)

        form = QFormLayout(self)
        form.addRow("Resistência à tração última, Tult (kN/m)", self.tult)
        form.addRow("Fator de redução — fluência, RFcr", self.rf_fluencia)
        form.addRow("Fator de redução — dano de instalação, RFid", self.rf_dano)
        form.addRow("Fator de redução — degradação, RFd", self.rf_degradacao)
        form.addRow("Coeficiente de interação (arrancamento), Ci", self.ci)
        form.addRow("Fator de segurança de projeto, FS", self.fs_alvo)

        obs = QLabel(
            "Obs. Valores default são ordens de grandeza típicas — ajuste "
            "conforme a ficha técnica do geossintético."
        )
        obs.setStyleSheet("color: #b00;")
        obs.setWordWrap(True)
        form.addRow(obs)

    def valores(self) -> Reforco:
        return Reforco(
            tult_kN_m=self.tult.value(),
            rf_fluencia=self.rf_fluencia.value(),
            rf_dano_instalacao=self.rf_dano.value(),
            rf_degradacao=self.rf_degradacao.value(),
            ci_interacao=self.ci.value(),
            fs_alvo=self.fs_alvo.value(),
        )


# --------------------------------------------------------------------------- #
# Diálogo principal
# --------------------------------------------------------------------------- #
class EntradaDadosDialog(QDialog):
    def __init__(self, projeto: Projeto, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entrada de dados")
        self.resize(720, 380)
        self._projeto_original = projeto
        self.projeto = replace(projeto)  # cópia rasa p/ cancelar

        # ---- montar abas ---- #
        self.aba_aterro = _AbaSolo(self.projeto.solo_aterro, com_atrito_blocos=True)
        self.aba_encosta = _AbaSolo(
            self.projeto.solo_encosta, com_atrito_blocos=False,
            observacoes="Obs. Os parâmetros do solo de encosta não são "
                        "necessários no dimensionamento.",
        )
        self.aba_fundacao = _AbaSolo(self.projeto.solo_fundacao,
                                      com_atrito_blocos=False)
        self.aba_geometria = _AbaGeometria(self.projeto.geometria)
        self.aba_face = _AbaFace(self.projeto.face)
        self.aba_sobrecarga = _AbaSobrecarga(self.projeto.sobrecarga)
        self.aba_reforco = _AbaReforco(self.projeto.reforco)
        self.aba_identif = _AbaIdentificacao(self.projeto.identificacao)

        tabs = QTabWidget()
        tabs.addTab(self.aba_aterro, "Solo de aterro")
        tabs.addTab(self.aba_encosta, "Solo de encosta")
        tabs.addTab(self.aba_fundacao, "Solo de fundação")
        tabs.addTab(self.aba_geometria, "Geometria da estrutura")
        tabs.addTab(self.aba_face, "Face da estrutura")
        tabs.addTab(self.aba_sobrecarga, "Sobrecarga")
        tabs.addTab(self.aba_reforco, "Reforço (geossintético)")
        tabs.addTab(self.aba_identif, "Identificação do projeto")

        # ---- esquema ilustrativo à direita ---- #
        esquema_box = QGroupBox("Esquema ilustrativo")
        self.esquema = EsquemaWidget(self.projeto)
        box_lay = QVBoxLayout(esquema_box)
        box_lay.addWidget(self.esquema)

        # ---- botões OK / Cancelar ---- #
        ok = QPushButton("&OK")
        ok.setDefault(True)
        cancel = QPushButton("&Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(ok)
        btn_row.addWidget(cancel)

        right = QVBoxLayout()
        right.addWidget(esquema_box)
        right.addLayout(btn_row)

        # ---- status bar inferior ---- #
        self.status = QLabel("Dimensiona a estrutura.")
        self.status.setFrameShape(QFrame.StyledPanel)
        self.status.setStyleSheet("padding: 2px;")

        center = QHBoxLayout()
        center.addWidget(tabs, 1)
        center.addLayout(right)

        outer = QVBoxLayout(self)
        outer.addLayout(center)
        outer.addWidget(self.status)

        # ---- atualização ao vivo do esquema ---- #
        self._ligar_live_update()

    # ------------------------------------------------------------------ #
    def _ligar_live_update(self):
        """Cada edição de geometria/sobrecarga redesenha o esquema."""
        for spin in (self.aba_geometria.altura_H,
                     self.aba_geometria.inclinacao_beta,
                     self.aba_geometria.largura_B,
                     self.aba_geometria.inclinacao_betae,
                     self.aba_geometria.inclinacao_i,
                     self.aba_geometria.altura_Ht,
                     self.aba_sobrecarga.uniforme,
                     self.aba_sobrecarga.trem,
                     self.aba_sobrecarga.posicao):
            spin.valueChanged.connect(self._repaint_esquema)

    def _repaint_esquema(self):
        self.projeto.geometria = self.aba_geometria.valores()
        self.projeto.sobrecarga = self.aba_sobrecarga.valores()
        self.esquema.atualizar(self.projeto)

    # ------------------------------------------------------------------ #
    def resultado(self) -> Projeto:
        """Retorna o Projeto consolidado após o OK."""
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
