# Gestao Financeira

Aplicativo Flask para controle financeiro mensal com salario, gastos fixos, gastos variados, resumo, graficos, historico mensal e categorias gerenciaveis.

Versao atual: 1.1

## Execucao local

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

## Configuracao

As principais variaveis estao documentadas em `.env.example`:

- `APP_ENV`: use `production` no ambiente publicado.
- `SECRET_KEY`: chave longa e aleatoria para sessoes Flask.
- `DATABASE_URL`: ativa PostgreSQL quando usar URL `postgresql://`.
- `CREATE_LOCAL_USER`: controla a criacao automatica do usuario local.
- `LOCAL_USER_NAME` e `LOCAL_USER_PASSWORD`: credenciais do usuario local quando habilitado.

Sem `DATABASE_URL`, o app usa SQLite em `database/app.db`.
