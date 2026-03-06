import os
import sys
import re
import json
import time
import random
import hashlib
import threading
import urllib.parse
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

import requests
import phonenumbers
from phonenumbers import carrier, geocoder
from faker import Faker
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

Window.size = (400, 700)
Window.clearcolor = get_color_from_hex('#0a0a0a')

COLORS = {
    'background': '#0a0a0a',
    'surface': '#1a1a1a',
    'primary': '#ff3333',
    'primary_dark': '#cc0000',
    'primary_light': '#ff6666',
    'text': '#ffffff',
    'text_secondary': '#aaaaaa',
    'success': '#00ff88',
    'error': '#ff3333',
    'warning': '#ffaa00'
}

OPERATORS_DB = {
    "901": "Билайн", "902": "Билайн", "903": "Билайн", "904": "Билайн", "905": "Билайн",
    "910": "МТС", "911": "МТС", "912": "МТС", "913": "МТС", "916": "МТС",
    "920": "Мегафон", "921": "Мегафон", "922": "Мегафон", "925": "Мегафон",
    "930": "Tele2", "931": "Tele2", "932": "Tele2",
}

CITIES_DB = {
    "910": "Москва", "911": "Санкт-Петербург", "912": "Екатеринбург", "913": "Новосибирск",
    "916": "Москва", "925": "Москва", "921": "Санкт-Петербург",
}

COUNTRY_CODES = {
    "7": "Россия/Казахстан",
    "375": "Беларусь",
    "380": "Украина",
}

COMPLAINT_TEXTS = {
    "Спам": ["Пользователь {user} ID: {user_id} занимается спамом. Ссылка на нарушение: {id}"],
    "Порнография": ["Аккаунт {user} (ID: {user_id}) распространяет порнографию. {id}"],
    "Оскорбления": ["Аккаунт {user} оскорбляет пользователей. ID: {user_id} {id}"],
}
class GlowingButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0,0,0,0)
        self.background_normal = ''
        self.border = (0,0,0,0)
        self.color = get_color_from_hex(COLORS['text'])
        self.font_size = sp(18)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(60)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['primary']), a=0.3)
            RoundedRectangle(pos=(self.x-2, self.y-2), size=(self.width+4, self.height+4), radius=[dp(15)])
            Color(*get_color_from_hex(COLORS['surface']))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
            Color(*get_color_from_hex(COLORS['primary']))
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(15)), width=1.5)

    def on_press(self):
        self.glow_alpha = 0.8
        self.update_canvas()
        return super().on_press()

    def on_release(self):
        self.glow_alpha = 0
        self.update_canvas()
        return super().on_release()

class GlowingLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = get_color_from_hex(COLORS['text'])
        self.font_size = sp(16)
        self.halign = 'left'
        self.valign = 'middle'
        self.size_hint_y = None
        self.height = dp(40)
        self.bind(size=self.setter('text_size'))

class ResultLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = get_color_from_hex(COLORS['text_secondary'])
        self.font_size = sp(14)
        self.halign = 'left'
        self.valign = 'top'
        self.size_hint_y = None
        self.bind(size=self.update_text_size)

    def update_text_size(self, *args):
        self.text_size = (self.width - dp(20), None)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        title = Label(text='[b]OSINT / SNOS[/b]', markup=True, font_size=sp(28),
                     color=get_color_from_hex(COLORS['primary']), size_hint_y=None, height=dp(80))
        layout.add_widget(title)
        btn_osint = GlowingButton(text='🔍 OSINT')
        btn_osint.bind(on_release=self.go_to_osint)
        layout.add_widget(btn_osint)
        btn_snos = GlowingButton(text='💥 SNOS')
        btn_snos.bind(on_release=self.go_to_snos)
        layout.add_widget(btn_snos)
        layout.add_widget(Label(size_hint_y=1))
        self.add_widget(layout)

    def go_to_osint(self, *args):
        self.manager.current = 'osint'

    def go_to_snos(self, *args):
        self.manager.current = 'snos'
      class OSINTScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'osint'
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        top = BoxLayout(size_hint_y=None, height=dp(50))
        back_btn = Button(text='←', size_hint_x=None, width=dp(50),
                          background_color=get_color_from_hex(COLORS['surface']),
                          color=get_color_from_hex(COLORS['primary']))
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'main'))
        top.add_widget(back_btn)
        top.add_widget(Label(text='[b]OSINT[/b]', markup=True, color=get_color_from_hex(COLORS['primary'])))
        top.add_widget(Label())
        main_layout.add_widget(top)
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(GlowingLabel(text='📞 Поиск по номеру'))
        self.phone_input = TextInput(hint_text='+7...', multiline=False,
                                     background_color=get_color_from_hex(COLORS['surface']),
                                     foreground_color=get_color_from_hex(COLORS['text']),
                                     size_hint_y=None, height=dp(40))
        content.add_widget(self.phone_input)
        phone_btn = GlowingButton(text='Найти', size_hint_y=None, height=dp(50))
        phone_btn.bind(on_release=self.search_phone)
        content.add_widget(phone_btn)

        content.add_widget(GlowingLabel(text='📧 Поиск по email'))
        self.email_input = TextInput(hint_text='email@example.com', multiline=False,
                                     background_color=get_color_from_hex(COLORS['surface']),
                                     foreground_color=get_color_from_hex(COLORS['text']),
                                     size_hint_y=None, height=dp(40))
        content.add_widget(self.email_input)
        email_btn = GlowingButton(text='Найти', size_hint_y=None, height=dp(50))
        email_btn.bind(on_release=self.search_email)
        content.add_widget(email_btn)

        content.add_widget(GlowingLabel(text='🔎 Поиск по никнейму'))
        self.nick_input = TextInput(hint_text='username', multiline=False,
                                    background_color=get_color_from_hex(COLORS['surface']),
                                    foreground_color=get_color_from_hex(COLORS['text']),
                                    size_hint_y=None, height=dp(40))
        content.add_widget(self.nick_input)
        nick_btn = GlowingButton(text='Найти', size_hint_y=None, height=dp(50))
        nick_btn.bind(on_release=self.search_nick)
        content.add_widget(nick_btn)

        content.add_widget(GlowingLabel(text='🌐 Поиск по IP'))
        self.ip_input = TextInput(hint_text='8.8.8.8', multiline=False,
                                  background_color=get_color_from_hex(COLORS['surface']),
                                  foreground_color=get_color_from_hex(COLORS['text']),
                                  size_hint_y=None, height=dp(40))
        content.add_widget(self.ip_input)
        ip_btn = GlowingButton(text='Найти', size_hint_y=None, height=dp(50))
        ip_btn.bind(on_release=self.search_ip)
        content.add_widget(ip_btn)

        content.add_widget(GlowingLabel(text='📱 Поиск в Telegram'))
        self.tg_input = TextInput(hint_text='@username', multiline=False,
                                  background_color=get_color_from_hex(COLORS['surface']),
                                  foreground_color=get_color_from_hex(COLORS['text']),
                                  size_hint_y=None, height=dp(40))
        content.add_widget(self.tg_input)
        tg_btn = GlowingButton(text='Найти', size_hint_y=None, height=dp(50))
        tg_btn.bind(on_release=self.search_tg)
        content.add_widget(tg_btn)

        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        self.result_label = ResultLabel(text='', size_hint_y=0.4)
        main_layout.add_widget(self.result_label)
        self.add_widget(main_layout)

    def search_phone(self, *args):
        phone = self.phone_input.text.strip()
        if not phone:
            self.result_label.text = 'Введите номер'
            return
        cleaned = re.sub(r'[^\d]', '', phone)
        if len(cleaned) == 10:
            cleaned = '7' + cleaned
        elif len(cleaned) == 11 and cleaned[0] == '8':
            cleaned = '7' + cleaned[1:]
        elif len(cleaned) == 11 and cleaned[0] == '7':
            pass
        else:
            self.result_label.text = 'Неверный формат'
            return
        result = f"Номер: +{cleaned}\n"
        def_code = cleaned[1:4]
        if def_code in OPERATORS_DB:
            result += f"Оператор: {OPERATORS_DB[def_code]}\n"
        if def_code in CITIES_DB:
            result += f"Регион: {CITIES_DB[def_code]}\n"
        try:
            num = phonenumbers.parse(f"+{cleaned}")
            result += f"Страна: {geocoder.description_for_number(num, 'ru')}\n"
            op = carrier.name_for_number(num, 'ru')
            if op:
                result += f"Оператор: {op}\n"
        except:
            pass
        try:
            r = requests.get(f"https://t.me/+{cleaned}", timeout=3)
            result += f"Telegram: {'активен' if r.status_code == 200 else 'не найден'}\n"
        except:
            result += "Telegram: ошибка проверки\n"
        try:
            r = requests.get(f"https://wa.me/{cleaned}", timeout=3)
            result += f"WhatsApp: {'активен' if r.status_code == 200 else 'не найден'}\n"
        except:
            result += "WhatsApp: ошибка проверки\n"
        self.result_label.text = result

    def search_email(self, *args):
        email = self.email_input.text.strip()
        if not email:
            self.result_label.text = 'Введите email'
            return
        result = f"Email: {email}\n"
        h = hashlib.md5(email.lower().encode()).hexdigest()
        result += f"Gravatar: https://www.gravatar.com/avatar/{h}\n"
        try:
            r = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                             headers={'User-Agent': 'OSINT-App'}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                result += "Утечки:\n"
                for b in data[:3]:
                    result += f"  - {b.get('Name')} ({b.get('BreachDate')})\n"
            elif r.status_code == 404:
                result += "Утечек не найдено\n"
            else:
                result += "Ошибка проверки утечек\n"
        except:
            result += "Не удалось проверить утечки\n"
        self.result_label.text = result

    def search_nick(self, *args):
        nick = self.nick_input.text.strip().replace('@', '')
        if not nick:
            self.result_label.text = 'Введите никнейм'
            return
        result = f"Никнейм: {nick}\n"
        sites = {
            "ВКонтакте": f"https://vk.com/{nick}",
            "Telegram": f"https://t.me/{nick}",
            "Instagram": f"https://instagram.com/{nick}",
            "TikTok": f"https://tiktok.com/@{nick}",
            "YouTube": f"https://youtube.com/@{nick}",
            "GitHub": f"https://github.com/{nick}",
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        for name, url in sites.items():
            try:
                r = requests.get(url, headers=headers, timeout=2)
                if r.status_code == 200:
                    result += f"{name}: найден\n"
            except:
                pass
        self.result_label.text = result

    def search_ip(self, *args):
        ip = self.ip_input.text.strip()
        if not ip:
            self.result_label.text = 'Введите IP'
            return
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data.get('status') == 'success':
                    result = (f"IP: {ip}\n"
                              f"Страна: {data.get('country')}\n"
                              f"Регион: {data.get('regionName')}\n"
                              f"Город: {data.get('city')}\n"
                              f"Провайдер: {data.get('isp')}\n"
                              f"Координаты: {data.get('lat')}, {data.get('lon')}")
                else:
                    result = "Не удалось определить"
            else:
                result = "Ошибка запроса"
        except:
            result = "Ошибка соединения"
        self.result_label.text = result

    def search_tg(self, *args):
        username = self.tg_input.text.strip().replace('@', '')
        if not username:
            self.result_label.text = 'Введите username'
            return
        try:
            r = requests.get(f"https://t.me/{username}", timeout=3)
            exists = r.status_code == 200
            result = f"@{username} — {'существует' if exists else 'не найден'}\n"
        except:
            result = "Ошибка проверки"
        self.result_label.text = result
      class SNOSScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'snos'
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        top = BoxLayout(size_hint_y=None, height=dp(50))
        back_btn = Button(text='←', size_hint_x=None, width=dp(50),
                          background_color=get_color_from_hex(COLORS['surface']),
                          color=get_color_from_hex(COLORS['primary']))
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'main'))
        top.add_widget(back_btn)
        top.add_widget(Label(text='[b]SNOS[/b]', markup=True, color=get_color_from_hex(COLORS['primary'])))
        top.add_widget(Label())
        main_layout.add_widget(top)
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(10))

        content.add_widget(GlowingLabel(text='ID цели:'))
        self.target_id = TextInput(hint_text='123456789', multiline=False,
                                   background_color=get_color_from_hex(COLORS['surface']),
                                   foreground_color=get_color_from_hex(COLORS['text']),
                                   size_hint_y=None, height=dp(40))
        content.add_widget(self.target_id)

        content.add_widget(GlowingLabel(text='@username (если есть):'))
        self.target_user = TextInput(hint_text='@username', multiline=False,
                                     background_color=get_color_from_hex(COLORS['surface']),
                                     foreground_color=get_color_from_hex(COLORS['text']),
                                     size_hint_y=None, height=dp(40))
        content.add_widget(self.target_user)

        content.add_widget(GlowingLabel(text='Ссылка на нарушение (опционально):'))
        self.violation_link = TextInput(hint_text='https://t.me/...', multiline=False,
                                        background_color=get_color_from_hex(COLORS['surface']),
                                        foreground_color=get_color_from_hex(COLORS['text']),
                                        size_hint_y=None, height=dp(40))
        content.add_widget(self.violation_link)

        content.add_widget(GlowingLabel(text='Тип жалобы:'))
        self.complaint_type = TextInput(text='Спам', readonly=True, multiline=False,
                                        background_color=get_color_from_hex(COLORS['surface']),
                                        foreground_color=get_color_from_hex(COLORS['primary']),
                                        size_hint_y=None, height=dp(40))
        content.add_widget(self.complaint_type)
        types = list(COMPLAINT_TEXTS.keys())
        type_box = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(120))
        for t in types:
            btn = Button(text=t[:10], size_hint_y=None, height=dp(40),
                         background_color=get_color_from_hex(COLORS['surface']),
                         color=get_color_from_hex(COLORS['text']))
            btn.bind(on_release=lambda x, t=t: setattr(self.complaint_type, 'text', t))
            type_box.add_widget(btn)
        content.add_widget(type_box)

        content.add_widget(GlowingLabel(text='Количество жалоб:'))
        self.slider_label = Label(text='50', color=get_color_from_hex(COLORS['primary']),
                                  size_hint_y=None, height=dp(30))
        content.add_widget(self.slider_label)
        self.slider = Slider(min=1, max=200, value=50, step=1,
                              value_track=True, value_track_color=get_color_from_hex(COLORS['primary']))
        self.slider.bind(value=lambda s, v: setattr(self.slider_label, 'text', str(int(v))))
        content.add_widget(self.slider)

        start_btn = GlowingButton(text='ЗАПУСТИТЬ СНОС')
        start_btn.bind(on_release=self.start_snos)
        content.add_widget(start_btn)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(30))
        content.add_widget(self.progress)

        self.log_label = ResultLabel(text='', size_hint_y=0.3)
        content.add_widget(self.log_label)

        main_layout.add_widget(content)
        self.add_widget(main_layout)
        self.is_running = False

    def start_snos(self, *args):
        if self.is_running:
            return
        target_id = self.target_id.text.strip()
        target_user = self.target_user.text.strip()
        violation_link = self.violation_link.text.strip()
        ctype = self.complaint_type.text
        count = int(self.slider.value)
        if not target_id and not target_user:
            self.log_label.text = 'Укажите ID или @username'
            return
        self.is_running = True
        self.progress.value = 0
        self.log_label.text = ''
        threading.Thread(target=self.snos_worker,
                         args=(target_id, target_user, violation_link, ctype, count)).start()

    def snos_worker(self, target_id, target_user, violation_link, ctype, count):
        def gen_email():
            domains = ["gmail.com", "mail.ru", "rambler.ru"]
            name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
            return f"{name}@{random.choice(domains)}"
        def gen_phone():
            return f"+79{''.join(random.choices('0123456789', k=9))}"
        texts = COMPLAINT_TEXTS.get(ctype, ["Жалоба на пользователя {user}"])
        base_text = random.choice(texts)
        complaint_text = base_text.format(user_id=target_id, user=target_user, id=violation_link)
        retry_strategy = Retry(total=3, status_forcelist=[429,500,502,503,504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount('https://', adapter)
        headers = {'User-Agent': 'Mozilla/5.0'}
        sites = [
            {'url': 'https://telegram.org/support?setln=ru', 'data': {'tg_feedback_appeal': '', 'tg_feedback_email': '', 'tg_feedback_phone': ''}},
            {'url': 'https://telegram.org/support', 'data': {'name': '', 'email': '', 'message': ''}}
        ]
        sent = 0
        for i in range(count):
            if not self.is_running:
                break
            site = random.choice(sites)
            email = gen_email()
            phone = gen_phone()
            proxy = None
            if 'tg_feedback_appeal' in site['data']:
                site['data']['tg_feedback_appeal'] = complaint_text
                site['data']['tg_feedback_email'] = email
                site['data']['tg_feedback_phone'] = phone
            else:
                site['data']['name'] = target_user
                site['data']['email'] = email
                site['data']['message'] = complaint_text
            try:
                resp = session.post(site['url'], headers=headers, data=site['data'], proxies=proxy, timeout=10)
                if resp.status_code == 200:
                    sent += 1
                    Clock.schedule_once(lambda dt, msg=f"✓ {i+1}/{count} отправлено": self.update_log(msg))
                else:
                    Clock.schedule_once(lambda dt, msg=f"✗ {i+1}/{count} ошибка {resp.status_code}": self.update_log(msg))
            except Exception as e:
                Clock.schedule_once(lambda dt, msg=f"✗ {i+1}/{count} ошибка: {str(e)[:30]}": self.update_log(msg))
            Clock.schedule_once(lambda dt, v=(i+1)/count*100: setattr(self.progress, 'value', v))
            time.sleep(random.uniform(0.5, 2))
        Clock.schedule_once(lambda dt: self.finish_snos(sent, count))

    def update_log(self, msg):
        self.log_label.text += msg + '\n'

    def finish_snos(self, sent, total):
        self.log_label.text += f'\n✅ Готово! Отправлено {sent} из {total}'
        self.is_running = False
        self.progress.value = 0

class OSINTSNOSApp(App):
    def build(self):
        self.title = 'OSINT SNOS'
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(OSINTScreen(name='osint'))
        sm.add_widget(SNOSScreen(name='snos'))
        return sm

if __name__ == '__main__':
    OSINTSNOSApp().run()
