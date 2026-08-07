# Prompt para o Claude Code — melhorias de interface do SoloRef

Este arquivo é um **prompt-mestre**. Você pode colar tudo de uma vez, ou colar
tarefa por tarefa (recomendado: uma tarefa, revisar, commitar, próxima). As
tarefas estão em ordem de dependência.

---

## Contexto e regras (leia antes de qualquer edição)

```
Você vai melhorar a INTERFACE do SoloRef (camada soloref/ui/), um app PySide6 de
dimensionamento de muros de solo reforçado. Antes de mexer, leia:
MANUAL_SOLOREF.md, PLANO_IMPLEMENTACAO.md e GUIA_DESENVOLVEDOR.md.

Arquitetura: soloref/core/ é Python puro (modelos + cálculos, sem Qt);
soloref/ui/ é PySide6. A UI hoje é uma janela única de três painéis
(soloref/ui/main_window.py): painel de dados à esquerda (soloref/ui/panels.py,
classe PainelDados, que reusa as abas _Aba* de dialogs/entrada_dados.py),
esquema ao centro (dialogs/esquema_widget.py, EsquemaWidget) e resultados à
direita (panels.py, PainelResultados). O Quadro Resumo é um QDockWidget
(dialogs/quadro_resumo.py). O mapeamento resultado→quadro está em
soloref/ui/resumo_map.py.

REGRAS INEGOCIÁVEIS:
1. NÃO altere as fórmulas de cálculo em core/methods/*.py. Os valores numéricos
   devem permanecer idênticos: `python validar.py` tem que continuar 100% verde.
2. NÃO remova nenhuma funcionalidade existente (menus, toolbar, atalhos,
   salvar/abrir JSON, os 5 métodos, hipóteses, quadro resumo, logging).
3. `pytest` deve continuar passando (32 testes hoje) e você deve ADICIONAR
   testes para toda lógica nova que não dependa de Qt.
4. Toda lógica testável deve morar em módulo SEM import de Qt (como resumo_map.py)
   para poder ser testada sem abrir janela. Widgets ficam só com apresentação.
5. Rode `pytest -q` e `python validar.py` ao fim de CADA tarefa e cole o resumo.
6. Commit por tarefa.

Chaves de `Resultado.extras` já disponíveis (use, não recalcule):
- Rankine: extras{Ka, z0_m}; inclinacao_cunha_g; solicitacao_kN_m
- Coulomb: extras{Ka, Ea_busca_cunha_kN_m, theta_g, delta_g}; inclinacao_cunha_g
- Dois Blocos: extras{cunha1_g, cunha2_g, inflexao_m, xp_m}; solicitacao_kN_m
- Bishop: fator_seguranca; extras{xc_m, yc_m, R_m, n_fatias}
- Geossintético: extras{Ka, Tadm_kN_m, n_camadas, Sv_m, Tmax_total_kN_m,
  camadas:[{z_m, sigma_v_kN_m2, Tmax_kN_m, La_m, Le_m, L_m}, ...]}

Campos de geometria (core/models.py, Geometria): altura_H_m,
inclinacao_face_beta_g (90=vertical), largura_aterro_B_m,
inclinacao_encosta_beta_e_g, inclinacao_topo_i_g, altura_topo_Ht_m.
Reforco: tult_kN_m, rf_fluencia, rf_dano_instalacao, rf_degradacao,
ci_interacao, fs_alvo.
```

---

## Tarefa 1 — Faixa de validade e avisos por método (fundação para o resto)

```
Adicione, SEM tocar nos cálculos, uma API de validade a cada método.

1. Em core/methods/base.py, na classe MetodoAnalise, adicione um método:
   `def avisos(self, projeto) -> list[str]: return []`
   (default vazio). Ele recebe o Projeto e devolve avisos de aplicabilidade,
   calculados de forma barata (só a partir dos dados, sem rodar calcular()).

2. Sobrescreva `avisos` em cada método conforme a faixa de validade que já está
   escrita nas hipóteses:
   - Coulomb, Rankine, Dois Blocos (cunha plana): se
     inclinacao_face_beta_g < 70, avisar:
     "Método de cunha plana: rigoroso apenas para face entre 70° e 90°
      (β atual = X°). Para faces mais abatidas use Bishop (cunha circular)."
   - Rankine: se inclinacao_face_beta_g < 90 e coesao_kN_m2 == 0, avisar que
     Rankine é rigoroso só para parede vertical.
   - Bishop: se inclinacao_face_beta_g >= 70, avisar:
     "Bishop (cunha circular) destina-se a taludes/faces abatidas (β < 70°);
      para faces íngremes prefira Coulomb/Rankine (cunha plana)."
     e se inclinacao_face_beta_g >= 89, avisar que a face é praticamente
     vertical e o círculo de ruptura degenera (resultado sem sentido físico).
   - Geossintético: se a tração admissível for insuficiente para o espaçamento
     mínimo (Tult muito baixo p/ γ·H+q), avisar. Reaproveite a mesma condição
     que hoje levanta ValueError, mas aqui só como aviso textual.

3. Crie tests/test_validade.py cobrindo: β=90 não gera aviso de cunha plana em
   Coulomb; β=45 gera; Bishop em β=90 gera aviso de face vertical; Bishop em
   β=30 não gera. NÃO teste texto exato, teste presença/ausência de aviso.

Aceite: `pytest -q` e `python validar.py` verdes; core/methods/*.py com os
mesmos resultados numéricos (só ganhou o método avisos()).
```

---

## Tarefa 2 — Esquema central reflete o resultado real de cada método

```
Hoje EsquemaWidget desenha um muro ilustrativo genérico, igual para todos os
métodos. Faça o painel central desenhar a SUPERFÍCIE CRÍTICA que o método
calculou, por cima do muro, usando os dados já presentes em Resultado.extras.

1. Em dialogs/esquema_widget.py:
   - Refatore o paintEvent extraindo o cálculo de escala/origem (scale, x0, y0)
     para um helper reutilizável, para que o overlay use a MESMA transformação
     mundo→tela do desenho do muro.
   - Adicione `mostrar_resultado(self, sigla: str, resultado)` que guarda o
     resultado do método ativo e chama update(); e `limpar_resultado()`.
   - No paintEvent, se houver resultado, desenhe o overlay conforme a sigla:
       * Rankine/Coulomb ("Rank"/"Coul"): reta da cunha a partir do pé do muro
         com o ângulo inclinacao_cunha_g (da horizontal). Rotule "cunha X°".
       * Dois Blocos ("DB"): linha bilinear usando cunha1_g, cunha2_g e o ponto
         de inflexão (xp_m, inflexao_m). Rotule as duas cunhas.
       * Bishop ("Bish"): arco de círculo com centro (xc_m, yc_m) e raio R_m,
         passando pelo pé do talude. Rotule "FS = ...".
       * Geossintético ("Ref"): linhas horizontais representando as camadas nas
         profundidades z_m da lista `camadas`, cada uma com comprimento L_m a
         partir da face. Rotule "N camadas".
     Use cores distintas do muro e uma legenda curta. Se algum dado faltar,
     desenhe só o muro (fallback seguro, sem exceção).

2. Em main_window.py, no fluxo de cálculo (_calcular), depois de obter o
   resultado, chame self.esquema.mostrar_resultado(metodo.sigla, resultado).
   Em _dados_alterados (edição sem recalcular), chame limpar_resultado() ou
   mantenha o muro; não pode quebrar.

3. Como é desenho, não há teste numérico; garanta que o app abre e desenha para
   os 5 métodos sem exceção (rode manualmente e tire um screenshot de cada;
   descreva o que apareceu). `pytest`/`validar.py` seguem verdes.
```

---

## Tarefa 3 — Relevância das entradas e abas "reservadas"

```
Deixe claro na UI quais dados o método ativo realmente usa, e sinalize as abas
que hoje não alimentam nenhum cálculo.

1. Em panels.py (PainelDados), marque as abas cujos dados não são consumidos por
   nenhum cálculo implementado como reservadas: renomeie os rótulos de
   "Solo encosta", "Solo fundação" e "Face" para incluir o sufixo
   "(estab. externa)" ou "(reservado)", e mostre no topo dessas abas um aviso
   discreto de que os campos ainda não entram no dimensionamento atual.
   NÃO remova as abas nem os campos (serão usados na estabilidade externa).

2. Indique a relevância por método: exponha em cada classe de método um
   atributo/estático (ou uma função em um módulo sem Qt, p.ex. ampliar
   resumo_map.py ou um novo ui/relevancia.py) que liste quais seções/campos o
   método consome:
     - Rankine: geometria (H, β, i), solo_aterro (γ, φ, c), sobrecarga (q)
     - Coulomb: + solo_aterro.angulo_atrito_blocos_g (δ)
     - Dois Blocos: igual Coulomb
     - Bishop: geometria (H, β), solo_aterro (γ, φ, c)
     - Geossintético: geometria (H), solo_aterro (γ, φ), sobrecarga (q), reforço (todos)
   Quando um método está ativo, destaque (negrito/realce) as abas relevantes no
   PainelDados e atenue as demais. Faça a lógica "quais abas para o método X"
   num módulo sem Qt e escreva um teste para ela.

Aceite: teste do mapa de relevância verde; app abre e ao trocar de método o
destaque das abas muda; nada removido.
```

---

## Tarefa 4 — Interpretar o resultado (não só exibir números)

```
Adicione julgamento aos resultados no PainelResultados (panels.py).

1. Bishop: compare fator_seguranca com o FS alvo (projeto.reforco.fs_alvo).
   Mostre um selo "ADEQUADO" (verde) se FS >= alvo, ou "INSUFICIENTE" (vermelho)
   se FS < alvo, junto do cartão de FS.
2. Geossintético: mostre se o dimensionamento fechou (nº de camadas finito e Sv
   > 0) como "OK"; caso a condição de Tult insuficiente ocorra, mostre alerta.
3. Métodos de empuxo: mostre o ponto de aplicação do empuxo (H/3 no caso simples)
   como cartão adicional, e — se disponível — a comparação percentual com
   Rankine (referência), ex.: "Coulomb 11% abaixo de Rankine".
4. Mostre os `avisos(projeto)` da Tarefa 1 como um banner no topo do
   PainelResultados (amarelo, ícone de atenção) sempre que houver avisos para o
   método ativo, e replique o primeiro aviso na status bar.

Toda a lógica de "adequado/insuficiente" e de formatação de cartões deve ficar
em função pura testável (amplie panels._cartoes ou crie ui/interpretacao.py sem
Qt) com testes. Aceite: testes verdes; selos aparecem corretamente para Bishop
adequado/insuficiente.
```

---

## Tarefa 5 — Comparar todos os métodos com um clique

```
Comparar métodos é o propósito da ferramenta; hoje isso exige registrar um a um.

1. Adicione uma ação "Comparar métodos" (toolbar + menu Dimensionamento) que:
   - roda os métodos APLICÁVEIS ao projeto atual (use avisos()/relevância para
     decidir; p.ex. não force Bishop num muro vertical — pode rodar mas marque
     como fora de faixa), com cursor de ocupado;
   - registra todos de uma vez no Quadro Resumo (uma coluna consolidada) e abre
     o dock do quadro.
2. Complete o Quadro Resumo (dialogs/quadro_resumo.py) e o resumo_map.py:
   - adicione a linha "FS, Mét. Bishop" em LINHAS e a chave bishop_fs no
     mapeamento (resumo_map.resultado_para_resumo para MetodoBishop → {bishop_fs});
   - garanta que a linha "número de camadas" seja populada pelo geossintético.
   - preserve as linhas e chaves atuais (coulomb_/rankine_/db_).
3. Amplie os testes de resumo_map para cobrir Bishop e geossintético.

Aceite: um clique preenche o quadro com todos os métodos; Bishop e geossintético
agora aparecem no quadro; testes verdes; validar.py verde.
```

---

## Tarefa 6 — Estado "não salvo" e simplificação do fluxo

```
1. Rastreie alterações não salvas: quando PainelDados.dadosAlterados dispara,
   marque o projeto como "sujo"; mostre um "*" no título da janela
   ("SoloRef - ... *"). Ao Salvar, limpe o estado sujo e o "*".
2. Proteja contra perda de dados: em Novo, Abrir e no fechamento da janela
   (closeEvent), se houver alterações não salvas, pergunte
   (Salvar / Descartar / Cancelar) antes de prosseguir.
3. Revise a redundância Calcular × Registrar: como trocar de método já recalcula,
   o botão "Calcular" ficou redundante. Escolha uma de:
   (a) remover "Calcular" e manter só "Registrar no quadro"; ou
   (b) manter "Calcular" apenas como "recalcular" explícito e renomear para isso.
   Documente a escolha no docstring. Não quebre os sinais existentes
   (calcularSolicitado/registrarSolicitado) — apenas reconecte/aposente com
   cuidado.

A lógica de "está sujo?" deve ser um pequeno helper testável (comparar o Projeto
atual do painel com o último salvo/carregado) sem Qt, com teste. Aceite: título
mostra "*" ao editar e some ao salvar; fechar com alterações pergunta; testes
verdes.
```

---

## Tarefa 7 — Performance percebida nos métodos com otimização

```
Dois Blocos e Bishop rodam otimização (scipy) e podem demorar; trocar de aba não
pode parecer travamento.

1. Cache: guarde o último resultado por método e só recalcule se o Projeto
   mudou desde o último cálculo daquele método (compare via dataclasses.asdict
   ou um hash). Ao trocar para um método já calculado com os mesmos dados, use
   o cache. Invalide o cache inteiro quando os dados mudam.
2. Indicador de ocupado: antes de calcular Dois Blocos/Bishop, mostre
   "Calculando {método}…" na status bar e use QApplication.setOverrideCursor
   (Qt.WaitCursor), restaurando ao fim (inclusive em erro). (Threading real com
   QThread é desejável, mas opcional; se fizer, não bloqueie a UI e trate o
   resultado no thread principal.)
3. A lógica de cache/invalidação deve ser testável sem Qt (um pequeno objeto que
   recebe (metodo_idx, projeto) e diz "hit"/"miss") com teste.

Aceite: alternar entre métodos já calculados é instantâneo; a primeira execução
de DB/Bishop mostra cursor de ocupado; testes verdes; validar.py verde.
```

---

## Tarefa 8 — Verificação final e documentação

```
1. Rode a suíte completa: `pytest -q` (todos verdes, incluindo os novos) e
   `python validar.py` (100% dos casos de literatura verdes — prova de que os
   cálculos não mudaram).
2. Rode o app, exercite os 5 métodos + comparar + salvar/abrir + novo, e tire
   screenshots do esquema por método (Tarefa 2) e do quadro completo (Tarefa 5).
3. Atualize MANUAL_SOLOREF.md e GUIA_DESENVOLVEDOR.md para refletir: esquema
   orientado a dados, avisos de validade, relevância de entradas, interpretação
   de FS, comparação de métodos, estado não salvo e cache. Não preencha a
   Parte III do manual (fica reservada).
4. Cole o resumo final do pytest e do validar.py.
```

---

### Ordem e por que ela importa

A Tarefa 1 (validade no core) é base para as Tarefas 4 e 5. A Tarefa 2 (esquema)
é a de maior impacto visual e independe das outras. As Tarefas 3–7 são
incrementais e podem ir uma a uma. Faça um commit por tarefa: se algo regredir,
`validar.py` e `pytest` apontam na hora.
