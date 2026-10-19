# Carrossel Tweet

Uma skill para o **Claude Code** e para o **Codex** que cria carrosséis de Instagram no formato "print de tweet": você conta a ideia, a IA escreve os 10 cards no seu jeito de falar, gera as imagens prontas (1080x1350) e ainda entrega a legenda.

![Exemplo](examples/saida-exemplo/card-01.png)

## Instalar (uma linha)

**Windows** (abra o PowerShell e cole):

```powershell
irm https://raw.githubusercontent.com/marcusforti/carrossel-tweet/main/install.ps1 | iex
```

**Mac ou Linux** (abra o Terminal e cole):

```bash
curl -fsSL https://raw.githubusercontent.com/marcusforti/carrossel-tweet/main/install.sh | bash
```

O instalador copia a skill para `~/.claude/skills/` e `~/.codex/skills/` e instala o Pillow (a biblioteca de imagem do Python). Você precisa ter o **Python 3** instalado ([python.org](https://www.python.org/downloads/)).

## Usar

Abra o Claude Code (ou o Codex) em qualquer pasta e peça, do seu jeito:

> crie um carrossel tweet sobre por que postar todo dia não faz ninguém lembrar de você

Na primeira vez, a IA pergunta seu nome, seu @, onde está sua foto, seu nicho, o que a pessoa deve fazer no fim e se você quer fundo preto ou branco. Depois disso, ela guarda o seu perfil e só pergunta o tema.

Você recebe:
- os cards `card-01.png` a `card-10.png` e um `.zip` com todos, na ordem de postagem;
- a legenda pronta para colar.

Também funciona mandando um texto seu ou a transcrição de um vídeo: "transforma esse texto num carrossel tweet".

## O que tem aqui

| Arquivo | Para que serve |
|---|---|
| `SKILL.md` | O método: perguntas, estrutura dos 10 cards, regras de copy e checklist |
| `scripts/render.py` | Gera as imagens a partir de um JSON (dá para usar sozinho: `python scripts/render.py meu.json`) |
| `examples/` | Um carrossel de exemplo completo |
| `install.ps1` / `install.sh` | Instaladores |

## Créditos

Criado por **Marcus Forti**. Licença MIT; créditos e avisos no arquivo `LICENSE`.
