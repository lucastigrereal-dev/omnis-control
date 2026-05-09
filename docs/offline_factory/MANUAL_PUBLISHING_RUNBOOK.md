# Manual Publishing Runbook

**Versao:** P1.8 | **Para:** Lucas (operador)

Como publicar manualmente usando os pacotes do OMNIS sem OAuth, sem bot, sem risco de conta.

---

## Prerequisito

Ter um pacote gerado com status `partial` ou `ready`:

```powershell
python jarvis.py offline package-carousel <queue_id>
python jarvis.py offline list
python jarvis.py offline show <package_id>
```

---

## Carrossel (Instagram Feed)

1. Abrir a pasta do pacote: `exports/offline_factory/<package_id>/`
2. Ler o `README.md` para entender o contexto
3. Abrir `caption.md` — copiar o texto completo da legenda
4. Abrir `slides_outline.md` — ver a estrutura dos slides
5. Abrir `visual_brief.md` — ver a direcao visual
6. Abrir `publishing_checklist.md` — conferir cada item antes de postar
7. Montar os slides no seu editor (Canva, Illustrator, Photoshop, etc.)
8. Colar a legenda no Instagram
9. Conferir hashtags (max 30, relevantes ao conteudo)
10. Publicar manualmente pelo app do Instagram
11. (Futuro P2.3) Registrar publicacao no OMNIS

---

## Reels (Instagram Reels)

1. Abrir a pasta do pacote: `exports/offline_factory/<package_id>/`
2. Ler o `README.md`
3. Abrir `script.md` — ver o roteiro completo
4. Abrir `shot_list.md` — ver a lista de cenas
5. Abrir `voiceover.md` — ver o guia de locucao
6. Abrir `editing_notes.md` — ver instrucoes de edicao
7. Gravar o video seguindo o script e shot list
8. Editar conforme `editing_notes.md` (qualquer editor de video)
9. Abrir `caption.md` — copiar a legenda
10. Publicar no Instagram como Reels
11. (Futuro P2.3) Registrar publicacao no OMNIS

---

## Post Simples (Feed ou Stories)

1. Abrir a pasta do pacote: `exports/offline_factory/<package_id>/`
2. Ler o `README.md`
3. Abrir `caption.md` — copiar a legenda
4. Abrir `hashtags.md` — conferir as hashtags
5. Abrir `cta.md` — confirmar o call-to-action
6. Abrir `publishing_checklist.md` — conferir cada item
7. Selecionar ou preparar a imagem/video do post
8. Publicar manualmente no Instagram
9. (Futuro P2.3) Registrar publicacao no OMNIS

---

## Validacao antes de publicar

Sempre validar o pacote antes de postar:

```powershell
python jarvis.py offline validate <package_id>
```

Score >= 70: pode publicar.
Score < 70: revisar os checks falhados antes de postar.

---

## Export para colaborador (editor, social media)

Para enviar o pacote para um editor ou assistente:

```powershell
python jarvis.py offline zip <package_id>
```

O ZIP e gerado em `exports/offline_factory_zips/`. Pode ser enviado por WhatsApp, email ou Drive.

---

## O que o OMNIS NAO faz automaticamente (ainda)

- NAO posta sozinho (OAuth congelado por decisao estrategica)
- NAO conecta contas (seguranca)
- NAO agenda via Meta API
- NAO processa pagamento de publi

Isso e intencional. O OMNIS e a fabrica. Voce e o operador que transporta.
