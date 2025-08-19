import os
import asyncio
import requests
import pyppeteer.chromium_downloader as cd
from pyppeteer import launch

# 1) Descobrir a última revisão disponível p/ Windows x64
def latest_win64_revision():
    url = "https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text.strip()

async def main():
    # 2) Apagar downloads antigos quebrados (opcional, mas recomendado)
    local_dir = os.path.expandvars(r"%LOCALAPPDATA%\pyppeteer\pyppeteer\local-chromium")
    if os.path.isdir(local_dir):
        # Se quiser, limpe a pasta inteira manualmente pelo Explorer
        pass

    # 3) Forçar a revisão para a mais recente disponível
    rev = latest_win64_revision()
    cd.REVISION = rev

    # 4) Baixar e obter o executável dessa revisão
    cd.download_chromium()  # baixa se não existir
    exe = cd.chromium_executable()

    # 5) Subir com essa revisão
    browser = await launch(executablePath=exe, headless=False)
    print(await browser.version())
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())