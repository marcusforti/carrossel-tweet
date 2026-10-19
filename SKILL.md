---
name: carrossel-tweet
description: Cria carrosséis de Instagram no formato "print de tweet" (cards 1080x1350 com foto, nome, selo e texto), do roteiro à imagem pronta e à legenda. Use quando a pessoa pedir "carrossel", "carrossel estilo tweet/Twitter/X", "post em formato de tweet" ou quiser transformar uma ideia, um texto ou uma transcrição em carrossel.
license: MIT
metadata:
  author: Marcus Forti
  version: "1.0"
---

# Carrossel Tweet

Você vai transformar uma ideia em um carrossel de Instagram que parece uma sequência de tweets: fundo liso, foto redonda, nome com selo, @ e um texto curto por card. O formato funciona porque parece conversa, não anúncio. Por isso a copy precisa soar como gente, e não como IA.

O trabalho tem quatro etapas: **entender a pessoa → escrever → renderizar → entregar com legenda**. Não pule etapas.

## 1. Antes de escrever: as perguntas

Na primeira vez, pergunte tudo numa mensagem só, em texto livre (sem botões), e espere a resposta. Se a pessoa já respondeu algo no pedido, só confirme.

1. **Seu nome e @** como aparecem no Instagram.
2. **Sua foto de perfil:** o caminho do arquivo no computador. Sem foto, o card sai com um círculo cinza.
3. **Seu nicho e para quem você fala** (em uma frase).
4. **O tema do carrossel.** Pode ser só a ideia ("constância"), um texto seu ou a transcrição de um vídeo/áudio para eu adaptar.
5. **O que a pessoa deve fazer no fim:** comentar uma palavra, salvar, mandar para alguém, ir para a bio, chamar no direct.
6. **Fundo preto ou branco?** E se quiser uma cor de destaque (padrão: âmbar no preto, azul no branco).

Guarde as respostas de 1, 2, 3 e 6 num arquivo `perfil.json` ao lado dos carrosséis, para não perguntar de novo da próxima vez.

## 2. A estrutura: 10 cards

Cada card é um "tweet". Um pensamento por card. A sequência segue AIDA, mas com uma regra que vale mais que todas: **nunca pare na provocação.**

| Card | Função | O que vai nele |
|---|---|---|
| 1 | **Gancho** | Uma frase que para o dedo. Curta. Só ela no card. |
| 2 | **Desarme** | Baixa a guarda: "calma, não é bem isso", "deixa eu explicar". Cria a vontade de seguir. |
| 3 e 4 | **Problema** | A cena que o leitor vive e não sabe nomear. Concreta, com detalhe. |
| 5 a 7 | **Mecanismo** | O porquê. A explicação que transforma a provocação em "faz sentido". Aqui mora o valor. |
| 8 e 9 | **Nova verdade** | A tese reformulada, um exemplo real, o "então o certo é...". |
| 10 | **Ação** | O CTA da pergunta 5, com bloco destacado. |

Para 6 a 8 cards, encolha o meio (problema e mecanismo), nunca o gancho e o CTA.

### A regra que separa carrossel bom de carrossel "que besteira"

Toda provocação precisa de quatro partes: **a crença comum → a virada → o mecanismo → a nova verdade.** Sem o mecanismo, o leitor pensa "que besteira" e sai. Com o mecanismo, ele pensa "como assim?" e lê até o fim.

- Errado: "Postar todo dia não funciona." (e passa para o próximo assunto)
- Certo: "Postar todo dia não funciona... porque o seguidor lembra de ideias, não de frequência. Quando cada post é um ângulo da mesma ideia, ele te reconhece antes de ler o seu nome."

### Ganchos que funcionam (card 1)

Prefira o gancho humano ao gancho de manchete:

- **Cena:** "Ontem eu recusei um cliente de 3 mil. Já explico."
- **Confissão com número:** "Eu postei todo dia por 90 dias. E perdi seguidor."
- **Coragem de dizer:** "Ninguém no meu nicho tem coragem de falar isso, então eu falo."
- **Contradição:** "Cobrar barato é desonesto."

Proibido no gancho: CAIXA ALTA gritando, "🚨 PARE TUDO", promessa vazia ("o segredo que vai mudar sua vida"), pergunta genérica ("você sabia que...?").

## 3. Regras de copy (para não ter cara de IA)

- **Primeira pessoa.** "Eu", "comigo", "no meu caso". Carrossel tweet é opinião de alguém, não manual.
- **Frases curtas.** Até umas 12 palavras. Quebra de linha entre ideias.
- **Zero travessão (— ou –).** Use vírgula, ponto ou quebra de linha.
- **Nada de "regra de três" automática** ("rápido, simples e eficaz"). Se listar, que seja porque precisa.
- **Detalhe concreto vence adjetivo.** "Três da manhã refazendo a conta" vence "momentos difíceis".
- **Pode ter bagunça humana:** "calma", "kkk", "sério", "já explico".
- **Sem emoji no meio do texto** e sem hashtag nos cards. Para listas, use `•` ou `1.`, `2.`, `3.`.
- **Varie o CTA** entre carrosséis. Comentar uma palavra, salvar, mandar para alguém: compartilhar e salvar costumam render mais alcance que comentar.
- **Não invente fato da pessoa.** Número, história e resultado só se ela disse. Na dúvida, pergunte.

Teste final de cada card: *se eu tirar o nome do autor, qualquer pessoa do nicho poderia ter escrito isso?* Se sim, ainda está genérico. Reescreva com a cena, a opinião ou o número dela.

## 4. Renderizar

Monte um JSON e rode o script desta skill (`scripts/render.py`, ao lado deste arquivo):

```json
{
  "nome": "Nome da Pessoa",
  "handle": "@perfil",
  "foto": "C:/caminho/foto.jpg",
  "tema": "escuro",
  "destaque": "#FFB020",
  "saida": "01-slug-do-tema",
  "cards": [
    {"texto": "Gancho curto.", "destaques": ["curto"]},
    {"texto": "Primeiro parágrafo.\n\nSegundo parágrafo.", "destaques": []},
    {"texto": "Pergunta final?", "destaques": ["final"], "cta": "Comenta PALAVRA", "rodape": "que eu te mando no direct."}
  ]
}
```

```bash
python scripts/render.py caminho/do/carrossel.json
```

Ele gera `card-01.png` até `card-NN.png` (1080x1350) e um `.zip` com todos, na pasta `saida`.

Detalhes do visual (o script já faz, não reinvente):

- **Mesmo layout em todos os cards:** foto, nome, selo, @ e texto, centralizados na vertical. O card 1 não muda de layout; ele se destaca pelo texto.
- **Sem linha separadora,** sem horário, sem curtidas, sem número de página.
- **Destaques:** 1 palavra por card (no máximo 2 ou 3), a que carrega a tensão da frase: o número, o verbo forte, a palavra da virada. Nunca artigo ou preposição.
- **Bloco de CTA só no último card** (campo `cta`), com o `rodape` menor embaixo.
- **Letra se ajusta sozinha:** se o texto for longo, o tamanho diminui até caber com respiro. Se ficar pequeno demais, divida em dois cards.
- **Símbolos:** o script troca de fonte por caractere quando a principal não tem o símbolo, então ✓, → e ★ não viram quadradinho. Mesmo assim, evite emoji colorido (sai em preto e branco).
- **Ritmo de feed:** quem posta vários carrosséis pode alternar preto e branco a cada lote, para o perfil não ficar monótono.

Depois de renderizar, **abra pelo menos o card 1, um do meio e o último** para conferir se nada estourou, se a foto está bem recortada e se o destaque caiu na palavra certa.

## 5. Entregar

Entregue três coisas:

1. **A pasta e o .zip** com os cards, na ordem de postagem.
2. **A legenda pronta**, no mesmo tom do carrossel:
   - abre com uma cena ou frase que complementa o card 1 (não repete);
   - 3 a 6 parágrafos curtos, em primeira pessoa;
   - fecha com o mesmo CTA do card 10, com outras palavras;
   - 3 a 5 hashtags no fim, do nicho, sem exagero.
3. **Uma frase** perguntando se quer ajustar algum card específico.

Ao ajustar: mude só o que foi pedido, no card pedido. Fonte, cores, tamanho do cabeçalho e layout ficam iguais aos outros cards.

## Checklist antes de entregar

- [ ] Fiz as perguntas (ou confirmei o perfil salvo)?
- [ ] O card 1 tem só o gancho e para o dedo?
- [ ] Existe mecanismo, ou o carrossel parou na provocação?
- [ ] Zero travessão, zero regra de três automática, tudo em primeira pessoa?
- [ ] Nenhum fato inventado?
- [ ] Último card tem bloco de CTA, e o CTA é diferente do último carrossel?
- [ ] Conferi o card 1, um do meio e o último depois de renderizar?
- [ ] Entreguei pasta, .zip e legenda?
