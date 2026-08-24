# Como gerar o APK

O código já está pronto e testado (a lógica de colagem foi validada). Falta só compilar,
o que precisa de Android SDK/NDK — algo que não roda em qualquer computador Windows
diretamente. Duas opções:

## Opção A — GitHub Actions (recomendado, mais fácil, grátis)

1. Crie um repositório novo no GitHub e suba esta pasta inteira (`colagem_kivy`).
2. Vá em **Actions** no repositório → o workflow "Build APK" vai rodar sozinho
   (ou clique em "Run workflow" para rodar na hora).
3. Espere ~15-20 minutos (a primeira vez demora mais, baixa o Android SDK/NDK).
4. Quando terminar, baixe o APK gerado em **Actions → build → Artifacts →
   colagem-inteligente-apk**.
5. Transfira o `.apk` pro celular (Google Drive, cabo USB, etc.) e instale
   (pode precisar ativar "instalar de fontes desconhecidas" nas configurações do Android).

Essa é a forma mais simples porque você não instala nada no seu PC — tudo roda
nos servidores do GitHub.

## Opção B — Localmente, via WSL (Windows Subsystem for Linux)

Buildozer só roda em Linux/Mac, então no Windows você precisa do WSL:

```
wsl --install
```

Depois, dentro do WSL (Ubuntu):

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
  pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev build-essential

pip install --upgrade buildozer cython==0.29.36

cd /caminho/para/colagem_kivy
buildozer -v android debug
```

O APK final aparece em `bin/*.apk`. A primeira compilação baixa uns 3-4 GB
(SDK + NDK) e pode levar 30-60 minutos, dependendo da internet.

## Testar no PC antes de compilar (opcional, mas recomendado)

Para conferir a interface sem esperar a compilação toda vez:

```bash
pip install kivy pillow
python main.py
```

Isso abre o app numa janela desktop — a lógica e o visual são os mesmos,
só o empacotamento final é que muda pro Android.

## Próximos passos (funcionalidades que ficaram de fora do MVP)

- Templates diferentes (hero_left, coluna, etc.)
- Zoom/arraste individual por foto
- Filtros (P&B, sépia, brilho)
- Marca d'água
- Tema claro/escuro

Se quiser, posso ir adicionando essas features de volta uma por uma.
