# Organizador Pro — Índice BMAD

Este diretório contém toda a documentação formal do projeto **Organizador Pro** organizada segundo a metodologia **BMAD** (Business, Management, Architecture, Development).

---

## Estrutura de Documentação

```
docs/bmad/
├── 1_negocios/              ← Fase B: Visão de produto, escopo e regras de negócio
│   ├── visao_negocios.md
│   └── README.md
├── 2_gerenciamento/         ← Fase M: Backlog, histórias de usuário e status
│   ├── tarefas.md
│   ├── plano_projeto.md
│   ├── status_fluxo.md      ← PAINEL PRINCIPAL DE STATUS DO PROJETO
│   └── README.md
├── 3_arquitetura/           ← Fase A: Design técnico e diagramas
│   ├── design_arquitetura.md
│   ├── fluxo_dados.md
│   └── README.md
├── 4_desenvolvimento/       ← Fase D: Especificações, guias e relatórios de dev
│   ├── especificacao_desenvolvimento.md
│   ├── guia_implantacao.md
│   ├── auditoria_forense_plano.md      ← Relatório forense: falhas e correções
│   ├── auditoria_forense_tarefas.md    ← Checklist de execução da auditoria
│   ├── auditoria_forense_walkthrough.md ← Walkthrough pós-auditoria
│   └── README.md
└── historico/               ← Trilha histórica e conversas de alinhamento
    ├── trilha_dev_organizador.md
    ├── Roteiro complementar.md
    └── brain_conversas/
        ├── conversa_1_requisitos_e_ux/
        ├── conversa_2_estruturacao_bmad/
        └── conversa_3_planejamento_ui/
```

---

## 🗺️ Navegação Rápida

| Documento | Descrição |
|-----------|-----------|
| [status_fluxo.md](./2_gerenciamento/status_fluxo.md) | **PAINEL PRINCIPAL** — Status de todas as fases do projeto |
| [tarefas.md](./2_gerenciamento/tarefas.md) | Histórias de usuário e critérios de aceite (US1–US5) |
| [visao_negocios.md](./1_negocios/visao_negocios.md) | Proposta de valor, escopo e regras de negócio |
| [design_arquitetura.md](./3_arquitetura/design_arquitetura.md) | Design patterns SOLID e diagrama de componentes |
| [fluxo_dados.md](./3_arquitetura/fluxo_dados.md) | Diagrama de estados do pipeline ETL e concorrência SQLite |
| [especificacao_desenvolvimento.md](./4_desenvolvimento/especificacao_desenvolvimento.md) | Especificação técnica completa das 5 fases |
| [guia_implantacao.md](./4_desenvolvimento/guia_implantacao.md) | Guia de setup e configuração do ambiente |
| [auditoria_forense_walkthrough.md](./4_desenvolvimento/auditoria_forense_walkthrough.md) | Relatório da auditoria forense e ações corretivas |

---

## 📊 Status Atual

> **Fase:** Deploy / Produção (Fase 6 — Próxima Etapa)
>
> Todas as fases de Negócios, Gerenciamento, Arquitetura, Desenvolvimento (Fases 1–5) e QA/Auditoria Forense foram **concluídas com 100% de aprovação** nos testes automatizados (30 pytest + 6 feature tests Laravel).
>
> O próximo passo é executar o empacotamento final via PyInstaller e gerar o bundle de produção em `deploy/producao/`.

---

## 🔗 Rastreabilidade de Conversas

Todas as sessões de desenvolvimento foram preservadas no histórico:

- **`historico/brain_conversas/`** — Conversas das fases de Business e Arquitetura
- **`status_fluxo.md` seção 3** — Rastreabilidade completa de todas as conversas BMAD com ID e fase correspondente

---

*Documentação gerada e mantida pelo agente Antigravity sob metodologia BMAD.*
*Última atualização: 2026-06-13*
