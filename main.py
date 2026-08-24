# Colagem Inteligente - versão Android (Kivy)
import os
import math
import tempfile

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty
from kivy.core.window import Window
from kivy.clock import Clock

from PIL import Image, ImageOps, ImageDraw

# ── permissões / storage no Android ─────────────────────────────
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False


def pasta_saida():
    if ANDROID:
        base = os.path.join(primary_external_storage_path(), 'Pictures', 'ColagemInteligente')
    else:
        base = os.path.join(os.path.expanduser('~'), 'ColagemInteligente')
    os.makedirs(base, exist_ok=True)
    return base


def gerar_nome_unico(pasta, base='colagem', ext='.jpg'):
    idx = 1
    while True:
        nome = f'{base}_{idx}{ext}'
        caminho = os.path.join(pasta, nome)
        if not os.path.exists(caminho):
            return caminho
        idx += 1


# ── lógica de colagem (portada do script desktop, é PIL puro) ───

def escolher_layout(qtd):
    layouts = {
        1: (1, 1), 2: (1, 2), 3: (1, 3), 4: (2, 2),
        5: (2, 3), 6: (2, 3), 7: (3, 3), 8: (3, 3),
        9: (3, 3), 10: (3, 4), 11: (3, 4), 12: (3, 4),
    }
    if qtd in layouts:
        return layouts[qtd]
    cols = math.ceil(math.sqrt(qtd))
    return math.ceil(qtd / cols), cols


def abrir_imagem(caminho):
    img = Image.open(caminho)
    img = ImageOps.exif_transpose(img)
    if img.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert('RGB')


def resize_fit(img, box_w, box_h):
    """Preenche box_w x box_h cortando o excesso (crop central)."""
    if box_w < 1 or box_h < 1:
        return Image.new('RGB', (max(1, box_w), max(1, box_h)), (200, 200, 200))
    scale = max(box_w / img.width, box_h / img.height)
    nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - box_w) // 2
    top = (nh - box_h) // 2
    return resized.crop((left, top, left + box_w, top + box_h))


def montar_colagem(caminhos, gap=10, radius=0, bg_color=(255, 255, 255), largura_total=1600):
    """Gera a colagem em grade e devolve o objeto PIL.Image."""
    imagens = [abrir_imagem(c) for c in caminhos]
    qtd = len(imagens)
    rows, cols = escolher_layout(qtd)

    avg_ratio = sum(im.width / im.height for im in imagens) / qtd
    cell_w = (largura_total - gap * (cols + 1)) // cols
    cell_h = int(cell_w / avg_ratio)

    total_w = cell_w * cols + gap * (cols + 1)
    total_h = cell_h * rows + gap * (rows + 1)

    colagem = Image.new('RGB', (total_w, total_h), bg_color)

    for i, img in enumerate(imagens):
        r, c = divmod(i, cols)
        x = gap + c * (cell_w + gap)
        y = gap + r * (cell_h + gap)

        fitted = resize_fit(img, cell_w, cell_h)

        if radius > 0:
            mask = Image.new('L', (cell_w, cell_h), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, cell_w, cell_h), radius=radius, fill=255)
            fitted = fitted.convert('RGBA')
            fitted.putalpha(mask)
            colagem.paste(fitted, (x, y), fitted)
        else:
            colagem.paste(fitted, (x, y))

    return colagem


# ── Interface Kivy ────────────────────────────────────────────

class ColagemApp(App):
    def build(self):
        self.title = 'Colagem Inteligente'
        self.imagens_selecionadas = []
        self.bg_color_rgb = (255, 255, 255)
        self.ultima_colagem_path = None

        if ANDROID:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])

        root = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # Barra superior
        top = BoxLayout(size_hint_y=None, height=48, spacing=8)
        top.add_widget(Button(text='📁 Selecionar Fotos', on_release=self.abrir_seletor))
        top.add_widget(Button(text='🎨 Cor de fundo', on_release=self.abrir_cor))
        root.add_widget(top)

        self.lbl_status = Label(text='Nenhuma foto selecionada', size_hint_y=None, height=28)
        root.add_widget(self.lbl_status)

        # Preview
        self.preview = KivyImage(allow_stretch=True, keep_ratio=True)
        root.add_widget(self.preview)

        # Controles: gap e radius
        controls = GridLayout(cols=2, size_hint_y=None, height=100, spacing=8)
        controls.add_widget(Label(text='Espaçamento'))
        self.slider_gap = Slider(min=0, max=40, value=10)
        self.slider_gap.bind(value=lambda *a: self.atualizar_preview())
        controls.add_widget(self.slider_gap)

        controls.add_widget(Label(text='Cantos arred.'))
        self.slider_radius = Slider(min=0, max=60, value=0)
        self.slider_radius.bind(value=lambda *a: self.atualizar_preview())
        controls.add_widget(self.slider_radius)
        root.add_widget(controls)

        # Botão salvar
        self.btn_salvar = Button(text='💾 Salvar Colagem', size_hint_y=None, height=52,
                                  disabled=True, on_release=self.salvar_colagem)
        root.add_widget(self.btn_salvar)

        return root

    # ── seleção de fotos ──
    def abrir_seletor(self, *a):
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg', '*.webp'],
                                       multiselect=True)
        content.add_widget(chooser)

        botoes = BoxLayout(size_hint_y=None, height=48, spacing=8)
        popup = Popup(title='Selecione as fotos', content=content, size_hint=(0.9, 0.9))

        def confirmar(*a):
            if chooser.selection:
                self.imagens_selecionadas = list(chooser.selection)
                self.lbl_status.text = f'{len(self.imagens_selecionadas)} foto(s) selecionada(s)'
                self.btn_salvar.disabled = False
                self.atualizar_preview()
            popup.dismiss()

        botoes.add_widget(Button(text='Cancelar', on_release=popup.dismiss))
        botoes.add_widget(Button(text='Confirmar', on_release=confirmar))
        content.add_widget(botoes)
        popup.open()

    # ── seletor de cor ──
    def abrir_cor(self, *a):
        picker = ColorPicker(color=(1, 1, 1, 1))
        popup = Popup(title='Cor de fundo', content=picker, size_hint=(0.9, 0.9))

        def fechar(*a):
            r, g, b, _ = picker.color
            self.bg_color_rgb = (int(r * 255), int(g * 255), int(b * 255))
            self.atualizar_preview()
            popup.dismiss()

        picker.bind(color=lambda *a: None)
        box = BoxLayout(orientation='vertical')
        box.add_widget(picker)
        box.add_widget(Button(text='Aplicar', size_hint_y=None, height=48, on_release=fechar))
        popup.content = box
        popup.open()

    # ── preview (debounce simples) ──
    def atualizar_preview(self, *a):
        if not self.imagens_selecionadas:
            return
        Clock.unschedule(self._gerar_preview)
        Clock.schedule_once(self._gerar_preview, 0.3)

    def _gerar_preview(self, *a):
        try:
            colagem = montar_colagem(
                self.imagens_selecionadas,
                gap=int(self.slider_gap.value),
                radius=int(self.slider_radius.value),
                bg_color=self.bg_color_rgb,
                largura_total=1000,
            )
            tmp_path = os.path.join(tempfile.gettempdir(), '_preview_colagem.png')
            colagem.save(tmp_path)
            self.preview.source = tmp_path
            self.preview.reload()
        except Exception as e:
            self.lbl_status.text = f'Erro ao gerar preview: {e}'

    # ── salvar arquivo final ──
    def salvar_colagem(self, *a):
        try:
            colagem = montar_colagem(
                self.imagens_selecionadas,
                gap=int(self.slider_gap.value),
                radius=int(self.slider_radius.value),
                bg_color=self.bg_color_rgb,
                largura_total=2400,  # resolução final maior
            )
            destino = gerar_nome_unico(pasta_saida())
            colagem.save(destino, quality=92)
            self.ultima_colagem_path = destino
            self.lbl_status.text = f'Salvo em: {destino}'
        except Exception as e:
            self.lbl_status.text = f'Erro ao salvar: {e}'


if __name__ == '__main__':
    ColagemApp().run()
