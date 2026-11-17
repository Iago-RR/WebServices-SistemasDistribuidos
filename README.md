# ⚔️ O Mercador da Steam: Desafio da Mochila 0/1 com Web Services (REST + SOAP + Programação Dinâmica)

Trabalho prático da disciplina de **Sistemas Distribuídos** (**IFNMG**), desenvolvido para explorar, implementar e comparar na prática dois paradigmas distintos de comunicação distribuída na Web: **API REST (JSON)** e **Web Service SOAP (XML baseado em WSDL)**, integrados a um motor de otimização combinatória baseado em **Programação Dinâmica (Problema da Mochila 0/1)**.

---

## 📌 Sumário
1. [Fundamentos Teóricos: REST (JSON) vs. SOAP (WSDL/XML)](#-1-fundamentos-teóricos-rest-json-vs-soap-wsdlxml)
2. [Sobre o Jogo e Mecânica de Otimização](#-2-sobre-o-jogo-e-mecânica-de-otimização)
3. [Infraestrutura do Projeto e Explicação de Cada Função](#-3-infraestrutura-do-projeto-e-explicação-de-cada-função)
4. [Relatório Técnico (Entregável 2.C: Itens a, b, c, d Explicados)](#-4-relatório-técnico-entregável-2c-itens-a-b-c-d-explicados)
5. [Dificuldades Encontradas e Observações Importantes (Item 1 da Apresentação)](#-5-dificuldades-encontradas-e-observações-importantes-item-1-da-apresentação)
6. [Instruções de Como Executar (Entregáveis 2.A e 2.B)](#-6-instruções-de-como-executar-entregáveis-2a-e-2b)

---

## 🌐 1. Fundamentos Teóricos: REST (JSON) vs. SOAP (WSDL/XML)

Para compreender a arquitetura deste projeto, é fundamental partir da diferença conceitual entre **REST** e **SOAP** em Sistemas Distribuídos:

### 1.1. O que é REST (*Representational State Transfer*)?
* **Conceito:** REST não é um protocolo fechado, mas sim um **estilo arquitetural** que utiliza nativamente o protocolo **HTTP** para expor **Recursos** (identificados por URLs/URIs, como `/api/1.0/deals`).
* **Como opera:** Utiliza os próprios verbos semânticos do HTTP (`GET` para buscar, `POST` para criar, `PUT`/`DELETE` para atualizar/remover) e códigos de status HTTP (`200 OK`, `404 Not Found`, `500 Internal Server Error`). É *stateless* (cada requisição é independente).
* **Formato de dados (JSON):** Utiliza predominantemente o **JSON (*JavaScript Object Notation*)**, um formato textual leve de pares `"chave": valor` e listas `[...]`, com baixíssima sobrecarga de rede (*overhead*) e conversão direta para dicionários em Python (`dict`) ou objetos em JavaScript.

### 1.2. O que é SOAP (*Simple Object Access Protocol*)?
* **Conceito:** SOAP é um **protocolo formal e rígido de troca de mensagens** projetado originalmente para integração corporativa e chamadas de procedimentos remotos (*RPC - Remote Procedure Call*). Em vez de acessar "recursos", o cliente invoca **Operações/Funções remotas** (ex: `NumberToDollars(34.97)` ou `NumberToWords(85)`).
* **Como opera (O Envelope XML):** Toda mensagem SOAP — tanto na ida (*Request*) quanto na volta (*Response*) — obrigatoriamente viaja em formato **XML** empacotada dentro de uma estrutura formal chamada **Envelope SOAP**:
  * `<soap:Envelope>`: O elemento raiz que declara via *namespaces* (`xmlns:soap`) que aquele documento XML segue a especificação SOAP.
  * `<soap:Header>` *(opcional)*: Metadados de segurança, autenticação ou transações.
  * `<soap:Body>` *(obrigatório)*: O corpo da mensagem contendo o nome da função chamada e seus parâmetros (na requisição) ou o resultado/erro (na resposta).
* **O papel do WSDL (*Web Services Description Language*):** Todo serviço SOAP possui um arquivo de contrato formal com extensão **`.wsdl`** (escrito em XML). Esse arquivo funciona como um "manual de instruções legível por máquina" que declara exatamente quais funções existem no servidor, quais tipos de dados cada parâmetro exige (`int`, `decimal`, `string`) e qual o endereço (`endpoint`) do serviço.

---

## 🎮 2. Sobre o Jogo e Mecânica de Otimização

**O Mercador da Steam** coloca o jogador no papel de um colecionador com um **orçamento limitado em dólares** (ex: `$30 USD`) diante de uma vitrine com **10 jogos reais em promoção na Steam** (obtidos ao vivo via API REST).

1. **Desafio da Mochila 0/1 (10 Jogos Balanceados):** Cada um dos 10 jogos exibe abertamente seu **Peso/Custo na Mochila (`$`)** e sua **Pontuação de Valor (`+pts`)**. O objetivo é selecionar o subconjunto de jogos que maximize a pontuação total sem estourar o orçamento.
2. **Twist — Eventos Dinâmicos de Mercado:** A cada rodada, uma regra especial da Guilda é sorteada (ex: *Festival Metacritic 82+*, *Frenesi de Super Descontos 80%+*, *Incentivo Indie* ou *Taxa Alfandegária AAA*), modificando pesos e bônus de parte dos jogos. Isso cria **armadilhas gulosas** onde escolher apenas o jogo de maior custo-benefício isolado deixa dinheiro ocioso na carteira.
3. **Oráculo de Programação Dinâmica & Checkout SOAP:** O jogador pode pedir até 3 dicas extraídas da matriz de Programação Dinâmica. Ao fechar a mochila, o sistema:
   * Compara a mochila do jogador com a **Escolha Gulosa (Intuição Humana)** e com o **Ótimo Global da Programação Dinâmica**;
   * Chama o **Web Service SOAP** para emitir o **Cheque Oficial em Dólares por Extenso (`NumberToDollars`)** e a **Certificação Oficial da Porcentagem de Proximidade da Solução Ideal (`NumberToWords`)**.

---

## 🏗️ 3. Infraestrutura do Projeto e Explicação de Cada Função

```text
├── app.py                     # Servidor Flask (Orquestrador REST + SOAP + Programação Dinâmica)
├── requirements.txt           # Dependências Python (flask, requests, zeep, lxml)
├── README.md                  # Relatório Técnico e documentação completa da arquitetura
├── services/
│   ├── __init__.py            # Inicializador do pacote de serviços
│   ├── rest_client.py         # [Entregável 2.A] Cliente da API REST pública (CheapShark - JSON)
│   ├── soap_client.py         # [Entregável 2.B] Cliente do Web Service SOAP (DataAccess - WSDL/XML)
│   └── optimizer.py           # Motor de Programação Dinâmica (Mochila 0/1, Balanceamento e Twists)
└── static/
    ├── index.html             # Interface Web (Vitrine de 10 jogos + Painel Raio-X REST vs SOAP)
    ├── styles.css             # Folha de estilos visual
    └── game.js                # Lógica de eventos no navegador e consumo das rotas do Flask
```

### 3.1. Módulo REST: `services/rest_client.py`
Responsável exclusivamente pela comunicação com a API REST pública **CheapShark**.
* **`fetch_steam_deals(page_size, upper_price, lower_price, min_metacritic, page_number, use_cache=True)`**:
  1. Monta uma requisição HTTP `GET` para `https://www.cheapshark.com/api/1.0/deals` passando filtros na URL (`storeID=1` para Steam, `onSale=1` para jogos em promoção e `metacritic=65`).
  2. Conta com **Cache em Memória com TTL (5 minutos)** e *fallback* resiliente (`_LAST_SUCCESSFUL_REST_RESULT`) para evitar bloqueios por *Rate Limiting* (`HTTP 429`) em chamadas repetidas.
  3. Mede o tempo exato de resposta em milissegundos (`time.perf_counter()`) e o tamanho do payload recebido em bytes (`len(response.content)`).
  4. Converte o texto JSON recebido em listas/dicionários Python (`response.json()`), remove títulos repetidos (`seen_titles`) e calcula o custo discreto inicial (`discreteCost`) e o valor base (`merchantValue`) de cada jogo.
  5. Retorna tanto os jogos higienizados quanto uma amostra real do JSON bruto (`raw_json_sample`) para exibição no Painel Raio-X.

### 3.2. Módulo SOAP: `services/soap_client.py`
Responsável pela comunicação XML com o Web Service SOAP público **DataAccess NumberConversion** baseado em WSDL.
* **`_get_zeep_client()`**:
  * Inicializa o cliente WSDL da biblioteca `zeep` apontando para o arquivo `.wsdl` remoto e guarda a instância em cache (`_CACHED_ZEEP_CLIENT`). Isso evita que o arquivo `.wsdl` seja baixado do zero a cada clique do jogador, reduzindo o tempo de chamada de ~10s para ~300ms. Também acopla o `HistoryPlugin()` para capturar os envelopes XML brutos.
* **`_pretty_format_xml(xml_string)`**:
  * Utiliza `xml.dom.minidom` para indentar o bloco XML recebido, facilitando a leitura humana no Painel Raio-X e nos logs.
* **`convert_amount_to_dollars_soap(amount)`**:
  * Invoca a operação remota **`NumberToDollars`** do WSDL passando um `Decimal` (ex: `26.84`).
  * Retorna o texto do cheque oficial em inglês (`"twenty six dollars and eighty four cents"`), a latência em `ms`, o tamanho em `bytes` e os blocos XML enviados (`raw_xml_request`) e recebidos (`raw_xml_response`). Possui ainda um *fallback* automático que envia o `<soap:Envelope>` via `requests.post` caso o parser WSDL sofra instabilidade.
* **`convert_number_to_words_soap(number)`**:
  * Invoca a operação remota **`NumberToWords`** do WSDL passando um número inteiro (`ubiNum`, ex: `30` para o orçamento da rodada) e extrai a resposta da tag `<m:NumberToWordsResult>` (`"thirty"`).
* **`certify_knapsack_proximity_soap(proximity_percent)`**:
  * Recebe o percentual de proximidade que o jogador atingiu em relação à solução ótima da Mochila 0/1 (ex: `85.2%`), arredonda para inteiro (`85`) e chama `convert_number_to_words_soap(85)` no servidor SOAP para emitir a certificação por extenso: `"85.2% de proximidade da solução ideal (SOAP XML: 'eighty five percent')"`.

### 3.3. Módulo de Otimização e Programação Dinâmica: `services/optimizer.py`
Responsável pelo balanceamento matemático da vitrine, pelos eventos de mercado e pela resolução exata do Problema da Mochila 0/1.
* **`select_balanced_knapsack_games(candidates, budget, target_count=10)`**:
  * Aplica **Amostragem Estratificada por Faixas (Tiers)** nos jogos vindos da API da Steam para evitar que os 10 jogos sejam todos caros demais (onde só caberia 1 jogo) ou baratos demais (onde caberiam todos os 10).
  * Divide os 10 jogos em **3 Jogos Leves** (`12% a 22%` do orçamento), **4 Jogos Médios** (`25% a 38%`) e **3 Jogos Pesados** (`42% a 60%`, travando o teto individual em no máximo 65% do orçamento). Garante que a soma total dos 10 jogos fique sempre em torno de $\approx 2.1 \times W$.
* **`apply_round_twist(games, twist_id)`**:
  * Sorteia um dos 4 **Eventos de Mercado da Rodada** (*Festival Crítica Metacritic 82+*, *Frenesi de Super Descontos 80%+*, *Incentivo Indie* ou *Taxa Alfandegária AAA*) e altera os custos/valores dos jogos correspondentes, criando cenários onde a intuição gulosa falha.
* **`_solve_greedy_baseline(games, budget)`**:
  * Simula a escolha de um **Algoritmo Guloso** (que ordena os jogos pela maior razão $\frac{\text{Valor}}{\text{Custo}}$ e pega os primeiros que cabem). Serve como linha de base para provar quantos pontos a Programação Dinâmica ganha a mais que a escolha gulosa (`dp_beats_greedy_by`).
* **`solve_optimal_steam_bundle(games, budget)`**:
  * Constrói a matriz de Programação Dinâmica `dp[n + 1][W + 1]` aplicando a recorrência clássica da **Mochila 0/1**:
    $$DP[i][w] = \max\left(DP[i-1][w],\; DP[i-1][w - c_i] + v_i\right)$$
  * Realiza o **Backtracking** (percorrendo de `i = 10` até `1`) comparando `dp[i][w_rem] != dp[i-1][w_rem]` para descobrir exatamente quais jogos compõem a **Rota Ideal de Compras** e gerar a explicação matemática de cada decisão (`INCLUÍDO NA ROTA ÓTIMA` vs. `DESCARTADO PELA PD`), além das 3 dicas progressivas do Oráculo.

### 3.4. Servidor Web e Orquestração: `app.py`
* **`index()` (`GET /`)**: Entrega a página HTML principal (`static/index.html`) estilizada com motor óptico *Liquid Glass* (geração dinâmica de *Displacement Map* via *Signed Distance Function* em SVG/Canvas).
* **`create_round()` (`GET /api/round`)**: Coordena o início de cada partida disparando concorrentemente (`ThreadPoolExecutor`) a busca REST (`fetch_steam_deals`) e a validação SOAP do orçamento (`convert_number_to_words_soap`), seleciona e balanceia os 10 jogos (`select_balanced_knapsack_games`), aplica o Twist da rodada (`apply_round_twist`) e resolve a tabela de Programação Dinâmica (`solve_optimal_steam_bundle`).
* **`checkout_round()` (`POST /api/checkout`)**: Recebe os IDs dos jogos colocados na mochila pelo jogador, verifica se respeitou o orçamento, calcula o percentual de proximidade frente ao ótimo da Programação Dinâmica e dispara em paralelo duas chamadas SOAP (`convert_amount_to_dollars_soap` + `certify_knapsack_proximity_soap`) para emitir o recibo e a certificação em XML.

---

## 📋 4. Relatório Técnico (Entregável 2.C: Itens a, b, c, d Explicados)

### a) Links das Documentações Oficiais das APIs Escolhidas
* **API REST (Padrão JSON) — CheapShark Steam Deals API:**
  * Documentação Oficial: https://apidocs.cheapshark.com/
  * Endpoint consumido: `https://www.cheapshark.com/api/1.0/deals`
* **Web Service SOAP (Padrão XML/WSDL) — DataAccess NumberConversion Web Service:**
  * Documentação Oficial das Operações (`NumberToDollars` e `NumberToWords`): https://www.dataaccess.com/webservicesserver/NumberConversion.wso

---

### b) O Link Direto para o Arquivo `.wsdl` Utilizado na Aplicação SOAP
* **Link Direto do Contrato `.wsdl`:**
  👉 **https://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL**

#### 💡 O que esse item (`b`) significa tecnicamente?
No padrão SOAP, o cliente não "adivinha" como chamar o servidor: ele precisa primeiro ler o arquivo **WSDL (*Web Services Description Language*)** nesse link. Ao abrir essa URL no navegador, você verá um documento XML dividido em seções formais:
1. **`<types>` (XSD Schema):** Define os tipos exatos de entrada e saída — por exemplo, que `NumberToDollars` exige um parâmetro `<xs:element name="dNum" type="xs:decimal"/>` e `NumberToWords` exige `<xs:element name="ubiNum" type="xs:unsignedLong"/>`.
2. **`<message>` e `<portType>`:** Declaram as assinaturas das funções disponíveis no serviço.
3. **`<binding>` e `<service>`:** Informam que o transporte deve ser feito via **HTTP POST** em formato `text/xml` (SOAP 1.1) ou `application/soap+xml` (SOAP 1.2) para o endereço `https://www.dataaccess.com/webservicesserver/NumberConversion.wso`.

---

### c) Exemplo Real do Texto JSON que a Aplicação REST Recebe

#### 💡 O que esse item (`c`) significa tecnicamente?
Quando nosso módulo [`services/rest_client.py`](services/rest_client.py) faz um `GET` na CheapShark API, o servidor HTTP responde com o cabeçalho `Content-Type: application/json` e entrega no corpo da resposta uma lista de objetos JSON. Note como o JSON é enxuto: não há tags de abertura/fechamento repetidas nem envelopes de protocolo — apenas os atributos diretos de cada jogo na Steam.

**Exemplo real capturado pela nossa aplicação REST:**
```json
[
  {
    "internalName": "POSSESSORS",
    "title": "Possessor(s)",
    "metacriticLink": "/game/possessors/",
    "dealID": "bj%2B5z967kX%2FPGICjEnf0DZNvfJ%2FgKx8kXaqJjV4Wtms%3D",
    "storeID": "1",
    "gameID": "311663",
    "salePrice": "1.49",
    "normalPrice": "9.99",
    "isOnSale": "1",
    "savings": "85.085085",
    "metacriticScore": "71",
    "steamRatingText": "Mostly Positive",
    "steamRatingPercent": "75",
    "steamRatingCount": "788",
    "steamAppID": "2132890",
    "releaseDate": 1762819200,
    "lastChange": 1794437245,
    "dealRating": "9.5",
    "thumb": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2132890/7aec32ef73e2eb46ea6e5be14740695148d9f000/capsule_231x87.jpg?t=1766931447"
  }
]
```

---

### d) Exemplo Real do Bloco XML que a Aplicação SOAP Recebe

#### 💡 O que esse item (`d`) significa tecnicamente?
Diferente do JSON acima, quando nosso módulo [`services/soap_client.py`](services/soap_client.py) invoca uma operação SOAP, o servidor responde com um documento XML estruturado segundo o protocolo SOAP 1.1:
* `<soap:Envelope>`: Declara o namespace oficial `http://schemas.xmlsoap.org/soap/envelope/`.
* `<soap:Body>`: Contém o objeto de resposta tipado pelo contrato WSDL (`<m:NumberToDollarsResponse>` ou `<m:NumberToWordsResponse>`), vinculado ao namespace do serviço (`xmlns:m="http://www.dataaccess.com/webservicesserver/"`).
* `<m:NumberToDollarsResult>` / `<m:NumberToWordsResult>`: A tag interna onde finalmente reside o dado útil retornado pelo servidor.

**Exemplo real 1 — Bloco XML recebido na emissão do Cheque (`NumberToDollars` para `$34.97`):**
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <m:NumberToDollarsResponse xmlns:m="http://www.dataaccess.com/webservicesserver/">
      <m:NumberToDollarsResult>thirty four dollars and ninety seven cents</m:NumberToDollarsResult>
    </m:NumberToDollarsResponse>
  </soap:Body>
</soap:Envelope>
```

**Exemplo real 2 — Bloco XML recebido na Certificação de Proximidade da Mochila (`NumberToWords` para `85%`):**
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <m:NumberToWordsResponse xmlns:m="http://www.dataaccess.com/webservicesserver/">
      <m:NumberToWordsResult>eighty five</m:NumberToWordsResult>
    </m:NumberToWordsResponse>
  </soap:Body>
</soap:Envelope>
```

---

## ⚠️ 5. Dificuldades Encontradas e Observações Importantes (Item 1 da Apresentação)

1. **Escassez de Serviços SOAP Públicos e Gratuitos Ativos:**
   * A maior dificuldade inicial na etapa de pesquisa foi encontrar Web Services SOAP reais que ainda estivessem online, gratuitos e sem exigência de certificados digitais corporativos. Enquanto APIs REST públicas existem aos milhares, o ecossistema SOAP ficou restrito a sistemas legados, bancários e governamentais (como NF-e e sistemas internos dos Correios). A escolha do serviço público `DataAccess NumberConversion` permitiu integrar um contrato `.wsdl` real e estável ao contexto do jogo.
2. **Custo de Descoberta do Contrato WSDL (Latência Inicial no SOAP):**
   * Observamos nos primeiros testes que instanciar o cliente SOAP (`zeep.Client(wsdl=...)`) a cada requisição fazia a chamada demorar mais de **10 segundos**, pois a biblioteca precisava baixar o arquivo `.wsdl` completo e validar os schemas XSD antes de enviar o XML. Solucionamos isso implementando o cache `_get_zeep_client()` em [`services/soap_client.py`](services/soap_client.py), caindo para **~300 a 500 ms** nas chamadas subsequentes.
3. **Verbosidade do XML (Overhead de Protocolo) vs. Eficiência do JSON:**
   * Para retornar uma única frase como `"thirty four dollars and ninety seven cents"` (42 caracteres), o protocolo SOAP trafega **382 bytes** de envelope XML (quase 9x o tamanho do dado útil em tags e *namespaces*). Já a API REST retorna dezenas de atributos completos de jogos em JSON com estrutura mínima e leitura imediata no JavaScript.
4. **Balanceamento dos Dados Reais da API para o Algoritmo da Mochila:**
   * Como os preços reais retornados pela API da Steam variam muito (muitos jogos de `$1.49` ou jogos caros de `$29.99`), um sorteio puramente aleatório gerava rodadas triviais (onde cabiam todos os 10 jogos ou apenas 1). Foi necessário projetar a função `select_balanced_knapsack_games()` com amostragem estratificada em 3 faixas de orçamento (Leves, Médios e Pesados) para garantir que toda rodada exija raciocínio combinatório real.

---

## 🚀 6. Instruções de Como Executar (Entregáveis 2.A e 2.B)

### Passo 1: Instalar as dependências
No terminal, dentro da pasta raiz do projeto:
```bash
pip install -r requirements.txt
```

### Passo 2: Executar a Aplicação Completa Integrada (Jogo Web + Painel Raio-X)
```bash
python app.py
```
Acesse no navegador: **`http://127.0.0.1:5000`**

### Passo 3: Executar Isoladamente a Aplicação REST (Entregável 2.A)
```bash
python -m services.rest_client
```

### Passo 4: Executar Isoladamente a Aplicação SOAP (Entregável 2.B)
```bash
python -m services.soap_client
```
