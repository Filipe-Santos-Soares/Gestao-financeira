# Changelog

## 1.1 - Em desenvolvimento

- Adicionada preparação inicial para banco de dados.
- Criados modelos de domínio para usuário, planejamento mensal, gasto e categoria.
- Criado schema SQLite inicial sem campo de email na tabela de usuários.
- Criada camada inicial de repositorio SQLite para salvar e consultar dados financeiros.
- Adicionado `config.py` com caminho padrao do banco SQLite.
- Adicionado `init_db.py` para inicializar o banco e criar o usuário local padrão.
- Adicionada base de login opcional com sessao Flask.
- Adicionada tela de login opcional sem bloquear o uso do sistema.
- Adicionado hash seguro de senha usando Werkzeug.
- Adicionados endpoints para salvar e carregar o orçamento mensal no SQLite.
- Adicionados botoes `Salvar` e `Carregar` para persistencia manual no banco.
- Adicionada listagem de meses salvos no banco com carregamento rápido pelo histórico.
- Adicionada ação para duplicar os dados do mês anterior para o período selecionado.
- Adicionado cadastro de nova conta na tela de login.
- Adicionada confirmação de senha no cadastro de conta.
- Adicionada comparação entre meses salvos.
- Adicionado gráfico de evolução mensal de gastos e saldo.
- Adicionado cadastro de categorias gerenciáveis com sugestões nos gastos.
- Removido o botão manual `Carregar`, pois a troca de mês/ano agora carrega automaticamente.
- Adicionada configuração por ambiente com `APP_ENV`, `SECRET_KEY`, `DATABASE_URL` e `CREATE_LOCAL_USER`.
- Adicionado suporte configuravel a PostgreSQL via `DATABASE_URL`, mantendo SQLite como fallback local.
- Adicionadas páginas simples de erro 404 e 500.
- Reforçado cadastro com usuário mínimo e senha mínima de 8 caracteres.
- Adicionado `.env.example` para orientar configuração de deploy.
- Adicionado `Procfile` e dependência `gunicorn` para execução em ambiente hospedado.
- Mantido `localStorage` como fallback local da interface.
- Adicionados testes automatizados para a camada de repositorio.
- Atualizada a versão da aplicação para 1.1.
- Adicionada edição e remoção de categorias.
- Ajustadas sugestões de categorias por tipo de gasto.
- Adicionada validação de mês e ano nas APIs de orçamento mensal.
- Adicionada proteção CSRF em ações mutáveis e configuração mais restrita para cookies de sessão.
- Adicionadas metas mensais opcionais por categoria.
- Adicionado painel de acompanhamento de gasto atual contra meta por categoria.

## 1.0 - Versao inicial

- Criado aplicativo web local com Python, Flask, HTML, CSS e JavaScript.
- Separada a logica financeira em `finance_logic.py`.
- Criado template HTML semantico em `templates/index.html`.
- Adicionado cadastro de salário mensal.
- Adicionadas tabelas de gastos fixos e gastos variados.
- Adicionados totais, saldo restante e percentuais.
- Adicionado gráfico de pizza com legenda própria.
- Adicionada validação básica de valores monetários.
- Adicionada persistencia local no navegador com `localStorage`.
- Adicionadas categorias opcionais para os gastos.
- Adicionados testes automatizados para logica financeira e rotas Flask.
