--
-- PostgreSQL database dump
--

\restrict 2RgvMuJi92Fylk9110TmeTEbR9zdsp2lW4epBfQ3fnaxyyJHtlRcbChTixgaSUI

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: forma_pagamento; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.forma_pagamento AS ENUM (
    'DINHEIRO',
    'PIX',
    'DEBITO',
    'CREDITO'
);


ALTER TYPE public.forma_pagamento OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: administrador; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.administrador (
    id_administrador integer NOT NULL,
    id_usuario integer NOT NULL,
    nivel_acesso character varying(30) NOT NULL
);


ALTER TABLE public.administrador OWNER TO postgres;

--
-- Name: administrador_id_administrador_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.administrador ALTER COLUMN id_administrador ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.administrador_id_administrador_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: avaliacao; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.avaliacao (
    id_avaliacao integer NOT NULL,
    nota integer NOT NULL,
    comentario text,
    data timestamp without time zone NOT NULL,
    id_cliente integer NOT NULL,
    id_estabelecimento integer NOT NULL,
    CONSTRAINT avaliacao_nota_check CHECK (((nota >= 1) AND (nota <= 5)))
);


ALTER TABLE public.avaliacao OWNER TO postgres;

--
-- Name: avaliacao_id_avaliacao_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.avaliacao ALTER COLUMN id_avaliacao ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.avaliacao_id_avaliacao_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cliente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cliente (
    id_cliente integer NOT NULL,
    id_usuario integer NOT NULL
);


ALTER TABLE public.cliente OWNER TO postgres;

--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.cliente ALTER COLUMN id_cliente ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cliente_id_cliente_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cupom; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cupom (
    id_cupom integer NOT NULL,
    codigo character varying(50) NOT NULL,
    percentual_desconto numeric(5,2),
    valor_desconto numeric(10,2),
    valor_minimo_pedido numeric(10,2),
    data_inicio timestamp without time zone NOT NULL,
    data_fim timestamp without time zone NOT NULL,
    ativo boolean NOT NULL,
    CONSTRAINT cupom_check CHECK ((data_fim >= data_inicio)),
    CONSTRAINT cupom_percentual_desconto_check CHECK (((percentual_desconto >= (0)::numeric) AND (percentual_desconto <= (100)::numeric))),
    CONSTRAINT cupom_valor_desconto_check CHECK ((valor_desconto >= (0)::numeric)),
    CONSTRAINT cupom_valor_minimo_pedido_check CHECK ((valor_minimo_pedido >= (0)::numeric))
);


ALTER TABLE public.cupom OWNER TO postgres;

--
-- Name: cupom_id_cupom_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.cupom ALTER COLUMN id_cupom ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cupom_id_cupom_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: endereco; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.endereco (
    id_endereco integer NOT NULL,
    logradouro character varying(150) NOT NULL,
    numero character varying(20) NOT NULL,
    complemento character varying(100),
    bairro character varying(100) NOT NULL,
    cidade character varying(100) NOT NULL,
    estado character varying(2) NOT NULL,
    cep character varying(9) NOT NULL,
    tipo character varying(30) NOT NULL,
    id_cliente integer NOT NULL
);


ALTER TABLE public.endereco OWNER TO postgres;

--
-- Name: endereco_id_endereco_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.endereco ALTER COLUMN id_endereco ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.endereco_id_endereco_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: entrega; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entrega (
    id_entrega integer NOT NULL,
    data_solicitacao timestamp without time zone NOT NULL,
    data_retirada timestamp without time zone,
    data_entrega timestamp without time zone,
    status character varying(30) NOT NULL,
    id_pedido integer NOT NULL,
    id_entregador integer
);


ALTER TABLE public.entrega OWNER TO postgres;

--
-- Name: entrega_id_entrega_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.entrega ALTER COLUMN id_entrega ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.entrega_id_entrega_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: entregador; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entregador (
    id_entregador integer NOT NULL,
    id_usuario integer NOT NULL,
    disponibilidade boolean NOT NULL,
    status_aprovacao character varying(30) NOT NULL
);


ALTER TABLE public.entregador OWNER TO postgres;

--
-- Name: entregador_id_entregador_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.entregador ALTER COLUMN id_entregador ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.entregador_id_entregador_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estabelecimento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estabelecimento (
    id_estabelecimento integer NOT NULL,
    nome_fantasia character varying(150) NOT NULL,
    cnpj character varying(18) NOT NULL,
    categoria character varying(60) NOT NULL,
    status character varying(30) NOT NULL,
    id_usuario integer NOT NULL
);


ALTER TABLE public.estabelecimento OWNER TO postgres;

--
-- Name: estabelecimento_id_estabelecimento_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estabelecimento ALTER COLUMN id_estabelecimento ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estabelecimento_id_estabelecimento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: item_pedido; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.item_pedido (
    id_pedido integer NOT NULL,
    id_produto integer NOT NULL,
    quantidade integer NOT NULL,
    preco_unitario numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    CONSTRAINT item_pedido_preco_unitario_check CHECK ((preco_unitario >= (0)::numeric)),
    CONSTRAINT item_pedido_quantidade_check CHECK ((quantidade > 0)),
    CONSTRAINT item_pedido_subtotal_check CHECK ((subtotal >= (0)::numeric))
);


ALTER TABLE public.item_pedido OWNER TO postgres;

--
-- Name: pagamento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pagamento (
    id_pagamento integer NOT NULL,
    forma_pagamento public.forma_pagamento NOT NULL,
    status_pagamento character varying(30) NOT NULL,
    valor numeric(10,2) NOT NULL,
    id_pedido integer NOT NULL,
    CONSTRAINT pagamento_valor_check CHECK ((valor >= (0)::numeric))
);


ALTER TABLE public.pagamento OWNER TO postgres;

--
-- Name: pagamento_id_pagamento_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.pagamento ALTER COLUMN id_pagamento ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pagamento_id_pagamento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: pedido; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pedido (
    id_pedido integer NOT NULL,
    data_hora timestamp without time zone NOT NULL,
    status character varying(30) NOT NULL,
    valor_subtotal numeric(10,2) NOT NULL,
    taxa_entrega numeric(10,2) NOT NULL,
    valor_total numeric(10,2) NOT NULL,
    observacao text,
    id_cliente integer NOT NULL,
    id_estabelecimento integer NOT NULL,
    id_endereco integer NOT NULL,
    id_cupom integer,
    CONSTRAINT pedido_taxa_entrega_check CHECK ((taxa_entrega >= (0)::numeric)),
    CONSTRAINT pedido_valor_subtotal_check CHECK ((valor_subtotal >= (0)::numeric)),
    CONSTRAINT pedido_valor_total_check CHECK ((valor_total >= (0)::numeric))
);


ALTER TABLE public.pedido OWNER TO postgres;

--
-- Name: pedido_id_pedido_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.pedido ALTER COLUMN id_pedido ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pedido_id_pedido_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: produto; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.produto (
    id_produto integer NOT NULL,
    nome character varying(150) NOT NULL,
    descricao text,
    preco numeric(10,2) NOT NULL,
    estoque integer NOT NULL,
    imagem character varying(500),
    ativo boolean NOT NULL,
    id_estabelecimento integer NOT NULL,
    CONSTRAINT produto_estoque_check CHECK ((estoque >= 0)),
    CONSTRAINT produto_preco_check CHECK ((preco >= (0)::numeric))
);


ALTER TABLE public.produto OWNER TO postgres;

--
-- Name: produto_id_produto_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.produto ALTER COLUMN id_produto ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.produto_id_produto_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: solicitacao_cancelamento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solicitacao_cancelamento (
    id_solicitacao integer NOT NULL,
    motivo text NOT NULL,
    data_solicitacao timestamp without time zone NOT NULL,
    status character varying(30) NOT NULL,
    observacao text,
    id_cliente integer NOT NULL,
    id_administrador integer,
    id_pedido integer NOT NULL
);


ALTER TABLE public.solicitacao_cancelamento OWNER TO postgres;

--
-- Name: solicitacao_cancelamento_id_solicitacao_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.solicitacao_cancelamento ALTER COLUMN id_solicitacao ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.solicitacao_cancelamento_id_solicitacao_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    senha character varying(255) NOT NULL,
    telefone character varying(20),
    status character varying(30) NOT NULL
);


ALTER TABLE public.usuario OWNER TO postgres;

--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.usuario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.usuario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: administrador; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.administrador (id_administrador, id_usuario, nivel_acesso) FROM stdin;
1	1	Suporte
\.


--
-- Data for Name: avaliacao; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.avaliacao (id_avaliacao, nota, comentario, data, id_cliente, id_estabelecimento) FROM stdin;
1	5	Muito bom!	2026-11-08 15:45:14.644906	3	1
\.


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cliente (id_cliente, id_usuario) FROM stdin;
1	2
3	5
\.


--
-- Data for Name: cupom; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cupom (id_cupom, codigo, percentual_desconto, valor_desconto, valor_minimo_pedido, data_inicio, data_fim, ativo) FROM stdin;
1	PROMO10	10.00	\N	30.00	2026-01-01 00:00:00	2026-12-31 23:59:59	t
\.


--
-- Data for Name: endereco; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.endereco (id_endereco, logradouro, numero, complemento, bairro, cidade, estado, cep, tipo, id_cliente) FROM stdin;
1	Rua 10	250	Apto 302	Setor Oeste	Goiania	GO	74120-020	RESIDENCIAL	1
2	Rua 15	100	Casa	Setor Bueno	Goiania	GO	74230-010	RESIDENCIAL	3
\.


--
-- Data for Name: entrega; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.entrega (id_entrega, data_solicitacao, data_retirada, data_entrega, status, id_pedido, id_entregador) FROM stdin;
2	2026-11-08 15:39:08.749973	2026-11-08 15:42:39.856613	2026-11-08 15:43:23.957683	ENTREGUE	3	1
1	2026-10-27 16:05:21.459503	2026-11-08 18:04:05.416176	2026-11-08 18:04:30.158938	ENTREGUE	1	1
\.


--
-- Data for Name: entregador; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.entregador (id_entregador, id_usuario, disponibilidade, status_aprovacao) FROM stdin;
1	3	t	APROVADO
\.


--
-- Data for Name: estabelecimento; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.estabelecimento (id_estabelecimento, nome_fantasia, cnpj, categoria, status, id_usuario) FROM stdin;
1	Burger House	12.345.678/0001-90	Hamburgueria	ATIVO	4
\.


--
-- Data for Name: item_pedido; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.item_pedido (id_pedido, id_produto, quantidade, preco_unitario, subtotal) FROM stdin;
1	1	2	18.00	36.00
2	2	1	22.00	22.00
2	4	1	6.00	6.00
3	1	1	18.00	18.00
3	3	1	12.00	12.00
\.


--
-- Data for Name: pagamento; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pagamento (id_pagamento, forma_pagamento, status_pagamento, valor, id_pedido) FROM stdin;
1	PIX	APROVADO	41.00	1
3	DINHEIRO	APROVADO	35.00	3
2	DINHEIRO	CANCELADO	33.00	2
\.


--
-- Data for Name: pedido; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pedido (id_pedido, data_hora, status, valor_subtotal, taxa_entrega, valor_total, observacao, id_cliente, id_estabelecimento, id_endereco, id_cupom) FROM stdin;
3	2026-11-08 15:23:24.059184	CONCLUIDO	30.00	5.00	35.00	Retirar a salada do X-Burger e enviar sachês de ketchup.	3	1	2	\N
2	2026-10-27 15:55:21.459503	CANCELADO	28.00	5.00	33.00	TESTE: pedido com cancelamento	1	1	1	\N
1	2026-10-27 16:05:21.459503	CONCLUIDO	36.00	5.00	41.00	TESTE: pedido normal	1	1	1	\N
\.


--
-- Data for Name: produto; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.produto (id_produto, nome, descricao, preco, estoque, imagem, ativo, id_estabelecimento) FROM stdin;
1	X-Burger	Pao, hamburguer, queijo e salada	18.00	49	\N	t	1
3	Batata Frita	Porcao individual de batata frita	12.00	59	\N	t	1
2	X-Bacon	Pao, hamburguer, queijo e bacon crocante	22.00	41	\N	t	1
4	Refrigerante	Lata 350 ml	6.00	101	\N	t	1
5	X-Salada	Pao, hamburguer artesanal, queijo, presunto, alface, tomate, milho, batata palha e molho especial	21.50	25	\N	t	1
\.


--
-- Data for Name: solicitacao_cancelamento; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solicitacao_cancelamento (id_solicitacao, motivo, data_solicitacao, status, observacao, id_cliente, id_administrador, id_pedido) FROM stdin;
1	Cliente desistiu do pedido	2026-10-27 16:05:21.459503	APROVADA	Cancelamento aceito.	1	1	2
2	Demora na preparação	2026-11-08 16:01:13.303154	RECUSADA	Cancelamento recusado. O pedido já está em preparação.	1	1	1
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuario (id, nome, email, senha, telefone, status) FROM stdin;
1	Carlos Administrador	admin@email.com	$2b$12$nlzRAOoXnx/e5U6mgCN3DOiF2OAaR5Pnr0WILM4zNl4WMdaj3DSf2	62999990001	ATIVO
2	João Cliente	cliente@email.com	$2b$12$zTZZpdM4xV5yGk6UwaeKauolpmz4No7JIHSuJVXVZJpe4AfkOOUY6	62999990002	ATIVO
3	Pedro Entregador	entregador@email.com	$2b$12$BL0xSNMzlb0fRbC0r.iAoexrYSc/1F52HNXzrZ5zBobyKsACQw6Au	62999990003	ATIVO
4	Burger House	restaurante@email.com	$2b$12$ky8QObFj0Hmby5FjQlPQ7eVmvQdecKRYym3nREEEJmQ3qE3nlBJY.	62999990004	ATIVO
5	Maria Teste	maria.teste@email.com	$2b$12$qnjVg1TfUwui5H43vmidQuoUwGHWIb6nrgGZq5.KkJYl1vluD89yO	62988887766	ATIVO
\.


--
-- Name: administrador_id_administrador_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.administrador_id_administrador_seq', 1, true);


--
-- Name: avaliacao_id_avaliacao_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.avaliacao_id_avaliacao_seq', 1, true);


--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cliente_id_cliente_seq', 3, true);


--
-- Name: cupom_id_cupom_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cupom_id_cupom_seq', 1, true);


--
-- Name: endereco_id_endereco_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.endereco_id_endereco_seq', 2, true);


--
-- Name: entrega_id_entrega_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.entrega_id_entrega_seq', 2, true);


--
-- Name: entregador_id_entregador_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.entregador_id_entregador_seq', 1, true);


--
-- Name: estabelecimento_id_estabelecimento_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estabelecimento_id_estabelecimento_seq', 1, true);


--
-- Name: pagamento_id_pagamento_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pagamento_id_pagamento_seq', 3, true);


--
-- Name: pedido_id_pedido_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pedido_id_pedido_seq', 3, true);


--
-- Name: produto_id_produto_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.produto_id_produto_seq', 5, true);


--
-- Name: solicitacao_cancelamento_id_solicitacao_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solicitacao_cancelamento_id_solicitacao_seq', 2, true);


--
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuario_id_seq', 5, true);


--
-- Name: administrador administrador_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.administrador
    ADD CONSTRAINT administrador_id_usuario_key UNIQUE (id_usuario);


--
-- Name: administrador administrador_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.administrador
    ADD CONSTRAINT administrador_pkey PRIMARY KEY (id_administrador);


--
-- Name: avaliacao avaliacao_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.avaliacao
    ADD CONSTRAINT avaliacao_pkey PRIMARY KEY (id_avaliacao);


--
-- Name: cliente cliente_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_id_usuario_key UNIQUE (id_usuario);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id_cliente);


--
-- Name: cupom cupom_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cupom
    ADD CONSTRAINT cupom_codigo_key UNIQUE (codigo);


--
-- Name: cupom cupom_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cupom
    ADD CONSTRAINT cupom_pkey PRIMARY KEY (id_cupom);


--
-- Name: endereco endereco_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.endereco
    ADD CONSTRAINT endereco_pkey PRIMARY KEY (id_endereco);


--
-- Name: entrega entrega_id_pedido_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entrega
    ADD CONSTRAINT entrega_id_pedido_key UNIQUE (id_pedido);


--
-- Name: entrega entrega_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entrega
    ADD CONSTRAINT entrega_pkey PRIMARY KEY (id_entrega);


--
-- Name: entregador entregador_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entregador
    ADD CONSTRAINT entregador_id_usuario_key UNIQUE (id_usuario);


--
-- Name: entregador entregador_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entregador
    ADD CONSTRAINT entregador_pkey PRIMARY KEY (id_entregador);


--
-- Name: estabelecimento estabelecimento_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT estabelecimento_cnpj_key UNIQUE (cnpj);


--
-- Name: estabelecimento estabelecimento_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT estabelecimento_id_usuario_key UNIQUE (id_usuario);


--
-- Name: estabelecimento estabelecimento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT estabelecimento_pkey PRIMARY KEY (id_estabelecimento);


--
-- Name: item_pedido item_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_pedido
    ADD CONSTRAINT item_pedido_pkey PRIMARY KEY (id_pedido, id_produto);


--
-- Name: pagamento pagamento_id_pedido_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagamento
    ADD CONSTRAINT pagamento_id_pedido_key UNIQUE (id_pedido);


--
-- Name: pagamento pagamento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagamento
    ADD CONSTRAINT pagamento_pkey PRIMARY KEY (id_pagamento);


--
-- Name: pedido pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_pkey PRIMARY KEY (id_pedido);


--
-- Name: produto produto_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produto
    ADD CONSTRAINT produto_pkey PRIMARY KEY (id_produto);


--
-- Name: solicitacao_cancelamento solicitacao_cancelamento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitacao_cancelamento
    ADD CONSTRAINT solicitacao_cancelamento_pkey PRIMARY KEY (id_solicitacao);


--
-- Name: usuario usuario_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_email_key UNIQUE (email);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- Name: administrador administrador_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.administrador
    ADD CONSTRAINT administrador_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id);


--
-- Name: avaliacao avaliacao_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.avaliacao
    ADD CONSTRAINT avaliacao_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente);


--
-- Name: avaliacao avaliacao_id_estabelecimento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.avaliacao
    ADD CONSTRAINT avaliacao_id_estabelecimento_fkey FOREIGN KEY (id_estabelecimento) REFERENCES public.estabelecimento(id_estabelecimento);


--
-- Name: cliente cliente_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id);


--
-- Name: endereco endereco_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.endereco
    ADD CONSTRAINT endereco_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente);


--
-- Name: entrega entrega_id_entregador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entrega
    ADD CONSTRAINT entrega_id_entregador_fkey FOREIGN KEY (id_entregador) REFERENCES public.entregador(id_entregador);


--
-- Name: entrega entrega_id_pedido_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entrega
    ADD CONSTRAINT entrega_id_pedido_fkey FOREIGN KEY (id_pedido) REFERENCES public.pedido(id_pedido);


--
-- Name: entregador entregador_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entregador
    ADD CONSTRAINT entregador_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id);


--
-- Name: estabelecimento estabelecimento_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT estabelecimento_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id);


--
-- Name: item_pedido item_pedido_id_pedido_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_pedido
    ADD CONSTRAINT item_pedido_id_pedido_fkey FOREIGN KEY (id_pedido) REFERENCES public.pedido(id_pedido);


--
-- Name: item_pedido item_pedido_id_produto_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_pedido
    ADD CONSTRAINT item_pedido_id_produto_fkey FOREIGN KEY (id_produto) REFERENCES public.produto(id_produto);


--
-- Name: pagamento pagamento_id_pedido_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagamento
    ADD CONSTRAINT pagamento_id_pedido_fkey FOREIGN KEY (id_pedido) REFERENCES public.pedido(id_pedido);


--
-- Name: pedido pedido_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente);


--
-- Name: pedido pedido_id_cupom_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_id_cupom_fkey FOREIGN KEY (id_cupom) REFERENCES public.cupom(id_cupom);


--
-- Name: pedido pedido_id_endereco_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_id_endereco_fkey FOREIGN KEY (id_endereco) REFERENCES public.endereco(id_endereco);


--
-- Name: pedido pedido_id_estabelecimento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_id_estabelecimento_fkey FOREIGN KEY (id_estabelecimento) REFERENCES public.estabelecimento(id_estabelecimento);


--
-- Name: produto produto_id_estabelecimento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produto
    ADD CONSTRAINT produto_id_estabelecimento_fkey FOREIGN KEY (id_estabelecimento) REFERENCES public.estabelecimento(id_estabelecimento);


--
-- Name: solicitacao_cancelamento solicitacao_cancelamento_id_administrador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitacao_cancelamento
    ADD CONSTRAINT solicitacao_cancelamento_id_administrador_fkey FOREIGN KEY (id_administrador) REFERENCES public.administrador(id_administrador);


--
-- Name: solicitacao_cancelamento solicitacao_cancelamento_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitacao_cancelamento
    ADD CONSTRAINT solicitacao_cancelamento_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente);


--
-- Name: solicitacao_cancelamento solicitacao_cancelamento_id_pedido_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitacao_cancelamento
    ADD CONSTRAINT solicitacao_cancelamento_id_pedido_fkey FOREIGN KEY (id_pedido) REFERENCES public.pedido(id_pedido);


--
-- PostgreSQL database dump complete
--

\unrestrict 2RgvMuJi92Fylk9110TmeTEbR9zdsp2lW4epBfQ3fnaxyyJHtlRcbChTixgaSUI

