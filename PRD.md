# PRD - Aplicativo Web de Gestao Financeira Pessoal

## 1. Visao Geral

O aplicativo sera um sistema web simples para auxiliar uma pessoa na organizacao da sua gestao financeira mensal. O usuario informara seu salario mensal, seus gastos fixos e seus gastos variados. A partir desses dados, o sistema exibira totais, saldo restante, percentual comprometido do salario e um grafico de pizza para facilitar a visualizacao da distribuicao dos gastos.

Nesta primeira versao, o sistema sera individual e local, sem login e sem banco de dados. A arquitetura deve deixar espaco para evolucoes futuras, como contas de usuario, login, persistencia de dados e historico mensal.

## 2. Objetivo do Produto

Permitir que o usuario tenha uma visao clara e rapida de como seu salario mensal esta sendo usado, separando os gastos em categorias simples:

- Salario mensal
- Gastos fixos
- Gastos variados

O sistema deve ajudar o usuario a responder perguntas como:

- Quanto recebo por mes?
- Quanto gasto com despesas fixas?
- Quanto gasto com despesas variadas?
- Quanto ainda sobra do salario?
- Qual percentual do salario ja foi comprometido?
- Como meus gastos estao distribuidos visualmente?

## 3. Publico-Alvo

Pessoas que desejam controlar melhor seus gastos mensais de forma simples, sem precisar usar planilhas complexas ou aplicativos financeiros completos.

O foco inicial e em usuarios individuais que querem registrar manualmente suas entradas e despesas principais.

## 4. Plataforma

O produto sera desenvolvido inicialmente como uma aplicacao web.

Stack recomendada para o MVP:

- Python
- Flask
- HTML em arquivos dentro de `templates`
- CSS
- JavaScript
- Chart.js para o grafico de pizza

## 5. Escopo do MVP

### Incluido na primeira versao

- Tela principal em formato de painel financeiro mensal.
- Campo para informar o salario mensal.
- Tabela para cadastro de gastos fixos.
- Tabela para cadastro de gastos variados.
- Campo de descricao para cada gasto.
- Campo opcional de categoria para cada gasto.
- Campo de valor para cada gasto.
- Calculo automatico de:
  - Total de gastos fixos
  - Total de gastos variados
  - Total geral de gastos
  - Saldo restante
  - Percentual do salario comprometido
  - Percentual do salario disponivel
- Grafico de pizza exibindo a distribuicao entre:
  - Gastos fixos
  - Gastos variados
  - Saldo restante
- Persistencia local simples usando `localStorage`.
- Interface em tela cheia.
- Moeda padrao: Real brasileiro, exibida como `R$`.
- Gestao mensal.
- Separacao entre logica financeira e template visual.

### Fora do escopo da primeira versao

- Login de usuarios.
- Cadastro de multiplas contas.
- Banco de dados.
- Sincronizacao em nuvem.
- Historico mensal persistente.
- Importacao automatica de extratos bancarios.
- Categorizacao automatica de despesas.
- Aplicativo mobile nativo.
- Deploy em ambiente online/producao.
- Responsividade avancada para mobile.
- Recursos avancados de privacidade e seguranca para ambiente online.

## 6. Estrutura Sugerida de Arquivos

A separacao deve ser feita por arquivos, sem necessidade de criar muitas pastas para a logica.

```text
app.py
finance_logic.py
templates/
  index.html
static/
  style.css
  script.js
```

Responsabilidades:

- `app.py`: inicializa o servidor Flask, define rotas e conecta a interface com a logica.
- `finance_logic.py`: concentra as regras de calculo financeiro.
- `templates/index.html`: estrutura visual principal da pagina.
- `static/style.css`: estilos da interface.
- `static/script.js`: comportamento da tela, manipulacao das tabelas e integracao com o grafico.

## 7. Requisitos Funcionais

### RF01 - Informar salario mensal

O sistema deve permitir que o usuario informe o salario mensal.

Criterios de aceite:

- O campo deve aceitar valores monetarios em Real brasileiro.
- O salario deve ser usado como base para todos os calculos.
- Caso o salario esteja vazio ou zerado, o sistema deve evitar calculos invalidos e orientar visualmente o usuario.

### RF02 - Cadastrar gastos fixos

O sistema deve permitir que o usuario cadastre gastos fixos mensais.

Exemplos:

- Aluguel
- Energia
- Agua
- Internet
- Plano de saude
- Faculdade

Cada item deve conter:

- Descricao
- Categoria opcional
- Valor

Criterios de aceite:

- O usuario deve conseguir adicionar mais de um gasto fixo.
- O usuario deve conseguir remover um gasto fixo.
- O total de gastos fixos deve ser atualizado apos cada alteracao.

### RF03 - Cadastrar gastos variados

O sistema deve permitir que o usuario cadastre gastos variados do mes.

Exemplos:

- Mercado
- Transporte
- Lazer
- Compras eventuais
- Restaurantes
- Emergencias

Cada item deve conter:

- Descricao
- Categoria opcional
- Valor

Criterios de aceite:

- O usuario deve conseguir adicionar mais de um gasto variado.
- O usuario deve conseguir remover um gasto variado.
- O total de gastos variados deve ser atualizado apos cada alteracao.

### RF04 - Calcular resumo financeiro

O sistema deve calcular automaticamente o resumo financeiro mensal.

Informacoes exibidas:

- Salario mensal
- Total de gastos fixos
- Total de gastos variados
- Total geral de gastos
- Saldo restante
- Percentual do salario comprometido
- Percentual do salario disponivel

Criterios de aceite:

- Os valores devem ser atualizados sempre que o salario ou qualquer gasto for alterado.
- O saldo restante deve considerar:

```text
saldo_restante = salario - gastos_fixos - gastos_variados
```

- Se o saldo ficar negativo, o sistema deve destacar visualmente que o usuario ultrapassou o salario mensal.

### RF05 - Exibir grafico de pizza

O sistema deve exibir um grafico de pizza para visualizacao dos dados financeiros.

Fatias do grafico:

- Gastos fixos
- Gastos variados
- Saldo restante

Criterios de aceite:

- O grafico deve ser atualizado conforme os valores forem alterados.
- O grafico deve usar cores distintas para cada fatia.
- Se o saldo restante for negativo, o grafico deve tratar esse caso sem quebrar a visualizacao.

### RF06 - Interface em tres areas principais

A tela deve ser organizada em tres areas principais:

1. Area de salario
2. Area de gastos fixos
3. Area de gastos variados

Tambem deve haver uma area de resumo, preferencialmente ao lado do grafico.

Criterios de aceite:

- A tela deve ocupar bem o espaco disponivel.
- A experiencia deve funcionar em desktop.
- A interface deve ser clara, com bom contraste e leitura facil.

### RF07 - Validar dados informados

O sistema deve validar os dados informados pelo usuario antes de realizar os calculos.

Criterios de aceite:

- Campos de valor devem aceitar numeros validos.
- Valores vazios devem ser tratados como zero.
- Valores negativos nao devem ser aceitos para salario ou gastos.
- O sistema deve aceitar valores decimais.
- O sistema deve considerar o formato brasileiro de moeda na exibicao dos valores.
- A descricao dos gastos deve ser curta e clara. No MVP, pode ser opcional para facilitar o uso inicial.

### RF08 - Exibir estados da interface

O sistema deve lidar com diferentes estados da tela de forma clara para o usuario.

Criterios de aceite:

- Estado inicial sem dados cadastrados.
- Estado com salario zerado ou vazio.
- Estado com saldo positivo.
- Estado com saldo negativo.
- Estado do grafico quando ainda nao houver dados suficientes para exibicao.
- Estado apos adicionar ou remover gastos.

## 8. Requisitos Nao Funcionais

### RNF01 - Simplicidade

O sistema deve ser facil de entender e revisar. A primeira versao deve evitar complexidade desnecessaria.

### RNF02 - Separacao de responsabilidades

A logica de calculos financeiros deve ficar separada da camada visual.

Diretriz:

- Calculos financeiros devem ficar em `finance_logic.py`.
- Estrutura visual deve ficar em `templates/index.html`.
- Interacoes de tela devem ficar em `static/script.js`.

### RNF03 - Manutenibilidade

O codigo deve ser organizado para permitir evolucoes futuras, como banco de dados, login e historico mensal.

### RNF04 - Moeda

O sistema deve usar Real brasileiro como moeda padrao.

Formato esperado:

```text
R$ 1.234,56
```

### RNF05 - Execucao local

O sistema deve ser executado localmente durante o MVP.

Exemplo de execucao:

```bash
python app.py
```

### RNF06 - HTML semantico

O template HTML deve usar uma estrutura semantica para facilitar leitura, manutencao e evolucao do codigo.

Diretrizes:

- Usar elementos como `header`, `main`, `section`, `article`, `table`, `thead`, `tbody`, `form`, `label` e `button` quando fizer sentido.
- Evitar excesso de `div` sem significado estrutural.
- Manter nomes de classes claros e relacionados a funcao do elemento.
- Separar bem a estrutura HTML, os estilos CSS e os comportamentos JavaScript.
- Garantir que campos de formulario tenham `label` associado.
- Usar tabelas HTML para os gastos fixos e variados, ja que os dados possuem formato tabular.

### RNF07 - Acessibilidade basica

O sistema deve seguir boas praticas basicas de acessibilidade desde o MVP.

Diretrizes:

- Associar `label` aos campos de entrada.
- Usar botoes com texto claro.
- Manter contraste visual adequado.
- Organizar as tabelas com cabecalhos apropriados.
- Permitir navegacao basica por teclado nos campos e botoes principais.

### RNF08 - Responsividade inicial

O foco do MVP sera desktop e tela cheia. A interface deve evitar quebras graves em telas menores, mas responsividade avancada para mobile nao faz parte da primeira versao.

Diretrizes:

- Priorizar boa experiencia em desktop.
- Manter a estrutura legivel em telas menores quando possivel.
- Considerar uma versao mobile mais refinada em roadmap futuro.

### RNF09 - Testabilidade da logica financeira

A logica financeira deve ser escrita de forma que possa ser testada separadamente da interface.

Diretrizes:

- Concentrar calculos em funcoes no arquivo `finance_logic.py`.
- Evitar acoplar regras de negocio diretamente ao HTML.
- Permitir testes unitarios para os principais cenarios financeiros.

## 9. Modelo de Dados Inicial

Como a primeira versao nao precisa de banco de dados, os dados podem existir apenas durante o uso da pagina.

Estrutura conceitual:

```python
salary = 3500.00

fixed_expenses = [
    {
        "description": "Aluguel",
        "category": "Moradia",
        "amount": 1200.00
    }
]

variable_expenses = [
    {
        "description": "Mercado",
        "category": "Alimentacao",
        "amount": 450.00
    }
]
```

## 10. Regras de Negocio

### RN01 - Total de gastos fixos

```text
total_gastos_fixos = soma de todos os valores da tabela de gastos fixos
```

### RN02 - Total de gastos variados

```text
total_gastos_variados = soma de todos os valores da tabela de gastos variados
```

### RN03 - Total geral de gastos

```text
total_gastos = total_gastos_fixos + total_gastos_variados
```

### RN04 - Saldo restante

```text
saldo_restante = salario - total_gastos
```

### RN05 - Percentual comprometido

```text
percentual_comprometido = (total_gastos / salario) * 100
```

Se o salario for zero, o percentual comprometido deve ser tratado como zero ou exibido como indisponivel.

### RN06 - Percentual disponivel

```text
percentual_disponivel = (saldo_restante / salario) * 100
```

Se o saldo restante for negativo, o percentual disponivel pode ser exibido como valor negativo para indicar excesso de gastos.

## 11. Layout Esperado

A tela principal deve ser um painel financeiro mensal em tela cheia.

Organizacao sugerida:

- Topo:
  - Titulo do sistema
  - Identificacao do mes atual ou campo para selecionar o mes
- Coluna ou bloco 1 (topo esquerda):
  - Salario mensal
- Coluna ou bloco 2 (topo meio):
  - Tabela de gastos fixos
- Coluna ou bloco 3 (topo direita):
  - Tabela de gastos variados
- Area inferior:
  - Grafico de pizza
  - Resumo financeiro com totais e percentuais

## 12. Comportamentos de Interface

- Ao alterar o salario, os totais devem ser recalculados.
- Ao adicionar um gasto, os totais devem ser recalculados.
- Ao remover um gasto, os totais devem ser recalculados.
- Campos de valor devem aceitar apenas numeros validos.
- Campos vazios devem ser tratados como zero.
- Valores monetarios exibidos devem seguir o padrao brasileiro.
- O saldo negativo deve receber destaque visual.

## 13. Roadmap Futuro

### Versao 2 - Persistencia local

- Salvar dados no navegador usando `localStorage`.
- Permitir que o usuario volte ao sistema e mantenha os dados do mes.
- Status atual: implementado na versao 1.0 como persistencia local simples.

### Versao 3 - Historico mensal

- Permitir criar e consultar meses anteriores.
- Comparar gastos entre meses.
- Exibir evolucao financeira em graficos adicionais.

### Versao 4 - Login e contas de usuario

- Criar base de login opcional.
- Associar dados financeiros a um usuario.
- Permitir acesso em diferentes dispositivos.
- O login nao deve ser obrigatorio enquanto o sistema estiver em modo local.
- A tela principal deve continuar acessivel sem autenticacao.

### Versao 5 - Banco de dados

- Persistir usuarios, salarios, gastos fixos, gastos variados e historico mensal.
- Possiveis opcoes:
  - SQLite para evolucao local simples
  - PostgreSQL para ambiente mais robusto

### Versao 6 - Categorias e metas avancadas

- Evoluir categorias opcionais para categorias gerenciaveis.
- Permitir metas mensais.
- Alertar quando uma categoria ultrapassar o limite definido.

### Versao 7 - Deploy e ambiente online

- Publicar o sistema em uma plataforma de hospedagem.
- Configurar ambiente de producao.
- Preparar variaveis de ambiente para dados sensiveis.
- Ativar HTTPS.
- Planejar backup e recuperacao dos dados quando houver banco de dados.
- Avaliar monitoramento basico de erros e disponibilidade.

Status atual:

- Configuracao por ambiente adicionada via `APP_ENV`, `SECRET_KEY`, `DATABASE_URL` e `CREATE_LOCAL_USER`.
- SQLite permanece como fallback local.
- PostgreSQL passa a ser o banco recomendado para deploy usando `DATABASE_URL`.
- Arquivo `.env.example` documenta as variaveis necessarias.
- `Procfile` e `gunicorn` foram adicionados para execucao em ambiente hospedado.
- Paginas simples de erro 404 e 500 foram adicionadas.
- O cadastro de conta exige usuario minimo e senha de pelo menos 8 caracteres.

Pendencia pos-deploy:

- Ajustar sugestoes de categorias por tipo: categorias do tipo `fixed` devem aparecer apenas em gastos fixos, categorias do tipo `variable` apenas em gastos variados, e categorias do tipo `both` em ambos.

### Versao 8 - Responsividade mobile avancada

- Refinar a experiencia em celulares.
- Reorganizar as tres areas principais em fluxo vertical quando necessario.
- Ajustar tabelas, grafico e resumo financeiro para telas pequenas.
- Testar a experiencia em diferentes tamanhos de tela.

### Versao 9 - Privacidade e seguranca avancadas

- Definir politicas de protecao de dados financeiros pessoais.
- Reforcar autenticacao e controle de acesso.
- Proteger dados sensiveis em ambiente online.
- Avaliar criptografia, logs seguros e politicas de retencao de dados.
- Documentar cuidados de seguranca antes de operar com usuarios reais.

## 14. Criterios Gerais de Sucesso

O MVP sera considerado bem-sucedido quando:

- O usuario conseguir informar seu salario mensal.
- O usuario conseguir adicionar e remover gastos fixos.
- O usuario conseguir adicionar e remover gastos variados.
- O sistema calcular corretamente totais, saldo e percentuais.
- O grafico de pizza representar os dados informados.
- A logica financeira estiver separada do template visual.
- A aplicacao puder ser executada localmente como app web.
- O HTML estiver organizado de forma semantica e facil de manter.
- Os principais estados da interface estiverem tratados.
- A logica financeira puder ser testada separadamente da interface.

## 15. Observacoes Tecnicas

Mesmo que parte dos calculos seja refletida em JavaScript para atualizacao dinamica da tela, a regra principal de calculo deve existir em `finance_logic.py`. Isso facilita revisao, testes e evolucao futura.

O arquivo `templates/index.html` deve priorizar HTML semantico, com secoes bem definidas para salario, gastos fixos, gastos variados, grafico e resumo financeiro. Essa organizacao deve tornar o codigo mais facil de revisar e alterar em versoes futuras.

Em uma etapa posterior, pode ser interessante adicionar testes automatizados para `finance_logic.py`, validando cenarios como:

- Salario sem gastos
- Salario com gastos fixos
- Salario com gastos variados
- Saldo negativo
- Salario zerado
- Valores negativos
- Campos vazios

Responsividade mobile avancada, privacidade robusta e seguranca para ambiente online devem ser tratadas em versoes futuras, especialmente quando o sistema incluir login, banco de dados e deploy.

## 16. Preparacao Para Banco de Dados

Esta secao descreve uma preparacao futura para banco de dados. Ela nao faz parte da versao inicial do MVP, que continua usando dados locais no navegador.

### Objetivo

Preparar o sistema para evoluir de `localStorage` para uma persistencia real, mantendo a logica organizada e permitindo que futuramente existam login, historico mensal e acesso por usuario.

### Banco recomendado por fase

- Primeira evolucao com banco real: SQLite.
- Evolucao para deploy e ambiente online: PostgreSQL.

### Entidades futuras

#### User

Representa um usuario do sistema.

Campos sugeridos:

```text
id
name
password_hash
created_at
updated_at
```

Observacao: a primeira modelagem de usuario nao deve incluir email.

#### MonthBudget

Representa o planejamento financeiro de um usuario em um mes especifico.

Campos sugeridos:

```text
id
user_id
month
year
salary
created_at
updated_at
```

#### Expense

Representa um gasto cadastrado dentro de um planejamento mensal.

Campos sugeridos:

```text
id
month_budget_id
type
description
category
amount
created_at
updated_at
```

O campo `type` deve indicar se o gasto e fixo ou variado.

#### Category

Representa uma categoria gerenciavel de gasto em versoes futuras.

Campos sugeridos:

```text
id
user_id
name
type
created_at
updated_at
```

O campo `type` pode indicar se a categoria e voltada para gastos fixos, gastos variados ou ambos.

### Relacionamentos

```text
User 1:N MonthBudget
MonthBudget 1:N Expense
User 1:N Category
```

### Camada de Repositorio

Quando o banco de dados for implementado, o projeto deve adicionar uma camada de repositorio para isolar o acesso aos dados.

Estrutura futura sugerida:

```text
config.py
init_db.py
database/
  schema.sql
  app.db
repositories/
  budget_repository.py
```

Responsabilidades dessa camada:

- Criar e buscar planejamentos mensais.
- Salvar salario mensal.
- Criar, atualizar e remover gastos.
- Buscar gastos por mes.
- Buscar resumo mensal persistido.
- Facilitar uma futura troca de SQLite para PostgreSQL.

O arquivo `init_db.py` deve permitir inicializar o banco SQLite local e criar um usuario local padrao enquanto ainda nao houver tela de login.

### Fluxo futuro de persistencia

Fluxo atual:

```text
Tela -> localStorage
Tela -> API Flask -> finance_logic.py -> resposta calculada
```

Fluxo futuro:

```text
Tela -> API Flask -> repositorio -> banco de dados
Tela -> API Flask -> finance_logic.py -> resposta calculada
```

Fluxo intermediario implementado:

```text
Tela -> localStorage
Tela -> API Flask -> repositorio -> SQLite
Tela -> API Flask -> finance_logic.py -> resposta calculada
```

Nesta etapa intermediaria, o usuario pode salvar e carregar manualmente os dados do mes no banco SQLite, sem que o login seja obrigatorio.

### Observacoes de migracao

- A versao atual pode continuar usando `localStorage` ate a implementacao do banco.
- Quando o banco for criado, os dados podem ser salvos via API em vez de apenas no navegador.
- O `localStorage` pode continuar existindo temporariamente como cache local ou rascunho.
- A logica de calculo deve continuar separada em `finance_logic.py`.
- O template HTML nao deve acessar diretamente detalhes do banco de dados.
