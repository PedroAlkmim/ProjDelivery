# Delivery API (projeto acadêmico)

Backend em **FastAPI + SQLAlchemy + PostgreSQL**. Usa o banco que já existe (14 tabelas + ENUM `forma_pagamento`): **nada é criado nem alterado na estrutura**.

## 1. Requisitos

- Python 3.10 ou superior
- PostgreSQL com o banco já criado e os dados de teste já inseridos

## 2. Instalação

```bash
cd delivery_api
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Configuração

Copie `.env.example` para `.env` e ajuste **DATABASE_URL** (usuário, senha, porta e nome do banco):

```env
DATABASE_URL=postgresql+psycopg2://postgres:SUA_SENHA@localhost:5432/NOME_DO_BANCO
SECRET_KEY=um-texto-longo-qualquer
```

## 4. Converter as senhas de teste para hash (uma única vez)

Os 4 usuários de teste foram inseridos com a senha `123456` em texto puro. A API usa bcrypt para armazenar as senhas com segurança.

Em um banco recém-preparado, execute:

```bash
python -m scripts.hash_senhas
```

**ATENÇÃO:** execute esse script somente uma vez, antes de as senhas serem convertidas para hash. Não execute novamente em um banco que já possui senhas convertidas, pois isso pode impedir os usuários de realizar login.

Depois da conversão, a senha de todos continua sendo `123456` para fazer login.

## 5. Executar

```bash
uvicorn app.main:app --reload
```

Abra o Swagger em **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

## 6. Usuários de teste

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@email.com | 123456 |
| Cliente | cliente@email.com | 123456 |
| Entregador | entregador@email.com | 123456 |
| Estabelecimento | restaurante@email.com | 123456 |

## 7. Como autenticar no Swagger

1. Clique em **Authorize** (cadeado, no topo da página).
2. Em `username` digite o **e-mail** e em `password` a senha. Deixe client_id/secret vazios. Clique em **Authorize**.
3. Para trocar de perfil: **Authorize → Logout** e entre de novo com outro e-mail.

(Alternativa: `POST /auth/login` devolve o `access_token`; cole-o no campo do Authorize se preferir.)

## 8. Roteiro de teste completo (fluxo principal)

Os `id_pedido` dos exemplos podem ser diferentes no seu banco: use sempre o que a resposta devolver.

### A) Login

`POST /auth/login`

```json
{ "email": "cliente@email.com", "senha": "123456" }
```

Resposta `200`:

```json
{ "access_token": "eyJ...", "token_type": "bearer", "perfil": "CLIENTE",
  "id_usuario": 2, "id_perfil": 1, "nome": "João Cliente" }
```

Erros: `401` e-mail/senha inválidos; `403` usuário bloqueado, entregador não aprovado, etc.

### B) Cliente (logado como cliente@email.com)

1. `GET /estabelecimentos?nome=burger` → lista de estabelecimentos ativos (RF28).
2. `GET /estabelecimentos/1/produtos` → cardápio com preço, estoque e imagem (RF29).
3. `GET /clientes/me/enderecos` → anote o `id_endereco`.
4. `POST /pedidos/simular` (RF32/RF34, não grava nada):

```json
{ "id_estabelecimento": 1, "codigo_cupom": null,
  "itens": [ { "id_produto": 1, "quantidade": 2 } ] }
```

Resposta `200`:

```json
{ "estabelecimento": "Burger House",
  "itens": [ { "id_produto": 1, "produto": "X-Burger", "quantidade": 2,
               "preco_unitario": 18.0, "subtotal": 36.0 } ],
  "codigo_cupom": null, "valor_subtotal": 36.0, "taxa_entrega": 5.0,
  "desconto": 0.0, "valor_total": 41.0 }
```

5. `POST /pedidos` (finalizar pedido):

```json
{ "id_estabelecimento": 1, "id_endereco": 1, "forma_pagamento": "PIX",
  "codigo_cupom": null, "observacao": "Sem cebola",
  "itens": [ { "id_produto": 1, "quantidade": 2 } ] }
```

Resposta `201` (resumida):

```json
{ "id_pedido": 3, "status": "CRIADO", "cliente": "João Cliente",
  "estabelecimento": "Burger House", "valor_subtotal": 36.0, "taxa_entrega": 5.0,
  "desconto": 0.0, "valor_total": 41.0,
  "itens": [ { "id_produto": 1, "produto": "X-Burger", "quantidade": 2,
               "preco_unitario": 18.0, "subtotal": 36.0 } ],
  "pagamento": { "forma_pagamento": "PIX", "status_pagamento": "PENDENTE", "valor": 41.0 },
  "entrega": null }
```

O estoque do X-Burger diminui em 2. Erros possíveis: `400` estoque insuficiente / produto de outro estabelecimento / cupom inválido; `404` endereço de outro cliente.

6. `GET /pedidos` e `GET /pedidos/{id_pedido}` → seus pedidos (RF36, RF39). Pedido de outro cliente dá `404`.

### C) Estabelecimento (logado como restaurante@email.com)

1. `GET /estabelecimento/pedidos?status=CRIADO` → o pedido novo aparece.
2. `PATCH /estabelecimento/pedidos/{id}/status` com `{ "status": "CONFIRMADO" }` **antes de confirmar o pagamento** → `409` (RN04, pagamento PIX pendente).
3. `POST /estabelecimento/pedidos/{id}/confirmar-pagamento` → pagamento `APROVADO` (simulado).
4. `PATCH /estabelecimento/pedidos/{id}/status` `{ "status": "CONFIRMADO" }` → ok.
5. `PATCH /estabelecimento/pedidos/{id}/status` `{ "status": "EM_PREPARO" }` → ok.

   Tentar pular etapas (ex.: `CRIADO → EM_PREPARO`) → `409` com as transições permitidas (RN07).
6. `POST /estabelecimento/pedidos/{id}/solicitar-entregador` → `201`, cria a entrega `SOLICITADA` sem entregador (valida o endereço, RF14).
7. Produtos: `GET /estabelecimento/produtos`, `POST /estabelecimento/produtos`, `PUT /estabelecimento/produtos/{id}`, `PATCH /estabelecimento/produtos/{id}/desativar`.

Exemplo `POST /estabelecimento/produtos`:

```json
{ "nome": "X-Salada", "descricao": "Pao, hamburguer, queijo e salada",
  "preco": 20.00, "estoque": 30, "imagem": null, "ativo": true }
```

### D) Entregador (logado como entregador@email.com)

1. `GET /entregador/entregas/disponiveis` → solicitações em aberto (só dados mínimos).
2. `POST /entregador/entregas/{id_entrega}/aceitar` → entrega `AGUARDANDO_RETIRADA`.
3. `PATCH /entregador/entregas/{id_entrega}/status` `{ "status": "EM_ROTA" }` → registra `data_retirada`; pedido vira `EM_ROTA`.
4. `PATCH /entregador/entregas/{id_entrega}/status` `{ "status": "ENTREGUE" }` → registra `data_entrega`; pedido vira `CONCLUIDO`.

   (Se o cliente estiver ausente: `{ "status": "DEVOLVIDA" }` → pedido `DEVOLVIDO`.)
5. `GET /entregador/entregas` → só as entregas atribuídas a você. `PATCH /entregador/disponibilidade` `{ "disponibilidade": true }`.

### E) Avaliação (volte ao cliente)

`POST /avaliacoes`

```json
{ "id_estabelecimento": 1, "nota": 5, "comentario": "Muito bom!" }
```

Só funciona se o cliente tiver pedido `CONCLUIDO` nesse estabelecimento; senão `403`.

### F) Cancelamento

1. Cliente: `POST /pedidos/{id}/cancelamento` `{ "motivo": "Demora na preparação" }` → `201`, status `PENDENTE`.
2. Administrador (admin@email.com): `GET /admin/cancelamentos?status=PENDENTE`.
3. Administrador: `PATCH /admin/cancelamentos/{id}`:

```json
{ "decisao": "APROVADA", "observacao": "Cancelamento aceito." }
```

Ao aprovar: pedido `CANCELADO`, estoque devolvido, pagamento `ESTORNADO` (ou `CANCELADO` se ainda pendente), entrega aberta `CANCELADA`, e o administrador responsável fica gravado na solicitação.

Com `RECUSADA` o pedido não muda.

### G) Administrador (logado como admin@email.com)

- Cadastros: `POST /admin/estabelecimentos`, `POST /admin/entregadores` (nasce `PENDENTE`).
- Aprovar entregador: `PATCH /admin/entregadores/{id}/aprovacao` `{ "status_aprovacao": "APROVADO" }`.
- Usuários: `GET /admin/usuarios?perfil=CLIENTE`, `PATCH /admin/usuarios/{id}/status` `{ "status": "BLOQUEADO" }`.
- Acompanhamento: `GET /admin/pedidos?status=EM_PREPARO`, `GET /admin/entregas?status=EM_ROTA`.
- Cupons: `POST /admin/cupons`, `GET /admin/cupons`, `PATCH /admin/cupons/{id}`.
- Relatórios: `GET /admin/relatorios/pedidos-por-status`, `GET /admin/relatorios/entregas-por-entregador`.

Exemplo de cupom (percentual **ou** valor fixo, nunca os dois):

```json
{ "codigo": "PROMO10", "percentual_desconto": 10, "valor_desconto": null,
  "valor_minimo_pedido": 30, "data_inicio": "2026-01-01T00:00:00",
  "data_fim": "2026-12-31T23:59:59", "ativo": true }
```

Use depois `"codigo_cupom": "PROMO10"` no pedido. Com subtotal de 60,00: desconto 6,00, total 59,00.

## 9. Regras implementadas

- **Valores calculados no backend** com os preços do banco; `preco_unitario` guarda o preço na hora da compra.
- **Estoque** validado e baixado ao criar o pedido (com trava de linha); devolvido ao aprovar cancelamento.
- **Cupom**: precisa estar ativo, dentro do período e respeitar o valor mínimo (RN02). O desconto não passa do subtotal.
- **Status** (RN01/RN07), sequência validada na aplicação:
  - Pedido: `CRIADO → CONFIRMADO → EM_PREPARO → EM_ROTA → CONCLUIDO` (+ `CANCELADO`, `DEVOLVIDO`)
  - Entrega: `SOLICITADA → AGUARDANDO_RETIRADA → EM_ROTA → ENTREGUE` (ou `DEVOLVIDA`; `CANCELADA`)
  - Pagamento: `PENDENTE → APROVADO → ESTORNADO` (`CANCELADO` se cancelado ainda pendente)
- **Pagamento antes de confirmar o pedido** (RN04): só `DINHEIRO` dispensa aprovação prévia (e é marcado `APROVADO` quando a entrega é concluída).
- **Acesso por perfil** (RNF06): cliente só vê seus pedidos; estabelecimento só os seus pedidos/produtos; entregador só as entregas atribuídas a ele; `/admin/*` só administrador.
- **Entregador** só acessa com `status_aprovacao = APROVADO` (RF17).

## 10. Limitações (conforme o banco e o escopo do MVP)

- Taxa de entrega é fixa (`TAXA_ENTREGA` no `.env`); o banco não tem taxa nem valor mínimo por estabelecimento.
- O desconto do cupom não tem coluna própria: aparece na resposta como `desconto = subtotal + taxa - total`.
- Sem tabelas para: gestão financeira/saldo, registro de atividades, descarte de perecíveis, mensagens, área de atendimento.
- Pagamentos são só registrados (nenhuma cobrança real).
- O carrinho não é persistido: ele vai no corpo de `POST /pedidos`.

## 11. Estrutura

```text
delivery_api/
├── app/
│   ├── main.py             # app FastAPI e registro das rotas
│   ├── config.py           # variáveis do .env
│   ├── database.py         # conexão e sessão
│   ├── models.py           # mapeamento das 14 tabelas
│   ├── constants.py        # status e transições válidas
│   ├── security.py         # hash de senha e token
│   ├── deps.py             # usuário logado e controle por perfil
│   ├── schemas/            # modelos de entrada/saída
│   ├── services/           # regras de negócio
│   └── routers/            # endpoints por perfil
├── scripts/hash_senhas.py
├── requirements.txt
├── .env.example
└── .gitignore
```