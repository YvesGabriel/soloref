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
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QPlainTextEdit, QFrame, QMessageBox,
)

from . import interpretacao, relevancia
from ..core.models import Projeto
from ..core.methods.base import MetodoAnalise, Resultado
from .dialogs.entrada_dados import (
    _AbaSolo, _AbaGeometria, _AbaFace, _AbaSobrecarga, _AbaReforco,
    _AbaIdentificacao,
)

# Rótulo de aba -> chave usada em `relevancia.py`, na mesma ordem em que as
# abas são montadas em `PainelDados._construir`.
_ABAS_ORDENADAS = (
    ("Geometria", relevancia.ABA_GEOMETRIA),
    ("Solo aterro", relevancia.ABA_ATERRO),
    ("Solo encosta", relevancia.ABA_ENCOSTA),
    ("Solo fundação", relevancia.ABA_FUNDACAO),
    ("Face (reservado)", relevancia.ABA_FACE),
    ("Sobrecarga", relevancia.ABA_SOBRECARGA),
    ("Reforço", relevancia.ABA_REFORCO),
    ("Identificação", relevancia.ABA_IDENTIFICACAO),
)

_AVISO_RESERVADA = "Estes campos ainda não entram em nenhum cálculo implementado."

_COR_RELEVANTE = QColor("#0b3d91")
_COR_ATENUADA = QColor("#9e9e9e")


def _marcar_reservada(widget: QWidget) -> None:
    """Insere um aviso discreto no topo de uma aba cujos campos nenhum
    método implementado hoje consome (ver `relevancia.ABAS_RESERVADAS`)."""
    aviso = QLabel(_AVISO_RESERVADA)
    aviso.setWordWrap(True)
    aviso.setStyleSheet(
        "color: #8a6d00; background: #fff6da; border: 1px solid #e0c56a;"
        " border-radius: 4px; padding: 4px; font-size: 11px;"
    )
    lay = widget.layout()
    if isinstance(lay, QFormLayout):
        lay.insertRow(0, aviso)
    else:
        lay.insertWidget(0, aviso)


# --------------------------------------------------------------------------- #
# Ajuda por aba (botão "?") — o que a aba faz e o que cada variável significa,
# indicando quais métodos usam cada parâmetro.
# --------------------------------------------------------------------------- #
_AJUDA = {
    "Geometria": (
        "Define a forma da estrutura.\n"
        "• H — altura da parte reforçada (m).\n"
        "• β — inclinação da face, medida da horizontal (90° = vertical). Nos "
        "métodos de cunha plana (Coulomb, Rankine, Dois Blocos) vale para 70°–90°; "
        "no Bishop, β é usado como o ângulo do talude.\n"
        "• B — largura da base do maciço (usada na Estabilidade externa).\n"
        "• βe — inclinação da encosta a jusante.\n"
        "• i — inclinação do talude no topo do muro.\n"
        "• Ht — altura do talude de topo.\n"
        "• Embutimento — profundidade da base na fundação (capacidade de carga)."
    ),
    "Solo de aterro": (
        "Solo do maciço reforçado (o que empurra a estrutura).\n"
        "• γ — peso específico (kN/m³).\n"
        "• c — coesão (kN/m²).\n"
        "• φ — ângulo de atrito interno (°); o parâmetro mais influente.\n"
        "• δ — atrito solo-muro; usado SÓ por Coulomb e Dois Blocos "
        "(Rankine e Bishop ignoram).\n"
        "Usado por todos os métodos de empuxo, pelo dimensionamento com "
        "geossintéticos e pelo peso do bloco na Estabilidade externa."
    ),
    "Solo de encosta": (
        "Solo retido atrás do maciço reforçado.\n"
        "Usado SÓ pela Estabilidade externa, para gerar o empuxo motor.\n"
        "• γ, c, φ — parâmetros do solo retido.\n"
        "• δ_ret — atrito solo-muro do retido: 0 é o padrão conservador; muros de "
        "solo reforçado costumam adotar δ_ret = φ.\n"
        "Os métodos internos (cunha plana e Bishop) ignoram esta aba."
    ),
    "Solo de fundação": (
        "Solo de apoio da base da estrutura.\n"
        "Usado SÓ pela Estabilidade externa:\n"
        "• φ e c — resistência ao deslizamento na base.\n"
        "• c, φ, γ — capacidade de carga da fundação (fatores de Vésic).\n"
        "Os métodos internos ignoram esta aba."
    ),
    "Face": (
        "Blocos de face (altura, largura, recuo).\n"
        "RESERVADO — estes campos ainda não entram em nenhum cálculo "
        "implementado; os blocos não são considerados elementos de contenção."
    ),
    "Sobrecarga": (
        "Cargas aplicadas no topo do aterro.\n"
        "• q — sobrecarga uniforme (kN/m²); usada por Rankine, Coulomb, Dois "
        "Blocos, geossintéticos e Estabilidade externa.\n"
        "• Trem-tipo (P, xo, e) — carga linear; reservado no cálculo atual "
        "(aparece no desenho, mas ainda não entra nas contas)."
    ),
    "Reforço": (
        "Parâmetros do geossintético — usados SÓ pelo método Reforço.\n"
        "• Tult — resistência à tração última (kN/m), da ficha do produto.\n"
        "• RFcr, RFid, RFd — fatores de redução por fluência, dano de instalação "
        "e degradação (transformam Tult na tração admissível de longo prazo).\n"
        "• Ci — coeficiente de interação solo-reforço (arrancamento).\n"
        "• FS — fator de segurança de projeto (espaçamento e ancoragem)."
    ),
    "Identificação": (
        "Identificação do projeto (nome, empresa, número do dimensionamento).\n"
        "Não afeta nenhum cálculo — é só para o relatório/registro."
    ),
}


def _adicionar_ajuda(widget: QWidget, titulo: str, texto: str) -> None:
    """Insere um botão '?' fixado no canto superior direito da aba, que abre
    um diálogo com a descrição da aba e de cada variável (indicando quais
    métodos usam cada parâmetro)."""
    btn = QPushButton("?")
    btn.setFixedWidth(28)
    btn.setToolTip("Explica a aba e o significado de cada campo")
    btn.clicked.connect(
        lambda: QMessageBox.information(btn, f"Ajuda — {titulo}", texto)
    )
    linha = QHBoxLayout()
    linha.addStretch()
    linha.addWidget(btn)
    lay = widget.layout()
    if isinstance(lay, QFormLayout):
        lay.insertRow(0, linha)
    else:
        lay.insertLayout(0, linha)


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
            projeto.solo_encosta, com_atrito_blocos=True,
            rotulo_atrito_blocos="Atrito solo-muro do retido, δ_ret (graus)",
            default_atrito_blocos=0.0,
            observacoes="Obs. Descreve o solo retido atrás do maciço "
                        "reforçado — usado na Estabilidade externa para o "
                        "empuxo motor (δ_ret=0 é o padrão conservador).",
        )
        self.aba_fundacao = _AbaSolo(projeto.solo_fundacao, com_atrito_blocos=False)
        self.aba_face = _AbaFace(projeto.face)
        self.aba_sobrecarga = _AbaSobrecarga(projeto.sobrecarga)
        self.aba_reforco = _AbaReforco(projeto.reforco)
        self.aba_identif = _AbaIdentificacao(projeto.identificacao)

        self._abas_widgets = (
            self.aba_geometria, self.aba_aterro, self.aba_encosta,
            self.aba_fundacao, self.aba_face, self.aba_sobrecarga,
            self.aba_reforco, self.aba_identif,
        )
        for widget, (rotulo, _chave) in zip(self._abas_widgets, _ABAS_ORDENADAS):
            self.tabs.addTab(widget, rotulo)

        _marcar_reservada(self.aba_face)

        # Botão "?" de ajuda no topo de cada aba (ver _AJUDA).
        for w, tit in (
            (self.aba_geometria, "Geometria"),
            (self.aba_aterro, "Solo de aterro"),
            (self.aba_encosta, "Solo de encosta"),
            (self.aba_fundacao, "Solo de fundação"),
            (self.aba_face, "Face"),
            (self.aba_sobrecarga, "Sobrecarga"),
            (self.aba_reforco, "Reforço"),
            (self.aba_identif, "Identificação"),
        ):
            _adicionar_ajuda(w, tit, _AJUDA[tit])

        self._ligar_live_update()
        self.destacar_metodo(None)

    def _ligar_live_update(self) -> None:
        """Qualquer edição, em qualquer aba, sinaliza `dadosAlterados`.

        O sinal serve dois propósitos: redesenhar o esquema ao vivo
        (só reage de fato a geometria/sobrecarga, que afetam o desenho) e
        marcar o projeto como "alterações não salvas" em `MainWindow`
        (esse precisa saber de QUALQUER campo — φ, Tult, identificação,
        etc. — não só dos que mudam o desenho). Por isso conecta tudo.
        """
        spins = [
            self.aba_geometria.altura_H,
            self.aba_geometria.inclinacao_beta,
            self.aba_geometria.largura_B,
            self.aba_geometria.inclinacao_betae,
            self.aba_geometria.inclinacao_i,
            self.aba_geometria.altura_Ht,
            self.aba_sobrecarga.uniforme,
            self.aba_sobrecarga.trem,
            self.aba_sobrecarga.posicao,
            self.aba_sobrecarga.eixo,
            self.aba_reforco.tult,
            self.aba_reforco.rf_fluencia,
            self.aba_reforco.rf_dano,
            self.aba_reforco.rf_degradacao,
            self.aba_reforco.ci,
            self.aba_reforco.fs_alvo,
            self.aba_face.altura,
            self.aba_face.largura,
            self.aba_face.recuo,
        ]
        for aba_solo in (self.aba_aterro, self.aba_encosta, self.aba_fundacao):
            spins.extend([aba_solo.peso, aba_solo.coesao, aba_solo.atrito])
            if aba_solo.atrito_blocos is not None:
                spins.append(aba_solo.atrito_blocos)
        for spin in spins:
            spin.valueChanged.connect(self.dadosAlterados)

        self.aba_face.considera.toggled.connect(self.dadosAlterados)
        self.aba_identif.identificacao.textChanged.connect(self.dadosAlterados)
        self.aba_identif.empresa.textChanged.connect(self.dadosAlterados)

    # ------------------------------------------------------------------ #
    def destacar_metodo(self, sigla: str | None) -> None:
        """Realça as abas que o método ativo (`sigla` = `metodo.sigla`)
        consome e atenua as demais — ver `ui/relevancia.py`. `sigla=None`
        (nenhum método ativo ainda) limpa o destaque. Abas reservadas
        (`relevancia.ABAS_RESERVADAS`) nunca são relevantes para nenhum
        método, então ficam sempre atenuadas.
        """
        relevantes = set(relevancia.abas_relevantes(sigla)) if sigla else set()
        tab_bar = self.tabs.tabBar()
        for idx, (_rotulo, chave) in enumerate(_ABAS_ORDENADAS):
            if sigla is None:
                tab_bar.setTabTextColor(idx, QColor())
                tab_bar.setTabToolTip(idx, "")
            elif chave in relevantes:
                tab_bar.setTabTextColor(idx, _COR_RELEVANTE)
                campos = relevancia.campos_relevantes(sigla, chave)
                tab_bar.setTabToolTip(idx, f"Usa: {', '.join(campos)}" if campos else "")
            else:
                tab_bar.setTabTextColor(idx, _COR_ATENUADA)
                tab_bar.setTabToolTip(idx, "")

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
_COR_SELO_OK = "#2e7d32"
_COR_SELO_RUIM = "#c62828"


class PainelResultados(QWidget):
    """Mostra o resultado do método ativo + hipóteses; botões de ação.

    Escolha de design — redundância Calcular × Registrar: trocar de
    método na navbar já recalcula sozinho (`MainWindow._selecionar_metodo`),
    o que em algum momento tornou o botão "Calcular" parecido com um
    "calcular pela primeira vez" redundante. Mas ele não é: editar um
    campo (φ, γ, Tult, ...) SEM trocar de método não recalcula nada —
    `MainWindow._dados_alterados` só redesenha o esquema genérico
    (recalcular a cada tecla seria caro para Dois Blocos/Bishop, que
    otimizam). Optamos pela opção (b): manter o botão, com o papel restrito
    a isso — "atualize o método ativo com os dados que acabei de editar" —
    e por isso ele foi renomeado para "Recalcular". O sinal
    `calcularSolicitado` (e sua conexão em `MainWindow`) não mudou, só o
    rótulo/tooltip do botão.
    """

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

        # Banner de avisos de aplicabilidade (metodo.avisos(projeto), Tarefa 1);
        # escondido quando o método ativo não tem nenhum aviso.
        self.aviso_banner = QLabel()
        self.aviso_banner.setWordWrap(True)
        self.aviso_banner.setStyleSheet(
            "background: #fff6da; color: #8a6d00; border: 1px solid #e0c56a;"
            " border-radius: 4px; padding: 6px; font-size: 11px;"
        )
        self.aviso_banner.setVisible(False)
        lay.addWidget(self.aviso_banner)

        self._grade_host = QWidget()
        self._grade = QGridLayout(self._grade_host)
        self._grade.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._grade_host)

        btns = QHBoxLayout()
        self.btn_calcular = QPushButton("Recalcular")
        self.btn_calcular.setToolTip(
            "Atualiza o resultado do método ativo com os dados atuais — "
            "útil depois de editar um campo sem trocar de método (trocar "
            "de método já recalcula sozinho)."
        )
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
    def mostrar(self, metodo: MetodoAnalise, resultado: Resultado,
                projeto: Projeto, referencia: Resultado | None = None) -> None:
        """Mostra o resultado de `metodo` para `projeto`. `referencia` é o
        `Resultado` de Rankine para o mesmo projeto (métodos de empuxo,
        comparação percentual) — `None` quando não aplicável/disponível.
        """
        self.titulo.setText(f"Resultado — {metodo.nome}")

        avisos = metodo.avisos(projeto)
        if avisos:
            self.aviso_banner.setText("\n".join(f"⚠ {a}" for a in avisos))
            self.aviso_banner.setVisible(True)
        else:
            self.aviso_banner.clear()
            self.aviso_banner.setVisible(False)

        # limpar grade — setParent(None) some com o cartão antigo na hora;
        # deleteLater() sozinho só agenda a destruição e deixava fantasmas
        # do cartão anterior visíveis por trás dos novos por um instante.
        while self._grade.count():
            item = self._grade.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        # recriar cartões (rótulo/valor/selo já julgados em interpretacao.py)
        cartoes = interpretacao.cartoes_resultado(
            metodo.sigla, resultado, projeto, referencia
        )
        row, col = 0, 0
        for cartao in cartoes:
            # "Comparação com Rankine" é uma frase, não um número curto —
            # ocupa a linha inteira em vez de dividir com o cartão vizinho.
            largura_total = cartao.rotulo == "Comparação com Rankine"
            card = QWidget()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            lab = QLabel(cartao.rotulo)
            lab.setStyleSheet("color: #666; font-size: 11px;")
            val = QLabel(cartao.valor)
            val.setWordWrap(True)
            val.setStyleSheet("font-size: 16px; font-weight: bold;")
            cl.addWidget(lab)
            cl.addWidget(val)
            if cartao.selo_texto:
                cor = _COR_SELO_OK if cartao.selo_ok else _COR_SELO_RUIM
                selo = QLabel(cartao.selo_texto)
                selo.setAlignment(Qt.AlignCenter)
                selo.setStyleSheet(
                    f"background: {cor}; color: white; font-size: 10px;"
                    " font-weight: bold; border-radius: 8px; padding: 2px 8px;"
                )
                cl.addWidget(selo, 0, Qt.AlignLeft)
            card.setStyleSheet(
                "background: palette(base); border: 1px solid palette(mid);"
                " border-radius: 6px;"
            )
            if largura_total:
                if col == 1:
                    row += 1
                    col = 0
                self._grade.addWidget(card, row, 0, 1, 2)
                row += 1
            else:
                self._grade.addWidget(card, row, col)
                row, col = (row + 1, 0) if col == 1 else (row, 1)

        self.hipoteses.setPlainText(
            "\n".join(f"• {h}" for h in metodo.hipoteses)
        )
