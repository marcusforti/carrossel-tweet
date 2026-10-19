"""Carrossel: app local para gerar carrosséis estilo tweet sem abrir o terminal.

Abre uma página em http://localhost:8765. Você digita os assuntos (um por linha), clica em Gerar,
e o agente (Codex por padrão, ou Claude Code) escreve a copy com a skill carrossel-tweet e gera os cards.
Cada carrossel fica em ~/Carrosseis/AAAA-MM-DD_assunto/ (card-01.png..., legenda.txt) e a pasta abre sozinha.

Uso: python app/server.py
Configuração opcional (variáveis de ambiente):
  CARROSSEL_MOTOR=codex|claude   qual agente usar (padrão: codex; também dá para trocar na página)
  CARROSSEL_HOME=<pasta>         onde salvar (padrão: ~/Carrosseis)
  CARROSSEL_PORTA=8765
  CARROSSEL_SEM_NAVEGADOR=1      não abre o navegador ao iniciar
"""
import base64
import datetime
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(APP)
RENDER = os.path.join(SKILL, "scripts", "render.py")
CASA = os.path.abspath(os.path.expanduser(os.environ.get("CARROSSEL_HOME") or "~/Carrosseis"))
PERFIL_DIR = os.path.join(CASA, "_perfil")
PERFIL = os.path.join(PERFIL_DIR, "perfil.json")
CONFIG = os.path.join(CASA, "_config.json")
PORTA = int(os.environ.get("CARROSSEL_PORTA") or 8765)
SISTEMA = platform.system()

os.makedirs(PERFIL_DIR, exist_ok=True)
JOBS = []
TRAVA = threading.Lock()


def ler_json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def gravar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def motor_atual():
    return os.environ.get("CARROSSEL_MOTOR") or ler_json(CONFIG, {}).get("motor") or "codex"


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return (t[:50].rstrip("-")) or "carrossel"


# ---------- localizar os agentes ----------

def achar_codex():
    c = shutil.which("codex")
    if c:
        return c
    candidatos = []
    if SISTEMA == "Darwin":
        candidatos += glob.glob("/Applications/Codex.app/Contents/Resources/**/codex", recursive=True)
        candidatos += glob.glob(os.path.expanduser("~/Applications/Codex.app/Contents/Resources/**/codex"), recursive=True)
        candidatos += ["/opt/homebrew/bin/codex", "/usr/local/bin/codex", os.path.expanduser("~/.local/bin/codex")]
    elif SISTEMA == "Linux":
        candidatos += [os.path.expanduser("~/.local/bin/codex")]
    elif SISTEMA == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        candidatos += [os.path.join(local, "Programs", "OpenAI", "Codex", "bin", "codex.exe"),
                       os.path.join(local, "Microsoft", "WindowsApps", "codex.exe")]
        candidatos += glob.glob(os.path.join(local, "Programs", "*Codex*", "**", "codex.exe"), recursive=True)
        candidatos += glob.glob(os.path.join(os.environ.get("APPDATA", ""), "npm", "codex.cmd"))
    for c in candidatos:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def achar_claude():
    return shutil.which("claude")


def status_motor():
    m = motor_atual()
    if m == "claude":
        b = achar_claude()
        return {"motor": "claude", "instalado": bool(b), "logado": bool(b), "mensagem": "" if b else "Claude Code não encontrado."}
    b = achar_codex()
    if not b:
        return {"motor": "codex", "instalado": False, "logado": False,
                "mensagem": "Falta instalar o Codex, o assistente que escreve os carrosséis. Clique no botão e espere a janela terminar."}
    try:
        r = subprocess.run([b, "login", "status"], capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        saida = (r.stdout + r.stderr).lower()
        logado = r.returncode == 0 and "not logged" not in saida
    except Exception:
        logado = False
    return {"motor": "codex", "instalado": True, "logado": logado,
            "mensagem": "" if logado else "Falta entrar com a sua conta do ChatGPT."}


def instalar_codex():
    """Abre uma janela rodando o instalador oficial do Codex CLI (não precisa de Node)."""
    if SISTEMA == "Windows":
        subprocess.Popen(["cmd", "/c", "start", "Instalando o Codex", "powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                          "-Command", "irm https://chatgpt.com/codex/install.ps1 | iex; Write-Host ''; Write-Host 'Pronto! Pode fechar esta janela e voltar ao Carrossel.'"])
    elif SISTEMA == "Darwin":
        subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "curl -fsSL https://chatgpt.com/codex/install.sh | sh; echo; echo Pronto! Pode fechar esta janela."'])
    else:
        subprocess.Popen(["sh", "-c", "curl -fsSL https://chatgpt.com/codex/install.sh | sh"])
    return True


def fazer_login():
    b = achar_codex()
    if not b:
        return False
    if SISTEMA == "Windows":
        subprocess.Popen(["cmd", "/c", "start", "Entrar no Codex", b, "login"])
    elif SISTEMA == "Darwin":
        subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "\\"{b}\\" login"'])
    else:
        subprocess.Popen([b, "login"])
    return True


# ---------- geração ----------

PROMPT = """Você vai criar UM carrossel estilo tweet para Instagram, sem fazer nenhuma pergunta (não há ninguém para responder).

1. Leia a skill em: {skill}
   e siga o método dela (estrutura de 10 cards, gancho, regras de copy, legenda).
2. Assunto do carrossel: "{assunto}"
   Autor: {nome} ({handle}). Nicho e contexto do autor: {nicho}
   Sobre o negócio do autor (fonte de verdade para tom de voz, histórias, provas e CTA; o que estiver marcado [confirmar] não é fato e não deve ser usado como fato):
   <<<
{negocio}
   >>>
   Escreva em português do Brasil, na voz do autor, em primeira pessoa. Não invente números, clientes ou fatos sobre o autor:
   use só os que aparecem acima. Se o perfil indicar uma chamada preferida (CTA), use-a no último card.
3. Crie o arquivo {json_path} neste formato:
   {{"nome": "{nome}", "handle": "{handle}", "foto": "{foto}", "tema": "{tema}", "saida": "{saida}",
     "cards": [{{"texto": "...", "destaques": ["..."]}}, ..., {{"texto": "...", "cta": "Comenta PALAVRA", "rodape": "..."}}]}}
   Use exatamente {n} cards.
4. Rode: "{python}" "{render}" "{json_path}"
5. Escreva a legenda pronta para postar em {legenda} (seguindo as regras de legenda da skill).
6. Confira que os arquivos card-01.png até card-{n:02d}.png existem em {saida}. Responda só "PRONTO" no final.
"""


def comando_motor(motor, prompt, pasta):
    if motor == "claude":
        return [achar_claude(), "-p", "--dangerously-skip-permissions"], prompt
    # Sandbox de escrita só na pasta do carrossel, sem pedir aprovação (não há ninguém olhando o terminal)
    return [achar_codex(), "exec", "--skip-git-repo-check", "-s", "workspace-write",
            "-c", 'approval_policy="never"', "-C", pasta, "-"], prompt


def rodar_job(job):
    perfil = ler_json(PERFIL, {})
    pasta = job["pasta"]
    os.makedirs(pasta, exist_ok=True)
    jp = os.path.join(pasta, "carrossel.json")
    prompt = PROMPT.format(
        skill=os.path.join(SKILL, "SKILL.md"), assunto=job["assunto"].replace('"', "'"),
        nome=perfil.get("nome", ""), handle=perfil.get("handle", ""), nicho=perfil.get("nicho") or "não informado",
        negocio=(perfil.get("negocio") or "(não preenchido)").replace("{", "(").replace("}", ")"),
        foto=(perfil.get("foto") or "").replace("\\", "/"), tema=job["tema"], saida=pasta.replace("\\", "/"),
        json_path=jp.replace("\\", "/"), n=job["cards"], python=sys.executable.replace("\\", "/"),
        render=RENDER.replace("\\", "/"), legenda=os.path.join(pasta, "legenda.txt").replace("\\", "/"))
    cmd, entrada = comando_motor(job["motor"], prompt, pasta)
    job["estado"] = "gerando"
    job["inicio"] = time.time()
    try:
        r = subprocess.run(cmd, input=entrada, cwd=pasta, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1200)
        with open(os.path.join(pasta, "_log.txt"), "w", encoding="utf-8") as f:
            f.write(r.stdout[-20000:] + "\n---\n" + r.stderr[-20000:])
    except Exception as e:
        job["erro"] = str(e)
    cards = sorted(glob.glob(os.path.join(pasta, "card-*.png")))
    if cards:
        job["estado"] = "pronto"
        abrir_pasta(pasta)
    else:
        job["estado"] = "erro"
        job.setdefault("erro", "O agente terminou sem gerar os cards. Veja o arquivo _log.txt na pasta.")
    job["fim"] = time.time()


def fila():
    while True:
        prox = None
        with TRAVA:
            if not any(j["estado"] == "gerando" for j in JOBS):
                prox = next((j for j in JOBS if j["estado"] == "na fila"), None)
                if prox:
                    prox["estado"] = "gerando"
        if prox:
            rodar_job(prox)
        time.sleep(1)


def abrir_pasta(pasta):
    try:
        if SISTEMA == "Windows":
            os.startfile(pasta)
        elif SISTEMA == "Darwin":
            subprocess.Popen(["open", pasta])
        else:
            subprocess.Popen(["xdg-open", pasta])
    except Exception:
        pass


def resultados():
    itens = []
    ocupadas = {j["pasta"] for j in JOBS if j["estado"] in ("na fila", "gerando")}
    for p in sorted(glob.glob(os.path.join(CASA, "20*")), reverse=True):
        if p in ocupadas:
            continue
        cards = sorted(glob.glob(os.path.join(p, "card-*.png")))
        if not cards:
            continue
        leg = os.path.join(p, "legenda.txt")
        itens.append({"pasta": p, "nome": os.path.basename(p),
                      "cards": [os.path.relpath(c, CASA).replace("\\", "/") for c in cards],
                      "legenda": open(leg, encoding="utf-8").read() if os.path.exists(leg) else ""})
    return itens[:30]


# ---------- servidor ----------

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def enviar(self, codigo, corpo, tipo="application/json; charset=utf-8"):
        if isinstance(corpo, (dict, list)):
            corpo = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        elif isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            with open(os.path.join(APP, "index.html"), encoding="utf-8") as f:
                return self.enviar(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/api/estado":
            perfil = ler_json(PERFIL, {})
            casa = CASA.replace(os.path.expanduser("~"), "~").replace("\\", "/")
            return self.enviar(200, {"perfil": perfil, "motor": status_motor(), "casa": casa,
                                     "jobs": [{k: v for k, v in j.items()} for j in JOBS],
                                     "resultados": resultados()})
        if u.path.startswith("/arquivo/"):
            rel = urllib.parse.unquote(u.path[len("/arquivo/"):])
            alvo = os.path.abspath(os.path.join(CASA, rel))
            if not alvo.startswith(CASA + os.sep) or not os.path.isfile(alvo):
                return self.enviar(404, {"erro": "não encontrado"})
            tipo = "image/png" if alvo.lower().endswith(".png") else "image/jpeg"
            with open(alvo, "rb") as f:
                return self.enviar(200, f.read(), tipo)
        self.enviar(404, {"erro": "não encontrado"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        d = self.corpo()
        if u.path == "/api/perfil":
            perfil = ler_json(PERFIL, {})
            perfil.update({k: d[k].strip() for k in ("nome", "handle", "nicho", "negocio") if isinstance(d.get(k), str)})
            if perfil.get("handle") and not perfil["handle"].startswith("@"):
                perfil["handle"] = "@" + perfil["handle"]
            if d.get("foto"):
                cab, dados = d["foto"].split(",", 1)
                ext = ".png" if "png" in cab else ".jpg"
                for velho in glob.glob(os.path.join(PERFIL_DIR, "foto.*")):
                    os.remove(velho)
                caminho = os.path.join(PERFIL_DIR, "foto" + ext)
                with open(caminho, "wb") as f:
                    f.write(base64.b64decode(dados))
                perfil["foto"] = caminho
            gravar_json(PERFIL, perfil)
            return self.enviar(200, {"ok": True, "perfil": perfil})
        if u.path == "/api/gerar":
            assuntos = [a.strip() for a in (d.get("assuntos") or "").splitlines() if a.strip()]
            if not assuntos:
                return self.enviar(400, {"erro": "Escreva pelo menos um assunto."})
            hoje = datetime.date.today().isoformat()
            with TRAVA:
                for a in assuntos:
                    pasta = os.path.join(CASA, f"{hoje}_{slug(a)}")
                    i = 2
                    while os.path.exists(pasta) or any(j["pasta"] == pasta for j in JOBS):
                        pasta = os.path.join(CASA, f"{hoje}_{slug(a)}-{i}")
                        i += 1
                    JOBS.append({"assunto": a, "pasta": pasta, "tema": d.get("tema") or "escuro",
                                 "cards": max(5, min(10, int(d.get("cards") or 10))), "motor": motor_atual(),
                                 "estado": "na fila"})
            return self.enviar(200, {"ok": True})
        if u.path == "/api/abrir":
            p = os.path.abspath(d.get("pasta") or CASA)
            if p.startswith(CASA):
                abrir_pasta(p)
            return self.enviar(200, {"ok": True})
        if u.path == "/api/login":
            return self.enviar(200, {"ok": fazer_login()})
        if u.path == "/api/instalar-codex":
            return self.enviar(200, {"ok": instalar_codex()})
        if u.path == "/api/motor":
            if d.get("motor") in ("codex", "claude"):
                cfg = ler_json(CONFIG, {})
                cfg["motor"] = d["motor"]
                gravar_json(CONFIG, cfg)
            return self.enviar(200, {"ok": True})
        self.enviar(404, {"erro": "não encontrado"})


def main():
    url = f"http://localhost:{PORTA}"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORTA), H)
    except OSError:
        # Já está rodando: só abre a página
        webbrowser.open(url)
        return
    threading.Thread(target=fila, daemon=True).start()
    print(f"Carrossel rodando em {url} (feche esta janela para desligar)")
    if not os.environ.get("CARROSSEL_SEM_NAVEGADOR"):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
