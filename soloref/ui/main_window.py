"""Janela principal do SoloRef (reimplementação).

Replica a estrutura do programa original: MDI com menus
(Sistema, Dimensionamento, Relatórios, Janelas, Ajuda) e toolbar com
os botões ED, Coul, Rank, DB, Ref, Ext, Resu, Rela.
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QMdiArea, QMdiSubWindow, QMessageBox, QFileDialog, QToolBar,
)

from ..core.methods import (
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
    MetodoGeossintetico, Resultado,
)
from ..core.models import Projeto
from ..core.persistence import salvar, carregar
from .dialogs.entrada_dados import EntradaDadosDialog
from .dialogs.metodo_info import MetodoInfoDialog
from .dialogs.quadro_resumo import QuadroResumoWidget

logger = logging.getLogger(__name__)

# aba do MetodoInfoDialog (0..4) -> classe de método correspondente.
_METODOS_POR_ABA = [
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop, MetodoGeossintetico,
]

# classe de método -> chaves de solicitação/cunha no dict `resultados` do
# QuadroResumoWidget. Bishop e Geossintético ainda não têm linha própria no
# quadro (ver PLANO_IMPLEMENTACAO.md §6), então ficam de fora deste mapa.
_CHAVES_RESUMO = {
    MetodoCoulomb: ("coulomb_solicit", "coulomb_cunha"),
    MetodoRankine: ("rankine_solicit", "rankine_cunha"),
    MetodoDoisBlocos: ("db_solicit", "db_cunha1"),
}


def _resultado_calculado(resultado: Resultado) -> bool:
    """Distingue um `Resultado` de verdade de um placeholder vazio.

    Heurística temporária: um método ainda não implementado devolve
    `Resultado(metodo=...)` com solicitação/cunha zeradas e `extras` vazio.
    Vale até todos os métodos estarem implementados (aí sempre é True).
    """
    return bool(resultado.extras) or resultado.solicitacao_kN_m != 0.0 or resultado.inclinacao_cunha_g != 0.0


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "SoloRef - Dimensionamento de Estruturas de Solo Reforçado"
        )
        self.resize(1280, 720)

        self.projeto = Projeto()
        self.caminho_arquivo: str | None = None

        self.mdi = QMdiArea()
        self.mdi.setViewMode(QMdiArea.SubWindowView)
        self.setCentralWidget(self.mdi)

        self._resumo_widget: QuadroResumoWidget | None = None
        self._resumo_sub: QMdiSubWindow | None = None

        self._montar_actions()
        self._montar_menus()
        self._montar_toolbar()
        self.statusBar().showMessage("Situação ainda indeterminada")

    # ================================================================== #
    # Actions
    # ================================================================== #
    def _montar_actions(self):
        self.act_novo = QAction("&Novo", self, shortcut=QKeySequence.New)
        self.act_novo.triggered.connect(self._novo)

        self.act_abrir = QAction("&Abrir...", self, shortcut=QKeySequence.Open)
        self.act_abrir.triggered.connect(self._abrir)

        self.act_salvar = QAction("&Salvar", self, shortcut=QKeySequence.Save)
        self.act_salvar.triggered.connect(self._salvar)

        self.act_salvar_como = QAction("Salvar &como...", self)
        self.act_salvar_como.triggered.connect(lambda: self._salvar(como=True))

        self.act_sair = QAction("Sai&r", self, shortcut=QKeySequence.Quit)
        self.act_sair.triggered.connect(self.close)

        self.act_ed = QAction("&Entrada de dados", self, shortcut="Ctrl+E")
        self.act_ed.triggered.connect(self._entrada_dados)

        self.act_coul = QAction("Método de &Coulomb", self)
        self.act_coul.triggered.connect(lambda: self._mostrar_metodo(0))

        self.act_rank = QAction("Método de &Rankine", self)
        self.act_rank.triggered.connect(lambda: self._mostrar_metodo(1))

        self.act_db = QAction("Método dos &Dois Blocos", self)
        self.act_db.triggered.connect(lambda: self._mostrar_metodo(2))

        self.act_bishop = QAction("Método de &Bishop (novo)", self)
        self.act_bishop.triggered.connect(lambda: self._mostrar_metodo(3))

        self.act_ref = QAction("Refor&ço (geossintético)", self)
        self.act_ref.triggered.connect(lambda: self._mostrar_metodo(4))

        self.act_ext = QAction("Estabilidade e&xterna", self)
        self.act_ext.triggered.connect(self._nao_impl)

        self.act_resu = QAction("Quadro Res&umo", self)
        self.act_resu.triggered.connect(self._abrir_resumo)

        self.act_rela = QAction("&Relatórios", self)
        self.act_rela.triggered.connect(self._nao_impl)

        self.act_sobre = QAction("&Sobre...", self)
        self.act_sobre.triggered.connect(self._sobre)

    # ================================================================== #
    # Menus
    # ================================================================== #
    def _montar_menus(self):
        mb = self.menuBar()

        m_sistema = mb.addMenu("&Sistema")
        m_sistema.addAction(self.act_novo)
        m_sistema.addAction(self.act_abrir)
        m_sistema.addAction(self.act_salvar)
        m_sistema.addAction(self.act_salvar_como)
        m_sistema.addSeparator()
        m_sistema.addAction(self.act_sair)

        m_dim = mb.addMenu("&Dimensionamento")
        m_dim.addAction(self.act_ed)
        m_dim.addSeparator()
        m_dim.addAction(self.act_coul)
        m_dim.addAction(self.act_rank)
        m_dim.addAction(self.act_db)
        m_dim.addAction(self.act_bishop)
        m_dim.addAction(self.act_ref)
        m_dim.addSeparator()
        m_dim.addAction(self.act_ext)
        m_dim.addAction(self.act_resu)

        m_rel = mb.addMenu("&Relatórios")
        m_rel.addAction(self.act_rela)

        m_janelas = mb.addMenu("&Janelas")
        m_janelas.addAction("Organizar em cascata",
                             self.mdi.cascadeSubWindows)
        m_janelas.addAction("Organizar lado a lado",
                             self.mdi.tileSubWindows)
        m_janelas.addAction("Fechar tudo", self.mdi.closeAllSubWindows)

        m_ajuda = mb.addMenu("&Ajuda")
        m_ajuda.addAction(self.act_sobre)

    # ================================================================== #
    # Toolbar
    # ================================================================== #
    def _montar_toolbar(self):
        tb = QToolBar("Principal")
        tb.setMovable(False)
        self.addToolBar(tb)

        def add(nome, action):
            # Cria uma action wrapper só p/ ter o texto curto no toolbar
            a = QAction(nome, self)
            a.triggered.connect(action.trigger)
            tb.addAction(a)
            return a

        add("ED", self.act_ed)
        add("Coul", self.act_coul)
        add("Rank", self.act_rank)
        add("DB", self.act_db)
        add("Bish", self.act_bishop)
        add("Ref", self.act_ref)
        add("Ext", self.act_ext)
        add("Resu", self.act_resu)
        add("Rela", self.act_rela)

    # ================================================================== #
    # Ações
    # ================================================================== #
    def _novo(self):
        self.projeto = Projeto()
        self.caminho_arquivo = None
        self.mdi.closeAllSubWindows()
        self._resumo_widget = None
        self.statusBar().showMessage("Novo projeto")

    def _abrir(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir projeto", "", "Projeto SoloRef (*.json);;Todos (*)"
        )
        if caminho:
            try:
                self.projeto = carregar(caminho)
                self.caminho_arquivo = caminho
                self.statusBar().showMessage(f"Carregado: {caminho}")
            except Exception as e:  # pragma: no cover
                QMessageBox.critical(self, "Erro ao abrir", str(e))

    def _salvar(self, como: bool = False):
        caminho = self.caminho_arquivo
        if como or not caminho:
            caminho, _ = QFileDialog.getSaveFileName(
                self, "Salvar projeto", "",
                "Projeto SoloRef (*.json)"
            )
            if not caminho:
                return
        try:
            salvar(self.projeto, caminho)
            self.caminho_arquivo = caminho
            self.statusBar().showMessage(f"Salvo: {caminho}")
        except Exception as e:  # pragma: no cover
            QMessageBox.critical(self, "Erro ao salvar", str(e))

    def _entrada_dados(self):
        dlg = EntradaDadosDialog(self.projeto, self)
        if dlg.exec():  # QDialog.exec() -> 1 (Accepted) / 0 (Rejected)
            self.projeto = dlg.resultado()
            self.statusBar().showMessage(
                "Dados atualizados — pronto para dimensionar"
            )

    def _mostrar_metodo(self, aba: int):
        dlg = MetodoInfoDialog(self, aba_inicial=aba)
        if not dlg.exec():  # QDialog.exec() -> 1 (Accepted) / 0 (Rejected)
            return

        metodo_cls = _METODOS_POR_ABA[aba]
        metodo = metodo_cls()
        try:
            resultado = metodo.calcular(self.projeto)
        except Exception as e:
            logger.exception("Erro ao calcular %s", metodo.nome)
            self.statusBar().showMessage(f"Erro ao calcular {metodo.nome}: {e}")
            return

        logger.info(
            "Método executado: %s | entrada=%s | resultado=%s",
            metodo.nome, asdict(self.projeto), asdict(resultado),
        )

        resultados: dict = {}
        chaves = _CHAVES_RESUMO.get(metodo_cls)
        if chaves and _resultado_calculado(resultado):
            chave_solicit, chave_cunha = chaves
            resultados[chave_solicit] = resultado.solicitacao_kN_m
            resultados[chave_cunha] = resultado.inclinacao_cunha_g

        self._abrir_resumo(trazer_pra_frente=True)
        self._resumo_widget.adicionar_situacao(self.projeto, resultados)

        if _resultado_calculado(resultado):
            self.statusBar().showMessage(
                f"{metodo.nome}: solicitação={resultado.solicitacao_kN_m:.3g} kN/m, "
                f"cunha={resultado.inclinacao_cunha_g:.3g}°"
            )
        else:
            self.statusBar().showMessage(
                f"{metodo.nome}: cálculo ainda não implementado"
            )

    def _abrir_resumo(self, trazer_pra_frente: bool = False):
        if self._resumo_widget is None:
            self._resumo_widget = QuadroResumoWidget()
            self._resumo_sub = self.mdi.addSubWindow(self._resumo_widget)
            self._resumo_sub.setWindowTitle("Quadro resumo")
            self._resumo_sub.resize(900, 500)
        self._resumo_sub.show()
        if trazer_pra_frente:
            self._resumo_sub.raise_()

    def _nao_impl(self):
        QMessageBox.information(
            self, "Não implementado",
            "Esta funcionalidade será implementada nas próximas etapas do projeto.",
        )

    def _sobre(self):
        QMessageBox.about(
            self, "Sobre o SoloRef",
            "<b>SoloRef</b> (reimplementação)<br>"
            "Dimensionamento de Estruturas de Solo Reforçado<br><br>"
            "Iniciação Científica — Yves Gabriel Queiroz de Sousa<br>"
            "Orientação: Prof. José Antonio Schiavon<br><br>"
            "Python + PySide6",
        )
