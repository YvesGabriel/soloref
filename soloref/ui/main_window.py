"""Janela principal do SoloRef — layout de painel único (três painéis).

Substitui a antiga metáfora MDI (sub-janelas flutuantes + diálogo modal
de entrada) por uma única janela dividida em três painéis vivos:

    ┌────────── navbar única (nomes completos) ─────────┐
    │  Dados        │      Esquema        │  Resultado  │
    │ (entrada)     │   (muro ao vivo)    │  (do método)│
    └──────────────────────────────────────────────────┘
    │            Quadro resumo (dock acoplável)         │

Toda a funcionalidade da versão MDI é preservada em uma única navbar:
menus Sistema / Dimensionamento / Relatórios / Janelas / Ajuda e uma
toolbar com Entrada de dados · os cinco métodos (como abas exclusivas,
com nome completo) · Estabilidade externa · Quadro Resumo · Relatórios;
atalhos, salvar/abrir JSON, o diálogo de hipóteses (agora acessível por
botão) e o Quadro Resumo (agora um painel acoplável em vez de
sub-janela MDI).
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, QToolBar, QWidget,
    QVBoxLayout, QSplitter, QGroupBox, QDockWidget,
)

from ..core.methods import (
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
    MetodoGeossintetico,
)
from ..core.models import Projeto
from ..core.persistence import salvar, carregar
from .dialogs.esquema_widget import EsquemaWidget
from .dialogs.metodo_info import MetodoInfoDialog
from .dialogs.quadro_resumo import QuadroResumoWidget
from .panels import PainelDados, PainelResultados
from .resumo_map import resultado_calculado, resultado_para_resumo

logger = logging.getLogger(__name__)

# Índice do seletor/toolbar (0..4) -> classe de método. Mesma ordem do
# programa original (Coul · Rank · DB · Bish · Ref).
_METODOS_POR_ABA = [
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
    MetodoGeossintetico,
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "SoloRef - Dimensionamento de Estruturas de Solo Reforçado"
        )
        self.resize(1440, 820)

        self.projeto = Projeto()
        self.caminho_arquivo: str | None = None
        self._metodo_atual = 1  # começa em Rankine (instantâneo)

        self._montar_central()
        self._montar_actions()
        self._montar_menus()
        self._montar_toolbar()
        self.statusBar().showMessage("Situação ainda indeterminada")

        # cálculo inicial (Rankine) para dar feedback imediato
        self._metodo_actions[self._metodo_atual].setChecked(True)
        self._calcular(self._metodo_atual)

    # ================================================================== #
    # Layout central (três painéis)
    # ================================================================== #
    def _montar_central(self):
        central = QWidget()
        vlay = QVBoxLayout(central)
        vlay.setContentsMargins(4, 4, 4, 4)

        # Splitter de três painéis
        self.splitter = QSplitter(Qt.Horizontal)

        self.painel_dados = PainelDados(self.projeto)
        self.painel_dados.dadosAlterados.connect(self._dados_alterados)

        esquema_box = QGroupBox("Esquema ilustrativo")
        ebl = QVBoxLayout(esquema_box)
        self.esquema = EsquemaWidget(self.projeto)
        ebl.addWidget(self.esquema)

        self.painel_resultados = PainelResultados()
        self.painel_resultados.calcularSolicitado.connect(
            lambda: self._calcular(self._metodo_atual)
        )
        self.painel_resultados.registrarSolicitado.connect(
            lambda: self._mostrar_metodo(self._metodo_atual)
        )
        self.painel_resultados.verHipoteses.connect(self._ver_hipoteses)

        self.splitter.addWidget(self.painel_dados)
        self.splitter.addWidget(esquema_box)
        self.splitter.addWidget(self.painel_resultados)
        # Dados ganha espaço suficiente por padrão para exibir os nomes
        # completos das abas (Geometria, Solo aterro/encosta/fundação,
        # Face, Sobrecarga, Reforço, Identificação) sem abreviar; o
        # esquema ilustrativo deixa de dominar a largura inicial.
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes([620, 470, 330])
        vlay.addWidget(self.splitter, 1)

        self.setCentralWidget(central)

        # Quadro resumo como dock acoplável (substitui a sub-janela MDI)
        self.quadro = QuadroResumoWidget()
        self.dock_resumo = QDockWidget("Quadro resumo", self)
        self.dock_resumo.setWidget(self.quadro)
        self.dock_resumo.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_resumo)
        self.dock_resumo.hide()

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

        self.act_coul = QAction("Método de &Coulomb", self, checkable=True)
        self.act_coul.triggered.connect(lambda: self._selecionar_metodo(0))

        self.act_rank = QAction("Método de &Rankine", self, checkable=True)
        self.act_rank.triggered.connect(lambda: self._selecionar_metodo(1))

        self.act_db = QAction("Método dos &Dois Blocos", self, checkable=True)
        self.act_db.triggered.connect(lambda: self._selecionar_metodo(2))

        self.act_bishop = QAction("Método de &Bishop (novo)", self, checkable=True)
        self.act_bishop.triggered.connect(lambda: self._selecionar_metodo(3))

        self.act_ref = QAction("Refor&ço (geossintético)", self, checkable=True)
        self.act_ref.triggered.connect(lambda: self._selecionar_metodo(4))

        # Grupo exclusivo: os cinco métodos funcionam como abas (navbar
        # única), alternando a visualização sem registrar no quadro resumo.
        self._metodo_actions = [
            self.act_coul, self.act_rank, self.act_db, self.act_bishop,
            self.act_ref,
        ]
        self.grupo_metodos = QActionGroup(self)
        self.grupo_metodos.setExclusive(True)
        for act in self._metodo_actions:
            self.grupo_metodos.addAction(act)

        self.act_comparar = QAction("Compa&rar métodos", self)
        self.act_comparar.setToolTip(
            "Roda os 5 métodos para o projeto atual e registra tudo numa "
            "única coluna do Quadro Resumo."
        )
        self.act_comparar.triggered.connect(self._comparar_metodos)

        self.act_ext = QAction("Estabilidade e&xterna", self)
        self.act_ext.triggered.connect(self._nao_impl)

        self.act_resu = QAction("Quadro Res&umo", self)
        self.act_resu.triggered.connect(self._abrir_resumo)

        self.act_rela = QAction("&Relatórios", self)
        self.act_rela.triggered.connect(self._nao_impl)

        self.act_sobre = QAction("&Sobre...", self)
        self.act_sobre.triggered.connect(self._sobre)

        # Toggles de visibilidade dos painéis (menu Janelas)
        self.act_toggle_dados = QAction("Painel de dados", self, checkable=True)
        self.act_toggle_dados.setChecked(True)
        self.act_toggle_dados.toggled.connect(self.painel_dados.setVisible)

        self.act_toggle_result = QAction("Painel de resultados", self, checkable=True)
        self.act_toggle_result.setChecked(True)
        self.act_toggle_result.toggled.connect(self.painel_resultados.setVisible)

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
        m_dim.addAction(self.act_comparar)
        m_dim.addSeparator()
        m_dim.addAction(self.act_ext)
        m_dim.addAction(self.act_resu)

        m_rel = mb.addMenu("&Relatórios")
        m_rel.addAction(self.act_rela)

        m_janelas = mb.addMenu("&Janelas")
        m_janelas.addAction(self.act_toggle_dados)
        m_janelas.addAction(self.act_toggle_result)
        m_janelas.addAction(self.dock_resumo.toggleViewAction())

        m_ajuda = mb.addMenu("&Ajuda")
        m_ajuda.addAction(self.act_sobre)

    # ================================================================== #
    # Toolbar
    # ================================================================== #
    def _montar_toolbar(self):
        """Navbar única: entrada de dados, os cinco métodos (como abas
        exclusivas) e as demais funções, todos com nomes completos.
        """
        tb = QToolBar("Principal")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(tb)

        tb.addAction(self.act_ed)
        tb.addSeparator()
        for act in self._metodo_actions:
            tb.addAction(act)
        tb.addSeparator()
        tb.addAction(self.act_comparar)
        tb.addSeparator()
        tb.addAction(self.act_ext)
        tb.addAction(self.act_resu)
        tb.addAction(self.act_rela)

    # ================================================================== #
    # Núcleo de cálculo
    # ================================================================== #
    def _dados_alterados(self):
        """Edição no painel de dados: redesenha o esquema ao vivo.

        Como os dados mudaram sem recalcular, a superfície crítica
        desenhada (se houver) ficaria desatualizada — some, volta a
        aparecer só o muro, até o próximo cálculo.
        """
        self.projeto = self.painel_dados.resultado()
        self.esquema.atualizar(self.projeto)
        self.esquema.limpar_resultado()

    def _calcular(self, aba: int):
        """Roda o método `aba`, atualiza esquema + painel de resultados e
        registra no log. Não mexe no Quadro Resumo. Devolve (metodo,
        resultado) ou (None, None) em caso de erro.
        """
        projeto = self.painel_dados.resultado()
        self.projeto = projeto
        metodo = _METODOS_POR_ABA[aba]()
        self.painel_dados.destacar_metodo(metodo.sigla)
        try:
            resultado = metodo.calcular(projeto)
        except Exception as e:  # noqa: BLE001
            logger.exception("Erro ao calcular %s", metodo.nome)
            self.statusBar().showMessage(f"Erro ao calcular {metodo.nome}: {e}")
            return None, None

        self.esquema.atualizar(projeto)
        self.esquema.mostrar_resultado(metodo.sigla, resultado)

        referencia = None
        if metodo.sigla in ("Coul", "DB"):
            # Rankine é fechado/barato — calcula de novo só como referência
            # para a comparação percentual no painel de resultados.
            try:
                referencia = MetodoRankine().calcular(projeto)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Falha ao calcular Rankine de referência para %s", metodo.nome
                )

        self.painel_resultados.mostrar(metodo, resultado, projeto, referencia)
        logger.info(
            "Método executado: %s | entrada=%s | resultado=%s",
            metodo.nome, asdict(projeto), asdict(resultado),
        )

        avisos = metodo.avisos(projeto)
        if avisos:
            self.statusBar().showMessage(avisos[0])
        elif resultado_calculado(resultado):
            self.statusBar().showMessage(self._msg_status(metodo, resultado))
        else:
            self.statusBar().showMessage(
                f"{metodo.nome}: cálculo ainda não implementado"
            )
        return metodo, resultado

    def _selecionar_metodo(self, aba: int):
        """Troca de método na navbar: recalcula e mostra, sem registrar."""
        self._metodo_atual = aba
        self._metodo_actions[aba].setChecked(True)
        self._calcular(aba)

    def _mostrar_metodo(self, aba: int):
        """Botão "Registrar no quadro": recalcula, mostra E registra uma
        situação no Quadro Resumo.
        """
        self._metodo_atual = aba
        self._metodo_actions[aba].setChecked(True)

        metodo, resultado = self._calcular(aba)
        if resultado is None:
            return
        resultados = resultado_para_resumo(_METODOS_POR_ABA[aba], resultado)
        self._abrir_resumo()
        self.quadro.adicionar_situacao(self.projeto, resultados)

    def _comparar_metodos(self):
        """Roda os 5 métodos para o projeto atual de uma vez e registra
        tudo numa única coluna consolidada do Quadro Resumo — comparar é o
        propósito central do programa, e hoje isso exigia registrar cada
        método um a um. Métodos fora da faixa de validade (`avisos()`)
        continuam rodando — não são pulados (ex.: Bishop num muro
        vertical roda igual), só ficam marcados como tal no log e no
        resumo da status bar.
        """
        projeto = self.painel_dados.resultado()
        self.projeto = projeto

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            resultados: dict = {}
            calculados: list[str] = []
            fora_de_faixa: list[str] = []
            falhas: list[str] = []
            for metodo_cls in _METODOS_POR_ABA:
                metodo = metodo_cls()
                avisos = metodo.avisos(projeto)
                try:
                    resultado = metodo.calcular(projeto)
                except Exception:  # noqa: BLE001
                    logger.exception("Comparar métodos: falha em %s", metodo.nome)
                    falhas.append(metodo.sigla)
                    continue
                logger.info(
                    "Comparar métodos — %s | entrada=%s | resultado=%s | avisos=%s",
                    metodo.nome, asdict(projeto), asdict(resultado), avisos,
                )
                resultados.update(resultado_para_resumo(metodo_cls, resultado))
                calculados.append(metodo.sigla)
                if avisos:
                    fora_de_faixa.append(metodo.sigla)
        finally:
            QApplication.restoreOverrideCursor()

        self._abrir_resumo()
        self.quadro.adicionar_situacao(projeto, resultados)

        msg = (f"Comparação: {len(calculados)}/{len(_METODOS_POR_ABA)} "
               f"métodos registrados")
        if fora_de_faixa:
            msg += f" ({', '.join(fora_de_faixa)} fora de faixa)"
        if falhas:
            msg += f" — falharam: {', '.join(falhas)}"
        self.statusBar().showMessage(msg)

    @staticmethod
    def _msg_status(metodo, resultado) -> str:
        e = resultado.extras
        if e.get("n_camadas") is not None:
            return (f"{metodo.nome}: {int(e['n_camadas'])} camadas, "
                    f"Sv={e.get('Sv_m', 0.0):.2f} m")
        if resultado.fator_seguranca and not resultado.solicitacao_kN_m:
            return f"{metodo.nome}: FS={resultado.fator_seguranca:.3f}"
        return (f"{metodo.nome}: solicitação={resultado.solicitacao_kN_m:.3g} kN/m, "
                f"cunha={resultado.inclinacao_cunha_g:.3g}°")

    # ================================================================== #
    # Ações
    # ================================================================== #
    def _novo(self):
        self.projeto = Projeto()
        self.caminho_arquivo = None
        self.painel_dados.set_projeto(self.projeto)
        self.esquema.atualizar(self.projeto)
        self.quadro.limpar()
        self.statusBar().showMessage("Novo projeto")

    def _abrir(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir projeto", "", "Projeto SoloRef (*.json);;Todos (*)"
        )
        if caminho:
            try:
                self.projeto = carregar(caminho)
                self.caminho_arquivo = caminho
                self.painel_dados.set_projeto(self.projeto)
                self.esquema.atualizar(self.projeto)
                self.statusBar().showMessage(f"Carregado: {caminho}")
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, "Erro ao abrir", str(e))

    def _salvar(self, como: bool = False):
        # Consolida o que está no painel antes de salvar
        self.projeto = self.painel_dados.resultado()
        caminho = self.caminho_arquivo
        if como or not caminho:
            caminho, _ = QFileDialog.getSaveFileName(
                self, "Salvar projeto", "", "Projeto SoloRef (*.json)"
            )
            if not caminho:
                return
        try:
            salvar(self.projeto, caminho)
            self.caminho_arquivo = caminho
            self.statusBar().showMessage(f"Salvo: {caminho}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Erro ao salvar", str(e))

    def _entrada_dados(self):
        """ED: garante o painel de dados visível e em foco."""
        self.act_toggle_dados.setChecked(True)
        self.painel_dados.setVisible(True)
        self.painel_dados.setFocus()
        self.statusBar().showMessage("Edite os dados no painel à esquerda")

    def _ver_hipoteses(self):
        """Abre o diálogo de hipóteses/figura da cunha no método atual."""
        dlg = MetodoInfoDialog(self, aba_inicial=self._metodo_atual)
        dlg.exec()

    def _abrir_resumo(self, *args):
        self.dock_resumo.show()
        self.dock_resumo.raise_()

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
