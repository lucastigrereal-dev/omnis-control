# API Contract — PubliPrice v1.0

**Base URL:** `http://localhost:5010/api/v1`
**Content-Type:** `application/json; charset=utf-8`
**Autenticacao:** Nenhuma (local-first, single-user)
**Versao:** 1.0 | **Data:** 2026-05-18

---

## Convencoes

- Todos os timestamps em ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- Moeda sempre em **reais (R$)**, formato `float` com 2 casas decimais
- IDs sao inteiros autoincrement
- Erros seguem o padrao: `{ "erro": true, "mensagem": "...", "codigo": 400 }`

---

## 1. PERFIS

### GET /perfis
Lista todos os perfis ativos.

**Response 200:**
```json
{
  "total": 6,
  "total_seguidores": 2581000,
  "perfis": [
    {
      "id": 1,
      "handle": "lucastigrereal",
      "nome_exibicao": "Lucas Tigre Real",
      "seguidores": 690000,
      "nicho": "lifestyle",
      "engagement_rate": 3.2,
      "alcance_medio": 185000,
      "ativo": true,
      "criado_em": "2026-05-18T10:00:00"
    }
  ]
}
```

---

### GET /perfis/:id
Retorna um perfil especifico.

**Response 200:** Objeto `perfil` unico.
**Response 404:** `{ "erro": true, "mensagem": "Perfil nao encontrado", "codigo": 404 }`

---

### POST /perfis
Cadastra novo perfil.

**Request Body:**
```json
{
  "handle": "novoperfil",
  "nome_exibicao": "Novo Perfil",
  "seguidores": 50000,
  "nicho": "turismo",
  "engagement_rate": 2.8,
  "alcance_medio": 18000
}
```

**Response 201:** Objeto `perfil` criado com `id`.
**Response 400:** Validacao falhou (campos obrigatorios, valores invalidos).
**Response 409:** Handle ja cadastrado.

---

### PUT /perfis/:id
Atualiza metricas de um perfil. Somente campos enviados sao atualizados (partial update).

**Request Body:**
```json
{
  "seguidores": 695000,
  "engagement_rate": 3.5,
  "alcance_medio": 192000
}
```

**Response 200:** Objeto `perfil` atualizado.
**Response 404:** Perfil nao encontrado.

---

### DELETE /perfis/:id
Soft-delete (marca `ativo = 0`). Nao remove fisicamente — cotacoes antigas preservam referencia.

**Response 200:** `{ "sucesso": true, "mensagem": "Perfil desativado" }`

---

## 2. PACOTES

### GET /pacotes
Lista todos os pacotes.

**Response 200:**
```json
{
  "total": 3,
  "pacotes": [
    {
      "id": 1,
      "nome": "Starter",
      "descricao": "1 collab em 1 perfil. Entrada acessivel.",
      "collabs": 1,
      "stories": 0,
      "reels": 0,
      "carrosseis": 0,
      "perfis_minimos": 1,
      "preco_base": 350.00,
      "seogram": false,
      "recomendado": false
    }
  ]
}
```

---

### GET /pacotes/:id
Retorna um pacote especifico.

---

### POST /pacotes
Cria novo pacote personalizado.

**Request Body:**
```json
{
  "nome": "Personalizado",
  "descricao": "Pacote sob medida",
  "collabs": 2,
  "stories": 5,
  "reels": 1,
  "carrosseis": 2,
  "perfis_minimos": 2,
  "preco_base": 1500.00
}
```

**Response 201:** Objeto `pacote` criado.

---

## 3. CLIENTES

### GET /clientes
Lista clientes. Query params opcionais: `?segmento=hotel&cidade=Natal&q=termo`

**Response 200:**
```json
{
  "total": 12,
  "clientes": [
    {
      "id": 1,
      "nome": "Maria Souza",
      "hotel": "Grand Hotel Ponta Negra",
      "cidade": "Natal",
      "uf": "RN",
      "segmento": "hotel",
      "telefone": "(84) 99999-0000",
      "instagram": "@grandhotelpontanegra",
      "data_contato": "2026-05-15"
    }
  ]
}
```

---

### GET /clientes/:id
Retorna cliente + ultimas 5 cotacoes vinculadas.

**Response 200:**
```json
{
  "cliente": { },
  "ultimas_cotacoes": [ ]
}
```

---

### POST /clientes
Cadastra novo cliente.

**Request Body:**
```json
{
  "nome": "Joao Silva",
  "hotel": "Pousada Villa do Sol",
  "cidade": "Tiradentes",
  "uf": "MG",
  "segmento": "pousada",
  "instagram": "@pousadavilladosol"
}
```

**Response 201:** Objeto `cliente` criado.

---

## 4. COTACOES

### GET /cotacoes
Lista historico de cotacoes. Query params opcionais:
- `?status=fechada` — filtra por status
- `?perfil_id=1` — filtra por perfil
- `?cliente_id=3` — filtra por cliente
- `?q=termo` — busca por nome do cliente/hotel
- `?ordem=data` (default) ou `ordem=valor`
- `?direcao=desc` (default) ou `direcao=asc`
- `?limite=20&offset=0` — paginacao

**Response 200:**
```json
{
  "total": 47,
  "limite": 20,
  "offset": 0,
  "cotacoes": [
    {
      "id": 1,
      "perfil": { "id": 1, "handle": "lucastigrereal", "nicho": "lifestyle" },
      "pacote": { "id": 2, "nome": "Growth", "preco_base": 990.00 },
      "cliente": { "id": 1, "nome": "Maria Souza", "hotel": "Grand Hotel Ponta Negra" },
      "preco_calculado": 1425.60,
      "desconto": 0,
      "preco_final": 1425.60,
      "fatores": {
        "seguidores": 1.15,
        "engajamento": 0.96,
        "nicho": 1.20,
        "volume": 1.00
      },
      "cpm_estimado": 0.15,
      "cpm_meta_ads": 18.00,
      "status": "gerada",
      "data_criacao": "2026-05-18T14:30:00"
    }
  ]
}
```

---

### GET /cotacoes/:id
Retorna cotacao completa com breakdown.

---

### POST /cotacoes
Salva uma nova cotacao.

**Request Body:**
```json
{
  "perfil_id": 1,
  "pacote_id": 2,
  "cliente_id": 1,
  "preco_calculado": 1425.60,
  "desconto": 0,
  "desconto_pct": 0,
  "motivo_desconto": null,
  "preco_final": 1425.60,
  "fator_seguidores": 1.15,
  "fator_engajamento": 0.96,
  "fator_nicho": 1.20,
  "fator_volume": 1.00,
  "volume_meses": 1,
  "cpm_estimado": 0.15,
  "cpm_meta_ads": 18.00,
  "status": "gerada"
}
```

**Response 201:** Objeto `cotacao` salvo.
**Response 400:** Validacao (perfil_id/pacote_id invalidos, precos negativos).

---

### PATCH /cotacoes/:id
Atualiza parcialmente (status, desconto).

**Request Body:**
```json
{
  "status": "fechada",
  "desconto": 200.00,
  "preco_final": 1225.60,
  "motivo_desconto": "Fechamento trimestral"
}
```

**Response 200:** Objeto `cotacao` atualizado.

---

### DELETE /cotacoes/:id
Remove cotacao do historico (hard delete).

**Response 200:** `{ "sucesso": true, "mensagem": "Cotacao removida" }`

---

## 5. CALCULADORA (CORE)

### POST /api/calculate
Endpoint central. Recebe `perfil_id` + `pacote_id` + opcionais, retorna preco calculado com breakdown completo.

**Request Body:**
```json
{
  "perfil_id": 1,
  "pacote_id": 2,
  "volume_meses": 3,
  "desconto_pct": 0
}
```

**Response 200:**
```json
{
  "preco_sugerido": 1425.60,
  "preco_volume_total": 4276.80,
  "breakdown": {
    "preco_base": 990.00,
    "fator_seguidores": { "valor": 1.15, "categoria": "690K seguidores", "explicacao": "Perfil acima de 500K aplica fator 1.15" },
    "fator_engajamento": { "valor": 0.96, "categoria": "3.2% engagement", "explicacao": "Engajamento abaixo de 3.5% reduz levemente o fator" },
    "fator_nicho": { "valor": 1.20, "categoria": "lifestyle", "explicacao": "Nicho lifestyle/autoridade tem maior influencia — fator 1.20" },
    "fator_volume": { "valor": 0.85, "categoria": "3 meses", "explicacao": "3 meses — 15% de desconto por volume" }
  },
  "comparativo_cpm": {
    "cpm_publiprice": 0.15,
    "cpm_meta_ads_medio": 18.00,
    "cpm_meta_ads_min": 15.00,
    "cpm_meta_ads_max": 25.00,
    "economia_pct": 99.17,
    "frase_venda": "Anuncio no Meta Ads custa 120x mais caro por mil impressoes."
  },
  "alcance_estimado": {
    "por_post": 185000,
    "total_pacote": 555000,
    "impressoes_estimadas": 925000
  },
  "validade_proposta": "7 dias"
}
```

**Response 400:**
```json
{
  "erro": true,
  "mensagem": "perfil_id invalido ou perfil desativado",
  "codigo": 400
}
```

---

## 6. EXPORTACAO

### POST /api/export/proposta
Gera texto formatado da proposta pronto para copiar.

**Request Body:**
```json
{
  "cotacao_id": 1,
  "formato": "whatsapp"
}
```

**Response 200:**
```json
{
  "texto": "📊 *Proposta PubliPrice — Lucas Tigre*\n\n🏨 Hotel: Grand Hotel Ponta Negra\n📱 Perfil: @lucastigrereal (690K)\n📦 Pacote: Growth — 3 collabs + SEOgram\n💰 Investimento: R$ 1.425,60/mês\n\n📈 CPM estimado: R$0,15 vs R$18,00 Meta Ads\n🔽 99% mais barato que anúncios\n\n📩 Validade: 7 dias.\nDM aberta pra dúvidas!",
  "copiado_em": "2026-05-18T14:31:00"
}
```

Formatos aceitos: `whatsapp`, `email`, `dm`, `markdown`.

---

## 7. RESUMO / DASHBOARD

### GET /api/dashboard
Retorna KPIs do historico.

**Response 200:**
```json
{
  "total_cotacoes": 47,
  "total_fechadas": 18,
  "total_perdidas": 9,
  "taxa_fechamento_pct": 38.3,
  "valor_total_cotado": 89650.40,
  "valor_total_fechado": 34420.00,
  "ticket_medio": 1912.22,
  "perfil_top": {
    "handle": "oinatalrn",
    "fechadas": 7
  }
}
```

---

## 8. CODIGOS DE ERRO

| HTTP | Significado |
|---|---|
| 200 | Sucesso |
| 201 | Criado |
| 400 | Validacao falhou (dados invalidos) |
| 404 | Recurso nao encontrado |
| 409 | Conflito (handle/campo unico duplicado) |
| 422 | Entidade nao processavel (ex: DELETE de perfil com cotacoes ativas) |
| 500 | Erro interno do servidor |

---

## 9. FORMULA DE PRECIFICACAO

```
preco_final = preco_base_pacote
            * fator_seguidores
            * fator_engajamento
            * fator_nicho
            * fator_volume
```

| Fator | Faixa | Multiplicador |
|---|---|---|
| **Seguidores** | < 100K | 0.85 |
| | 100K – 300K | 1.00 |
| | 300K – 500K | 1.10 |
| | 500K – 700K | 1.15 |
| | > 700K | 1.25 |
| **Engajamento** | < 2.0% | 0.85 |
| | 2.0% – 3.5% | 0.96 |
| | 3.5% – 5.0% | 1.05 |
| | > 5.0% | 1.20 |
| **Nicho** | Turismo | 1.00 |
| | Gastronomia | 0.90 |
| | Familia | 1.10 |
| | Lifestyle | 1.20 |
| **Volume** | 1 mes | 1.00 |
| | 2-3 meses | 0.85 |
| | 4-6 meses | 0.75 |
| | 7-12 meses | 0.65 |

---

## 10. CONFIGURACAO (GET/PUT /api/config)

Arquivo `config/precificacao.yaml` exposto via API para ajuste de fatores sem tocar codigo.

```json
{
  "fatores_seguidores": [
    { "min": 0,     "max": 100000,  "fator": 0.85 },
    { "min": 100001, "max": 300000, "fator": 1.00 },
    { "min": 300001, "max": 500000, "fator": 1.10 },
    { "min": 500001, "max": 700000, "fator": 1.15 },
    { "min": 700001, "max": 999999999, "fator": 1.25 }
  ],
  "fatores_nicho": {
    "turismo": 1.00,
    "gastronomia": 0.90,
    "familia": 1.10,
    "lifestyle": 1.20
  },
  "cpm_meta_ads_padrao": 18.00,
  "validade_proposta_dias": 7
}
```
