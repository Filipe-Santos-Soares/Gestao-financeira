# Changelog

## 1.1 - Em desenvolvimento

- Adicionada preparacao inicial para banco de dados.
- Criados modelos de dominio para usuario, planejamento mensal, gasto e categoria.
- Criado schema SQLite inicial sem campo de email na tabela de usuarios.
- Criada camada inicial de repositorio SQLite para salvar e consultar dados financeiros.
- Adicionado `config.py` com caminho padrao do banco SQLite.
- Adicionado `init_db.py` para inicializar o banco e criar o usuario local padrao.
- Adicionada base de login opcional com sessao Flask.
- Adicionada tela de login opcional sem bloquear o uso do sistema.
- Adicionado hash seguro de senha usando Werkzeug.
- Adicionados endpoints para salvar e carregar o orcamento mensal no SQLite.
- Adicionados botoes `Salvar` e `Carregar` para persistencia manual no banco.
- Adicionada listagem de meses salvos no banco com carregamento rapido pelo historico.
- Adicionada acao para duplicar os dados do mes anterior para o periodo selecionado.
- Adicionado cadastro de nova conta na tela de login.
- Adicionada confirmacao de senha no cadastro de conta.
- Adicionada comparacao entre meses salvos.
- Adicionado grafico de evolucao mensal de gastos e saldo.
- Adicionado cadastro de categorias gerenciaveis com sugestoes nos gastos.
- Removido o botao manual `Carregar`, pois a troca de mes/ano agora carrega automaticamente.
- Adicionada configuracao por ambiente com `APP_ENV`, `SECRET_KEY`, `DATABASE_URL` e `CREATE_LOCAL_USER`.
- Adicionado suporte configuravel a PostgreSQL via `DATABASE_URL`, mantendo SQLite como fallback local.
- Adicionadas paginas simples de erro 404 e 500.
- Reforcado cadastro com usuario minimo e senha minima de 8 caracteres.
- Adicionado `.env.example` para orientar configuracao de deploy.
- Adicionado `Procfile` e dependencia `gunicorn` para execucao em ambiente hospedado.
- Mantido `localStorage` como fallback local da interface.
- Adicionados testes automatizados para a camada de repositorio.

## 1.0 - Versao inicial

- Criado aplicativo web local com Python, Flask, HTML, CSS e JavaScript.
- Separada a logica financeira em `finance_logic.py`.
- Criado template HTML semantico em `templates/index.html`.
- Adicionado cadastro de salario mensal.
- Adicionadas tabelas de gastos fixos e gastos variados.
- Adicionados totais, saldo restante e percentuais.
- Adicionado grafico de pizza com legenda propria.
- Adicionada validacao basica de valores monetarios.
- Adicionada persistencia local no navegador com `localStorage`.
- Adicionadas categorias opcionais para os gastos.
- Adicionados testes automatizados para logica financeira e rotas Flask.
