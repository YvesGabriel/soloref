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
    MetodoGeossintetico, MetodoEstabilidadeExterna,
)
from ..core.models import Projeto
from ..core.persistence import salvar, carregar
from .dialogs.esquema_widget import EsquemaWidget
from .dialogs.metodo_info import MetodoInfoDialog
from .dialogs.quadro_resumo import QuadroResumoWidget
from .cache_resultados import CacheResultados
from .estado_projeto import projeto_sujo
from .panels import PainelDados, PainelResultados
from .resumo_map import resultado_calculado, resultado_para_resumo

logger = logging.getLogger(__name__)

# Índice do seletor/toolbar (0..4) -> classe de método. Mesma ordem do
# programa original (Coul · Rank · DB · Bish · Ref). Também é o índice
# usado em CacheResultados (0=Coulomb, 1=Rankine, 2=Dois Blocos,
# 3=Bishop, 4=Geossintético).
_METODOS_POR_ABA = [
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
    MetodoGeossintetico,
]
_IDX_RANKINE = 1
# Índice de cache dedicado à Estabilidade Externa — fora da faixa 0..4 dos
# métodos de cunha (não é uma "aba" do grupo exclusivo, é uma verificação
# à parte, mas ainda se beneficia do mesmo cache por método).
_IDX_EXT = 5

# Marcador de `_analise_atual` quando a análise exibida no painel de
# resultados é a Estabilidade Externa, não um dos 5 métodos de cunha
# (que usam o próprio índice inteiro 0..4 como marcador).
_ANALISE_EXT = "ext"

# Siglas dos métodos que rodam otimização (scipy) e podem demorar o
# bastante para justificar cursor de ocupado + mensagem na status bar.
_METODOS_PESADOS = ("DB", "Bish")


class MainWindow(QMainWindow):
    _TITULO_BASE = "SoloRef - Dimensionamento de Estruturas de Solo Reforçado"

    def __init__(self):
        super().__init__()
        self.resize(1440, 820)

        self.projeto = Projeto()
        self.caminho_arquivo: str | None = None
        # Referência p/ "alterações não salvas": o último Projeto salvo ou
        # carregado. Comparado contra painel_dados.resultado() a qualquer
        # momento via estado_projeto.projeto_sujo — ver _atualizar_titulo
        # e _confirmar_descarte.
        self._projeto_salvo: Projeto = self.projeto
        self._metodo_atual = 1  # começa em Rankine (instantâneo)
        # Análise exibida agora no painel de resultados: um índice 0..4 (um
        # dos 5 métodos de cunha) ou `_ANALISE_EXT` (Estabilidade Externa).
        # É o que os botões "Calcular"/"Registrar no quadro" do
        # PainelResultados usam para saber o que recalcular/registrar —
        # diferente de `_metodo_atual`, que só rastreia o último método de
        # CUNHA selecionado (usado pelo diálogo de Hipóteses, que não tem
        # aba para a Estabilidade Externa).
        self._analise_atual: int | str = self._metodo_atual
        # Cache de Resultado por método (índice), válido enquanto o
        # Projeto não mudar — trocar de aba entre métodos já calculados
        # com os mesmos dados fica instantâneo (Dois Blocos/Bishop
        # otimizam e podem demorar). Ver cache_resultados.py.
        self._cache = CacheResultados()

        self._montar_central()
        self._montar_actions()
        self._montar_menus()
        self._montar_toolbar()
        self._atualizar_titulo()
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
        self.painel_resultados.calcularSolicitado.connect(self._recalcular_atual)
        self.painel_resultados.registrarSolicitado.connect(self._registrar_atual)
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
        self.act_ext.setToolTip(
            "Trata o maciço reforçado como bloco rígido: deslizamento, "
            "tombamento e capacidade de carga da fundação."
        )
        self.act_ext.triggered.connect(self._calcular_externa)

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
        aparecer só o muro, até o próximo cálculo. Qualquer edição (não só
        geometria/sobrecarga — ver `PainelDados._ligar_live_update`)
        também pode ligar o "*" de alterações não salvas no título.
        """
        self.projeto = self.painel_dados.resultado()
        self.esquema.atualizar(self.projeto)
        self.esquema.limpar_resultado()
        self._cache.invalidar()
        self._atualizar_titulo()

    def _calcular_com_cache(self, idx: int, metodo, projeto: Projeto):
        """Devolve o `Resultado` de `metodo` para `projeto`, do cache se
        possível (mesmos dados desde o último cálculo desse método —
        instantâneo) ou calculando de novo. Para Dois Blocos/Bishop (que
        otimizam e podem demorar), mostra "Calculando..." na status bar e
        cursor de ocupado enquanto calcula — `processEvents()` garante que
        os dois realmente aparecem na tela antes da chamada bloqueante.
        Propaga qualquer exceção de `metodo.calcular` para o chamador.
        """
        resultado = self._cache.obter(idx, projeto)
        if resultado is not None:
            return resultado

        pesado = metodo.sigla in _METODOS_PESADOS
        if pesado:
            self.statusBar().showMessage(f"Calculando {metodo.nome}…")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
        try:
            resultado = metodo.calcular(projeto)
        finally:
            if pesado:
                QApplication.restoreOverrideCursor()
        self._cache.guardar(idx, projeto, resultado)
        return resultado

    def _calcular_metodo(self, metodo, cache_idx: int):
        """Núcleo comum a todos os métodos — os 5 de cunha (`_calcular`) e
        a Estabilidade Externa (`_calcular_externa`): cache, esquema (com
        overlay), painel de resultados, log e status bar. Não mexe no
        Quadro Resumo. Devolve (metodo, resultado) ou (metodo, None) em
        caso de erro.
        """
        projeto = self.painel_dados.resultado()
        self.projeto = projeto
        self.painel_dados.destacar_metodo(metodo.sigla)
        try:
            resultado = self._calcular_com_cache(cache_idx, metodo, projeto)
        except Exception as e:  # noqa: BLE001
            logger.exception("Erro ao calcular %s", metodo.nome)
            self.statusBar().showMessage(f"Erro ao calcular {metodo.nome}: {e}")
            return metodo, None

        self.esquema.atualizar(projeto)
        self.esquema.mostrar_resultado(metodo.sigla, resultado)

        referencia = None
        if metodo.sigla in ("Coul", "DB"):
            # Rankine é fechado/barato — calcula de novo (ou pega do cache)
            # só como referência para a comparação percentual no painel.
            try:
                referencia = self._calcular_com_cache(
                    _IDX_RANKINE, MetodoRankine(), projeto
                )
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

    def _calcular(self, aba: int):
        """Roda um dos 5 métodos de cunha (índice `aba`, mesmo índice do
        cache) pelo núcleo comum `_calcular_metodo`."""
        metodo = _METODOS_POR_ABA[aba]()
        return self._calcular_metodo(metodo, aba)

    def _calcular_externa(self):
        """Estabilidade externa: mesmo caminho dos 5 métodos de cunha
        (cache, esquema, painel, log) via `_calcular_metodo`, mas fora do
        grupo exclusivo da navbar — é uma verificação à parte, não uma
        "aba" de cunha, então não mexe em `_metodo_atual` (usado só pelo
        diálogo de Hipóteses, que não tem aba para ela). Marca
        `_analise_atual` como a Estabilidade Externa, para que os botões
        "Calcular"/"Registrar no quadro" do painel de resultados passem a
        agir sobre ela em vez de "voltar" para o último método de cunha.
        """
        self._analise_atual = _ANALISE_EXT
        metodo = MetodoEstabilidadeExterna()
        return self._calcular_metodo(metodo, _IDX_EXT)

    def _selecionar_metodo(self, aba: int):
        """Troca de método na navbar: recalcula e mostra, sem registrar."""
        self._metodo_atual = aba
        self._analise_atual = aba
        self._metodo_actions[aba].setChecked(True)
        self._calcular(aba)

    def _mostrar_metodo(self, aba: int):
        """Botão "Registrar no quadro" para um método de cunha: recalcula,
        mostra E registra uma situação no Quadro Resumo. Para a
        Estabilidade Externa, ver `_registrar_externa`.
        """
        self._metodo_atual = aba
        self._analise_atual = aba
        self._metodo_actions[aba].setChecked(True)

        metodo, resultado = self._calcular(aba)
        if resultado is None:
            return
        resultados = resultado_para_resumo(_METODOS_POR_ABA[aba], resultado)
        self._abrir_resumo()
        self.quadro.adicionar_situacao(self.projeto, resultados)

    def _registrar_externa(self):
        """Botão "Registrar no quadro" para a Estabilidade Externa:
        recalcula, mostra E registra os três FS (deslizamento, tombamento,
        capacidade de carga) numa situação do Quadro Resumo — mesmo
        mecanismo de `_mostrar_metodo`, mas para o método fora do grupo de
        cunha.
        """
        metodo, resultado = self._calcular_externa()
        if resultado is None:
            return
        resultados = resultado_para_resumo(MetodoEstabilidadeExterna, resultado)
        self._abrir_resumo()
        self.quadro.adicionar_situacao(self.projeto, resultados)

    def _recalcular_atual(self):
        """Botão "Calcular"/"Recalcular" do painel de resultados: age sobre
        a ANÁLISE ATUALMENTE EXIBIDA (`_analise_atual`) — um método de
        cunha ou a Estabilidade Externa — em vez de sempre voltar para o
        último método de cunha selecionado.
        """
        if self._analise_atual == _ANALISE_EXT:
            self._calcular_externa()
        else:
            self._calcular(self._analise_atual)

    def _registrar_atual(self):
        """Botão "Registrar no quadro" do painel de resultados: grava a
        ANÁLISE ATUALMENTE EXIBIDA (`_analise_atual`) no Quadro Resumo —
        um método de cunha ou a Estabilidade Externa.
        """
        if self._analise_atual == _ANALISE_EXT:
            self._registrar_externa()
        else:
            self._mostrar_metodo(self._analise_atual)

    def _comparar_metodos(self):
        """Roda os 5 métodos de cunha + a Estabilidade Externa para o
        projeto atual de uma vez e registra tudo numa única coluna
        consolidada do Quadro Resumo — comparar é o propósito central do
        programa, e hoje isso exigia registrar cada método um a um.
        Métodos fora da faixa de validade (`avisos()`) continuam rodando
        — não são pulados (ex.: Bishop num muro vertical roda igual), só
        ficam marcados como tal no log e no resumo da status bar.
        """
        projeto = self.painel_dados.resultado()
        self.projeto = projeto

        # Índice de cache (0..4 os de cunha, _IDX_EXT a estabilidade
        # externa) emparelhado com a classe do método.
        metodos_e_indices = list(enumerate(_METODOS_POR_ABA))
        metodos_e_indices.append((_IDX_EXT, MetodoEstabilidadeExterna))

        resultados: dict = {}
        calculados: list[str] = []
        fora_de_faixa: list[str] = []
        falhas: list[str] = []
        for idx, metodo_cls in metodos_e_indices:
            metodo = metodo_cls()
            avisos = metodo.avisos(projeto)
            try:
                # Reaproveita o cache (ex.: método já calculado ao trocar
                # de aba); só mostra cursor de ocupado nos que faltarem.
                resultado = self._calcular_com_cache(idx, metodo, projeto)
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

        self._abrir_resumo()
        self.quadro.adicionar_situacao(projeto, resultados)

        msg = (f"Comparação: {len(calculados)}/{len(metodos_e_indices)} "
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
    # Alterações não salvas
    # ================================================================== #
    def _atualizar_titulo(self) -> None:
        """Recalcula se há alterações não salvas e reflete no título
        (`" *"` no final quando `projeto_sujo`)."""
        sujo = projeto_sujo(self.painel_dados.resultado(), self._projeto_salvo)
        self.setWindowTitle(self._TITULO_BASE + (" *" if sujo else ""))

    def _confirmar_descarte(self, acao: str) -> bool:
        """Se houver alterações não salvas, pergunta Salvar/Descartar/
        Cancelar antes de `acao` (ex.: "criar um novo projeto"). Devolve
        `True` se pode prosseguir (nada sujo, usuário descartou, ou salvou
        com sucesso) e `False` se deve abortar (Cancelar, ou o Salvar não
        se completou — ex.: usuário fechou o file dialog sem escolher).
        """
        if not projeto_sujo(self.painel_dados.resultado(), self._projeto_salvo):
            return True
        resp = QMessageBox.question(
            self, "Alterações não salvas",
            f"Há alterações não salvas. Deseja salvar antes de {acao}?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if resp == QMessageBox.Cancel:
            return False
        if resp == QMessageBox.Discard:
            return True
        self._salvar()
        return not projeto_sujo(self.painel_dados.resultado(), self._projeto_salvo)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if self._confirmar_descarte("fechar o programa"):
            event.accept()
        else:
            event.ignore()

    # ================================================================== #
    # Ações
    # ================================================================== #
    def _novo(self):
        if not self._confirmar_descarte("criar um novo projeto"):
            return
        self.projeto = Projeto()
        self.caminho_arquivo = None
        self.painel_dados.set_projeto(self.projeto)
        self.esquema.atualizar(self.projeto)
        self.quadro.limpar()
        self._projeto_salvo = self.projeto
        self._atualizar_titulo()
        self.statusBar().showMessage("Novo projeto")

    def _abrir(self):
        if not self._confirmar_descarte("abrir outro projeto"):
            return
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir projeto", "", "Projeto SoloRef (*.json);;Todos (*)"
        )
        if caminho:
            try:
                self.projeto = carregar(caminho)
                self.caminho_arquivo = caminho
                self.painel_dados.set_projeto(self.projeto)
                self.esquema.atualizar(self.projeto)
                self._projeto_salvo = self.projeto
                self._atualizar_titulo()
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
            self._projeto_salvo = self.projeto
            self._atualizar_titulo()
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
