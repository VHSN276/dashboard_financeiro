Dashboard de finanças pessoais em Python, Flet e MySQL.

## Preparar o ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
```

Edite `.env` com o usuário e a senha do MySQL (`FINANCE_DB_USER` e
`FINANCE_DB_PASSWORD`). O arquivo `.env` é local e não deve ser enviado ao Git.

## Inicializar e executar

```bash
python -m database.connection_bd
flet run main.py -d
```

A inicialização cria o banco `finance_db`, as tabelas de categorias, transações,
metas e meses, e as categorias padrão quando necessário.
