# Gestão Financeira

Aplicativo Flask para controle financeiro mensal com salário, gastos fixos, gastos variados, resumo, gráficos, histórico mensal, categorias gerenciáveis, metas opcionais por categoria e exportação CSV mensal/anual.

Versão atual: 1.2

## Stack

- Python e Flask
- HTML, CSS e JavaScript puro
- SQLite para uso local
- PostgreSQL em produção via `DATABASE_URL`
- Gunicorn para execução em ambiente hospedado

## Execução local

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

Depois acesse `http://127.0.0.1:5000`.

## Testes

```bash
python -m unittest discover -s tests
```

Rode a suíte antes de enviar alterações para `main`.

## Configuração

As principais variáveis estão documentadas em `.env.example`:

- `APP_ENV`: use `production` no ambiente publicado.
- `SECRET_KEY`: chave longa e aleatória para sessões Flask.
- `DATABASE_URL`: ativa PostgreSQL quando usar URL `postgresql://`.
- `CREATE_LOCAL_USER`: controla a criação automática do usuário local.
- `LOCAL_USER_NAME` e `LOCAL_USER_PASSWORD`: credenciais do usuário local quando habilitado.
- `SESSION_IDLE_TIMEOUT_SECONDS`: tempo de inatividade antes de expirar a sessão.
- `AUTH_RATE_LIMIT_ATTEMPTS`: tentativas inválidas de login/cadastro antes do bloqueio temporário.
- `AUTH_RATE_LIMIT_WINDOW_SECONDS`: janela de tempo usada no bloqueio temporário.

Sem `DATABASE_URL`, o app usa SQLite em `database/app.db`.

## Fluxo de versionamento

- `main` representa a versão estável.
- Use branches curtas por mudança, como `docs/ajuste-readme`, `test/validacao-periodo` ou `refactor/rotas-orcamento`.
- Prefira commits pequenos com prefixos simples: `docs:`, `test:`, `fix:`, `refactor:`, `chore:`.
- Atualize o `CHANGELOG.md` quando a mudança alterar comportamento, validação, segurança, documentação relevante ou fluxo de uso.
- Ao fechar uma versão publicada, crie uma tag no formato `v1.2.0`.
