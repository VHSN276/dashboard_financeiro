# Controle Financeiro (desktop)

App desktop de finanças pessoais em Python + Flet, com banco SQLite local.
A interface em `views/` e `main.py` parte do protótipo original, adaptado para o
fluxo atual de meses e categorias.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Em sessões Linux Wayland com XWayland disponível, o app seleciona o backend
GTK X11 para evitar incompatibilidades do schema de fontes do GNOME.

Testes: `python -m pytest`

## Gerar o executável

O PyInstaller só gera executável para o sistema em que está rodando, então o
`.exe` precisa ser gerado no Windows (e o `.app`, no macOS).

- Windows: dê dois cliques em `build.bat` (ou rode no terminal). Saída: `dist\ControleFinanceiro.exe`
- macOS/Linux: `./build.sh`. Saída em `dist/`

No Ubuntu, o binário gerado em uma versão só roda em versões iguais ou mais novas
(o do build de referência foi feito no 24.04). Para versões mais antigas, gere com
`./build.sh` na própria máquina.

Os scripts criam um `.venv`, instalam as versões exatas de `requirements-build.txt`
e rodam `flet pack`. O arquivo único extrai-se em uma pasta temporária a cada
abertura, então a primeira tela pode demorar alguns segundos. Executáveis do
PyInstaller sem assinatura digital às vezes são sinalizados por antivírus ou pelo
SmartScreen; é falso positivo conhecido.

## Meses e transações

Cada transação pertence a um mês, escolhido no campo **Mês** do modal (a lista vem
dos meses cadastrados e se atualiza sozinha). Ela só aparece na aba desse mês e só
entra nos totais dele. A data é independente: ao trocar o mês no modal, a data é
levada para o mesmo dia no mês escolhido, mas você pode editá-la depois.

- Renomear um mês leva as transações dele junto.
- Excluir um mês não apaga as transações: elas voltam se você recriar o mês.

## Dados

O banco fica em `~/.controle_financeiro/financas.db`. Bancos criados por versões
anteriores são migrados automaticamente na abertura (cada transação recebe o mês da
sua data) e antes disso é feita uma cópia em `financas.db.v1.bak`. Para usar outro arquivo,
defina a variável de ambiente `CONTROLE_FINANCEIRO_DB`. Na primeira execução são
criadas categorias padrão e o mês atual.

A migração automática cobre o banco SQLite v1. Dados da versão antiga em MySQL
permanecem no banco MySQL e não são importados automaticamente.

## Estrutura

- `main.py`, `views/`: interface (protótipo original)
- `controllers/`: validação, regras de negócio e formatação para as views
- `database/`: esquema, conexão e consultas SQL
- `tests/`: testes unitários, de migração e smoke test das views com página falsa

## Regras implementadas

- Valores guardados em centavos (inteiros); aceita `1.234,56`, `1234.56` ou `50`.
- Meses no formato `AAAA-MM`; excluir ou renomear um mês não apaga transações.
- O tipo da transação precisa ser o mesmo tipo da categoria escolhida.
- Categoria com transações não pode ser excluída nem mudar de tipo.
- Nomes de categoria são únicos, sem diferenciar maiúsculas de minúsculas.
- Erros de validação do modal de transação aparecem dentro do próprio modal.
