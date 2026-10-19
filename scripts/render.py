"""Gera os cards de um carrossel estilo tweet (1080x1350) a partir de um JSON.

Uso:
    python render.py carrossel.json

Formato do JSON (veja examples/exemplo.json):
{
  "nome": "Seu Nome",
  "handle": "@seuarroba",
  "foto": "minha-foto.jpg",          # caminho relativo ao JSON ou absoluto
  "tema": "escuro",                  # "escuro" (fundo preto) ou "claro" (fundo branco)
  "destaque": "#FFB020",             # opcional: cor das palavras destacadas e do bloco de CTA
  "saida": "saida/meu-carrossel",    # opcional: pasta de saída (padrão: ao lado do JSON)
  "cards": [
    {"texto": "Primeira frase.\n\nSegundo parágrafo.", "destaques": ["frase"]},
    ...
    {"texto": "Último card.", "cta": "Comenta PALAVRA", "rodape": "que eu te mando no direct."}
  ]
}

Gera card-01.png, card-02.png... e um .zip com todos.
"""
import json
import os
import platform
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
MARGEM = 80
AVATAR = 100
GAP = 32
RESPIRO = 70
TAM_TEXTO = 54
TAM_MINIMO = 38
ALTURA_LINHA = 1.37

TEMAS = {
    "escuro": {"fundo": "#000000", "texto": "#E7E9EA", "handle": "#71767B", "selo": "#1D9BF0", "destaque": "#FFB020"},
    "claro": {"fundo": "#FFFFFF", "texto": "#0F1419", "handle": "#536471", "selo": "#1D9BF0", "destaque": "#1D9BF0"},
}

# Fontes por sistema: a primeira que existir é usada. A "simbolos" cobre caracteres que a principal não tem.
FONTES = {
    "Windows": {
        "regular": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
        "negrito": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
        "simbolos": ["C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/ARIALUNI.TTF"],
    },
    "Darwin": {
        "regular": ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"],
        "negrito": ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
        "simbolos": ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"],
    },
    "Linux": {
        "regular": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"],
        "negrito": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"],
        "simbolos": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    },
}


def achar_fonte(tipo):
    pasta_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
    local = {"regular": "regular.ttf", "negrito": "negrito.ttf", "simbolos": "simbolos.ttf"}[tipo]
    candidatos = [os.path.join(pasta_local, local)] + FONTES.get(platform.system(), FONTES["Linux"])[tipo]
    for c in candidatos:
        if os.path.exists(c):
            # Helvetica.ttc: índice 1 costuma ser o negrito
            idx = 1 if (tipo == "negrito" and c.endswith("Helvetica.ttc")) else 0
            return c, idx
    return None, 0


class Fonte:
    """Fonte com fallback por caractere: o que a principal não desenha (tofu) sai na de símbolos."""

    def __init__(self, tipo, tamanho):
        caminho, idx = achar_fonte(tipo)
        self.principal = ImageFont.truetype(caminho, tamanho, index=idx) if caminho else ImageFont.load_default(size=tamanho)
        caminho_s, idx_s = achar_fonte("simbolos")
        self.simbolos = ImageFont.truetype(caminho_s, tamanho, index=idx_s) if caminho_s else self.principal
        self._cache = {}

    def para(self, ch):
        if ch in self._cache:
            return self._cache[ch]
        f = self.principal
        if ord(ch) > 0x2000 and self.simbolos is not self.principal:
            try:
                tofu = self.principal.getmask("\uFFFF").getbbox()
                if self.principal.getmask(ch).getbbox() == tofu:
                    f = self.simbolos
            except Exception:
                f = self.simbolos
        self._cache[ch] = f
        return f

    def largura(self, texto):
        return sum(self.para(ch).getlength(ch) for ch in texto)

    def desenhar(self, draw, xy, texto, cor):
        x, y = xy
        for ch in texto:
            f = self.para(ch)
            draw.text((x, y), ch, font=f, fill=cor)
            x += f.getlength(ch)


def avatar_redondo(caminho, tamanho, ss=4):
    grande = tamanho * ss
    im = Image.open(caminho).convert("RGBA")
    w, h = im.size
    lado = min(w, h)
    # Recorte quadrado puxado para cima, onde costuma estar o rosto
    topo = max(0, int((h - lado) * 0.2))
    im = im.crop(((w - lado) // 2, topo, (w - lado) // 2 + lado, topo + lado)).resize((grande, grande), Image.LANCZOS)
    mascara = Image.new("L", (grande, grande), 0)
    ImageDraw.Draw(mascara).ellipse((ss, ss, grande - 1 - ss, grande - 1 - ss), fill=255)
    im.putalpha(mascara)
    return im.resize((tamanho, tamanho), Image.LANCZOS)


def selo(img, x, y, cor, tam=32, ss=4):
    g = tam * ss
    s = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((ss, ss, g - 1 - ss, g - 1 - ss), fill=cor)
    lw = 3 * ss
    pts = [(8 * ss, 16 * ss), (14 * ss, 22 * ss), (24 * ss, 10 * ss)]
    d.line(pts, fill="white", width=lw, joint="curve")
    for cx, cy in pts:
        d.ellipse((cx - lw // 2, cy - lw // 2, cx + lw // 2, cy + lw // 2), fill="white")
    s = s.resize((tam, tam), Image.LANCZOS)
    img.paste(s, (int(x), int(y)), s)


def limpar(p):
    return p.lower().strip(".,!?;:\"'()…")


def quebrar(texto, fonte, largura_max):
    """Devolve linhas; cada linha é uma lista de palavras. Linha vazia = espaço entre parágrafos."""
    linhas = []
    paragrafos = texto.split("\n\n")
    for i, par in enumerate(paragrafos):
        for trecho in par.split("\n"):
            atual = []
            for palavra in trecho.split():
                teste = " ".join(atual + [palavra])
                if atual and fonte.largura(teste) > largura_max:
                    linhas.append(atual)
                    atual = [palavra]
                else:
                    atual.append(palavra)
            linhas.append(atual)
        if i < len(paragrafos) - 1:
            linhas.append([])
    return linhas


def medir_cta(cta, rodape, tam):
    if not cta:
        return None, 0
    f = Fonte("negrito", int(tam * 0.95))
    linhas = quebrar(cta, f, W - 2 * MARGEM - 2 * 50)
    alt_linha = int(f.principal.size * 1.3)
    altura = len(linhas) * alt_linha + 2 * 36
    if rodape:
        altura += 24 + int(tam * 0.75 * 1.4)
    return (f, linhas, alt_linha), altura


def ajustar(card):
    """Maior corpo de letra (até TAM_TEXTO) que cabe no card com respiro."""
    tam = TAM_TEXTO
    while True:
        f = Fonte("regular", tam)
        linhas = quebrar(card.get("texto", ""), f, W - 2 * MARGEM)
        alt = int(tam * ALTURA_LINHA)
        _, alt_cta = medir_cta(card.get("cta"), card.get("rodape"), tam)
        total = AVATAR + GAP + len(linhas) * alt + (GAP + alt_cta if alt_cta else 0)
        if total <= H - 2 * RESPIRO or tam <= TAM_MINIMO:
            return tam, f, linhas, alt, total
        tam -= 2


def gerar_card(cfg, card, img_avatar, destino):
    t = TEMAS[cfg.get("tema", "escuro")]
    cor_dest = cfg.get("destaque") or t["destaque"]
    img = Image.new("RGB", (W, H), t["fundo"])
    d = ImageDraw.Draw(img)
    tam, f, linhas, alt, total = ajustar(card)
    y = (H - total) // 2

    # Cabeçalho: avatar, nome, selo e @
    if img_avatar is not None:
        img.paste(img_avatar, (MARGEM, y), img_avatar)
    else:
        d.ellipse((MARGEM, y, MARGEM + AVATAR, y + AVATAR), fill=t["handle"])
    fn, fh = Fonte("negrito", 36), Fonte("regular", 28)
    xn = MARGEM + AVATAR + 20
    fn.desenhar(d, (xn, y + 10), cfg["nome"], t["texto"])
    selo(img, xn + fn.largura(cfg["nome"]) + 10, y + 14, t["selo"])
    fh.desenhar(d, (xn, y + 56), cfg["handle"], t["handle"])
    y += AVATAR + GAP

    # Texto, com as palavras de destaque na cor de acento
    destaques = {limpar(p) for p in card.get("destaques", [])}
    espaco = f.largura(" ")
    for linha in linhas:
        x = MARGEM
        for palavra in linha:
            f.desenhar(d, (x, y), palavra, cor_dest if limpar(palavra) in destaques else t["texto"])
            x += f.largura(palavra) + espaco
        y += alt

    # Bloco de CTA (só no card que tiver "cta")
    medida, _ = medir_cta(card.get("cta"), card.get("rodape"), tam)
    if medida:
        fc, lc, ac = medida
        y += GAP
        alt_bloco = len(lc) * ac + 72
        d.rounded_rectangle((MARGEM, y, W - MARGEM, y + alt_bloco), radius=28, fill=cor_dest)
        cor_txt = cfg.get("cor_texto_cta") or ("#000000" if cfg.get("tema", "escuro") == "escuro" else "#FFFFFF")
        yy = y + 36
        for linha in lc:
            s = " ".join(linha)
            fc.desenhar(d, ((W - fc.largura(s)) // 2, yy), s, cor_txt)
            yy += ac
        y += alt_bloco
        if card.get("rodape"):
            fr = Fonte("regular", int(tam * 0.75))
            fr.desenhar(d, ((W - fr.largura(card["rodape"])) // 2, y + 24), card["rodape"], t["handle"])

    img.save(destino, "PNG", optimize=True)


def main(caminho_json):
    base = os.path.dirname(os.path.abspath(caminho_json))
    with open(caminho_json, encoding="utf-8") as fp:
        cfg = json.load(fp)
    saida = os.path.join(base, cfg.get("saida") or os.path.splitext(os.path.basename(caminho_json))[0])
    os.makedirs(saida, exist_ok=True)

    foto = cfg.get("foto")
    img_avatar = None
    if foto:
        caminho_foto = foto if os.path.isabs(foto) else os.path.join(base, foto)
        if os.path.exists(caminho_foto):
            img_avatar = avatar_redondo(caminho_foto, AVATAR)
        else:
            print(f"Aviso: foto não encontrada ({caminho_foto}). Usando um círculo no lugar.")

    arquivos = []
    for i, card in enumerate(cfg["cards"], 1):
        destino = os.path.join(saida, f"card-{i:02d}.png")
        gerar_card(cfg, card, img_avatar, destino)
        arquivos.append(destino)

    with zipfile.ZipFile(os.path.join(saida, os.path.basename(saida) + ".zip"), "w") as z:
        for a in arquivos:
            z.write(a, arcname=os.path.basename(a))
    print(f"{len(arquivos)} cards em {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
