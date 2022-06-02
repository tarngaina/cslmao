from tkinter import VERTICAL, Tk, Toplevel, Canvas, Entry, X, BOTH, NW, N, CENTER, LEFT, TOP, BOTTOM, NORMAL, HIDDEN
from tkinter.ttk import Scrollbar, Style
from tkinter.font import Font
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames, asksaveasfilename
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk

from os.path import join as pjoin, exists as pexists, dirname as pdirname, basename as pbasename, isdir as pisdir, relpath as prelpath
from os import mkdir, listdir, walk, startfile, remove, getpid
from sys import argv as ARGV, exit as sexit
from subprocess import run as Prun, Popen, PIPE, STDOUT, CREATE_NO_WINDOW
from threading import Thread
from json import load as jload, dump as jdump
from datetime import datetime as dt
from shutil import rmtree, copy
from ctypes import windll


class PATH:
    APP = pdirname(ARGV[0])
    DATA = pjoin(APP, 'data')
    RAW = pjoin(APP, 'raw')
    UI = pjoin(APP, 'ui')


class CLI:
    class CSLOL:
        EXE = pjoin(PATH.APP, 'cli', 'mod-tools.exe')

        def import_fantome(src, dst, game=None, noTFT=True):
            cmds = [CLI.CSLOL.EXE, 'import', src, dst]
            if game:
                cmds.append('--game:' + game)
            if noTFT:
                cmds.append('--noTFT')
            p = Popen(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            for line in p.stdout:
                LOG.write(line.decode()[:-1], time=False)
            p.wait()
            return p.returncode == 0

        def export_fantome(src, dst, game=None, noTFT=True):
            cmds = [CLI.CSLOL.EXE, 'export', src, dst]
            if game:
                cmds.append('--game:' + game)
            if noTFT:
                cmds.append('--noTFT')
            p = Popen(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            for line in p.stdout:
                LOG.write(line.decode()[:-1], time=False)
            p.wait()
            return p.returncode == 0

        def make_overlay(src, overlay, game=None, mods=None, noTFT=True, ignore_conflict=True):
            cmds = [CLI.CSLOL.EXE, 'mkoverlay', src, overlay]
            if game:
                cmds.append('--game:' + game)
            if mods:
                cmds.append('--mods:' + '/'.join(mods))
            if noTFT:
                cmds.append('--noTFT')
            if ignore_conflict:
                cmds.append('--ignoreConflict')
            SYSTEM.proc = Popen(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            for line in SYSTEM.proc.stdout:
                LOG.write(line.decode()[:-1], time=False)
            SYSTEM.proc.wait()
            return SYSTEM.proc.returncode == 0

        def run_overlay(overlay, config, game=None):
            cmds = [CLI.CSLOL.EXE, 'runoverlay', overlay, config]
            if game:
                cmds.append(game)
            SYSTEM.proc = Popen(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdin=PIPE, stdout=PIPE, stderr=STDOUT
            )
            for line in SYSTEM.proc.stdout:
                LOG.write(line.decode()[:-1])

        def wad_make(src, dst=None):
            cmds = [pjoin(PATH.APP, 'cli', 'wad-make.exe'), src]
            if dst:
                cmds.append(dst)
            p = Prun(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            return p.returncode == 0

    class RITOBIN:
        EXE = pjoin(PATH.APP, 'cli', 'ritobin_cli.exe')

        def run(src, dst=None):
            cmds = [CLI.RITOBIN.EXE, src]
            if dst:
                cmds.append(dst)
            p = Prun(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            return p.returncode == 0

    class SKLCONVERT:
        EXE = pjoin(PATH.APP, 'cli', 'skl-convert.exe')

        def run(src):
            cmds = [CLI.SKLCONVERT.EXE, src]
            p = Prun(
                cmds, creationflags=CREATE_NO_WINDOW,
                stdout=PIPE, stderr=STDOUT
            )
            return p.returncode == 0

    class ANM1E:
        def run(src):
            try:
                with open(src, 'rb') as inp:
                    data = inp.read().hex()
                    with open(src, 'wb') as out:
                        out.write(bytes.fromhex(
                            ''.join([data[:48], '1e', data[50:]])))
                return True
            except:
                return False


class MOD:
    EMPTY_INFO = {
        'Name': 'unnamed',
        'Author': 'empty',
        'Version': '0.0.0',
        'Description': ''
    }

    mods = []

    def get_mods(key=None):
        if key:
            return list(filter(lambda m: key in ''.join(m.path, str(m.infos)), MOD.mods))
        return MOD.mods

    def __init__(self, path, infos=None, image=None, enable=False):
        self.path = path
        self.infos = infos
        self.image = image
        self.enable = enable
        self.update()

        self.imagep = None
        self.border = None
        self.textbg = None
        self.text = None
        self.lenlines = '1'
        self.remove = None
        self.location = None
        self.edit = None
        self.export = None
        self.left = None
        self.right = None
        self.state = False

    def update(self):
        if not self.infos:
            temp = pjoin(self.path, 'META', 'info.json')
            if pexists(temp):
                with open(temp, 'r', encoding='utf-8') as f:
                    self.infos = jload(f)
            else:
                self.infos = MOD.EMPTY_INFO

        if not self.image:
            temp = pjoin(self.path, 'META', 'image.png')
            if pexists(temp):
                self.image = temp

    def edit_infos(self, name, author, version, desc):
        self.infos['Name'] = name
        self.infos['Author'] = author
        self.infos['Version'] = version
        self.infos['Description'] = desc
        with open(pjoin(self.path, 'META', 'info.json'), 'w+', encoding='utf-8') as f:
            jdump(self.infos, f, indent=4)

    def edit_image(self, newimage):
        self.image = pjoin(self.path, 'META', 'image.png')
        copy(newimage, self.image)


class LOG:
    logs = []

    def add_log(text, time=True):
        text = ' '.join(text.split()).strip()
        if text != '':
            LOG.logs.append(f'{SYSTEM.now()} {text}' if time else text)

    def write(obj, time=True):
        if type(obj) is list:
            obj = list(map(str, obj))
            obj = list(filter(lambda o: o != '', obj))
            list(map(lambda o: SYSTEM.add_log(o, time), obj))
            return
        obj = str(obj)
        if '\n' in obj:
            obj = list(filter(lambda o: o != '', obj.split('\n')))
            list(map(lambda o: SYSTEM.add_log(o, time), obj))
            return
        if obj != '':
            LOG.add_log(obj, time)
            return


class SYSTEM:
    g = None
    settings = {}
    proc = None
    state = 'idle'

    def is_blocking():
        return SYSTEM.state == 'blocking'

    def is_running():
        return SYSTEM.state == 'running'

    def now():
        return dt.now().strftime('%H:%M:%S.%f')[:-3]

    def ensure_folder():
        if not pexists(PATH.DATA):
            mkdir(PATH.DATA)
        if not pexists(pjoin(PATH.DATA, 'config.ini')):
            open(pjoin(PATH.DATA, 'config.ini'), 'w+').close()
        if not pexists(PATH.RAW):
            mkdir(PATH.RAW)

    def save_profile():
        with open(pjoin(PATH.DATA, 'profile'), 'w+', encoding='utf-8') as f:
            lines = [
                f'{pbasename(m.path)},{int(m.enable)}\n' for m in MOD.mods]
            f.writelines(lines)
        LOG.write('Saved profile')

    def load_profile():
        def load_default():
            MOD.mods = []
            if pexists(PATH.RAW):
                l = list(map(lambda f: pjoin(PATH.RAW, f), listdir(PATH.RAW)))
                l = list(filter(lambda f: pisdir(f), l))
                list(map(lambda f: MOD.mods.append(
                    MOD(path=pjoin(PATH.RAW, f))), l))

        MOD.mods = []
        if not pexists(pjoin(PATH.DATA, 'profile')):
            LOG.write('No profile found, loading RAW instead.')
            load_default()
        else:
            with open(pjoin(PATH.DATA, 'profile'), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    n, e = line[:-1].split(',')
                    path = pjoin(PATH.RAW, n)
                    if not pexists(path):
                        continue
                    MOD.mods.append(MOD(
                        path=path,
                        enable=bool(int(e))
                    ))

        LOG.write(f'Loaded profile')
        SYSTEM.save_profile()

    def save_settings():
        with open(pjoin(PATH.DATA, 'settings'), 'w+', encoding='utf-8') as f:
            jdump(SYSTEM.settings, f, indent=4)
        LOG.write('Saved settings')

    def load_settings():
        def load_default():
            SYSTEM.settings['game'] = ''
            SYSTEM.settings['extra_game_modes'] = False
            SYSTEM.settings['auto_pack_raw'] = False
            SYSTEM.settings['auto_update_skl'] = False
            SYSTEM.settings['auto_update_anm'] = False
            SYSTEM.settings['auto_convert_py'] = False
            SYSTEM.settings['theme'] = 'default'

        load_default()
        if pexists(pjoin(PATH.DATA, 'settings')):
            with open(pjoin(PATH.DATA, 'settings'), 'r', encoding='utf-8') as f:
                dic = jload(f)
                for key in dic:
                    SYSTEM.settings[key] = dic[key]

        LOG.write('Loaded settings')
        SYSTEM.save_settings()


class GUI:
    configs = {}
    cache = {}

    def load_configs():
        def load_default():
            GUI.configs['animated_topbar'] = False
            GUI.configs['border_bg'] = '#00163b'
            GUI.configs['textfield_bg'] = '#75cffb'
            GUI.configs['modname_text_fg'] = '#f0e7ff'
            GUI.configs['edit_text_fg'] = '#150037'
            GUI.configs['create_text_fg'] = '#150037'
            GUI.configs['log_text_fg'] = '#150037'
            GUI.configs['minilog_text_fg'] = '#150037'
            GUI.configs['setting_text_fg'] = '#150037'
            GUI.configs['scrollbar_fg'] = '#0084ff'
            GUI.configs['scrollbar_bg'] = '#00163b'

        load_default()
        if pexists(pjoin(PATH.UI, SYSTEM.settings['theme'])):
            if pexists(pjoin(PATH.UI, SYSTEM.settings['theme'], 'configs')):
                with open(pjoin(PATH.UI, SYSTEM.settings['theme'], 'configs'), 'r', encoding='utf-8') as f:
                    dic = jload(f)
                    for key in dic:
                        GUI.configs[key] = dic[key]

        LOG.write('Loaded theme')
        GUI.save_configs()

    def save_configs():
        if not pexists(pjoin(PATH.UI, SYSTEM.settings['theme'])):
            mkdir(pjoin(PATH.UI, SYSTEM.settings['theme']))
        with open(pjoin(PATH.UI, SYSTEM.settings['theme'], 'configs'), 'w+', encoding='utf-8') as f:
            jdump(GUI.configs, f, indent=4)
        LOG.write('Saved theme')

    def load_image(path, key, w, h, reload=False):
        if reload or key not in GUI.cache:
            try:
                photo = Image.open(
                    pjoin(PATH.UI, SYSTEM.settings['theme'], path))
                GUI.cache[key] = ImageTk.PhotoImage(photo.resize((w, h)))
            except:
                GUI.cache[key] = ImageTk.PhotoImage(Image.new('RGB', (w, h)))

    def load_image_gif(path, key, w, h, reload=False):
        if reload or key not in GUI.cache:
            try:
                photo = Image.open(
                    pjoin(PATH.UI, SYSTEM.settings['theme'], path))
                GUI.cache[key+'#max'] = photo.n_frames
                GUI.cache[key+'#delay'] = photo.info['duration']
                for i in range(0, GUI.cache[key+'#max']):
                    photo.seek(i)
                    GUI.cache[key+str(i)] = ImageTk.PhotoImage(
                        photo.copy().convert('RGBA').resize((w, h)))
            except:
                GUI.cache[key+'#max'] = 1
                GUI.cache[key+'#delay'] = 9999
                GUI.cache[key +
                          '0'] = ImageTk.PhotoImage(Image.new('RGB', (w, h)))
            GUI.cache[key] = 'loaded gif'

    class GLOBAL:
        refresh_mod_list = None

    def create_root(self):
        self.root = Tk()
        self.root.title('cslmao by tarngaina')
        self.root.iconphoto(True, ImageTk.PhotoImage(
            Image.open(pjoin(PATH.APP, 'icon.png'))))
        self.root.overrideredirect(True)
        self.root.resizable(False, False)
        self.root.geometry(
            f'{1116}x{634}+{int((self.root.winfo_screenwidth() - 1116) / 2)}+{int((self.root.winfo_screenheight() - 634) / 2)}')

        def map(e):
            if not self.root.wm_overrideredirect():
                self.root.overrideredirect(1)
                self.root.after(10, self.set_appwindow)

        self.root.bind('<Map>', map)

    def create_top_bar(self):
        def create_bar():
            def update_bar_gif():
                self.topbar.current += 1
                if self.topbar.current == self.topbar.max:
                    self.topbar.current = 0
                self.topbar.itemconfig(
                    self.topbarbg, image=GUI.cache['topbar'+str(self.topbar.current)])
                self.topbar.after(self.topbar.delay, update_bar_gif)

            self.topbar = Canvas(
                master=self.root,
                height=32,
                highlightthickness=1,
                highlightbackground=GUI.configs['border_bg'],
                highlightcolor=GUI.configs['border_bg']
            )
            self.topbar.pack(side=TOP, fill=X)
            if not GUI.configs['animated_topbar']:
                GUI.load_image(
                    path=pjoin('topbar', 'bg.png'),
                    key='topbar',
                    w=1116,
                    h=32+2
                )
                self.topbarbg = self.topbar.create_image(
                    (0, 0),
                    image=GUI.cache['topbar'],
                    anchor=NW
                )
            else:
                GUI.load_image_gif(
                    path=pjoin('topbar', 'bg.gif'),
                    key='topbar',
                    w=1116,
                    h=32+2
                )
                self.topbar.current = 0
                self.topbar.max = GUI.cache['topbar#max']
                self.topbar.delay = GUI.cache['topbar#delay']
                self.topbarbg = self.topbar.create_image(
                    (0, 0),
                    image=GUI.cache['topbar0'],
                    anchor=NW
                )
                update_bar_gif()

            def get_pos(e):
                xwin = self.root.winfo_x() - e.x_root
                ywin = self.root.winfo_y() - e.y_root

                def move_window(e):
                    self.root.geometry(
                        f'+{e.x_root + xwin}+{e.y_root + ywin}')
                self.topbar.tag_bind(self.topbarbg, '<B1-Motion>', move_window)

            self.topbar.tag_bind(self.topbarbg, '<Button-1>', get_pos)

        def create_minimize_button():
            def on_minimizeapp(e):
                if self.createwindow:
                    self.createwindow.destroy()
                    self.createwindow = None
                if self.editwindow:
                    self.editwindow.destroy()
                    self.editwindow = None
                self.root.withdraw()
                self.root.overrideredirect(False)
                self.root.iconify()

            GUI.load_image(
                path=pjoin('topbar', 'minimize.png'),
                key='minimize',
                w=32,
                h=32,
            )
            self.minimizebutton = self.topbar.create_image(
                (1116 - 64 - 24, 0),
                image=GUI.cache['minimize'],
                anchor=NW
            )
            self.topbar.tag_bind(self.minimizebutton,
                                 '<Button-1>', on_minimizeapp)

        def create_close_button():
            def on_closeapp(e):
                self.root.quit()
                sexit()

            GUI.load_image(
                path=pjoin('topbar', 'close.png'),
                key='close',
                w=32,
                h=32,
            )
            self.closebutton = self.topbar.create_image(
                (1116 - 32 - 12, 0),
                image=GUI.cache['close'],
                anchor=NW
            )
            self.topbar.tag_bind(self.closebutton, '<Button-1>', on_closeapp)

        def create_tab_buttons():
            def on_changetab(e):
                self.tab += 1
                if self.tab > 2:
                    self.tab = 0
                self.update_tab()

            GUI.load_image(
                path=pjoin('topbar', 'home.png'),
                key='home',
                w=32,
                h=32,
            )
            GUI.load_image(
                path=pjoin('topbar', 'log.png'),
                key='log',
                w=32,
                h=32,
            )
            GUI.load_image(
                path=pjoin('topbar', 'setting.png'),
                key='setting',
                w=32,
                h=32,
            )
            self.tabbutton = self.topbar.create_image(
                (12, 0),
                image=GUI.cache['log'],
                anchor=NW
            )
            self.topbar.tag_bind(self.tabbutton, '<Button-1>', on_changetab)

        def create_run_button():
            def get_enabled_mods():
                return list(filter(lambda m: m.enable and pexists(pjoin(m.path, 'WAD')), MOD.mods))

            def before_run(enabled_mods):
                if SYSTEM.settings['auto_pack_raw']:
                    for m in enabled_mods:
                        for root, dirs, files in walk(m.path):
                            if SYSTEM.settings['auto_update_skl']:
                                skls = list(
                                    filter(lambda f: f.endswith('.skl'), files))
                                skls = list(
                                    map(lambda f: pjoin(root, f), skls))
                                for skl in skls:
                                    s = prelpath(
                                        skl, pdirname(m.path)).replace('\\', '/')
                                    if (CLI.SKLCONVERT.run(src=skl)):
                                        LOG.write(
                                            f'B4R[SKL] Converted: {s}')
                                    else:
                                        LOG.write(
                                            f'B4R[SKL] Error: Failed to convert {s}')

                            if SYSTEM.settings['auto_update_anm']:
                                anms = list(
                                    filter(lambda f: f.endswith('.anm'), files))
                                anms = list(
                                    map(lambda f: pjoin(root, f), anms))
                                for anm in anms:
                                    s = prelpath(
                                        anm, pdirname(m.path)).replace('\\', '/')
                                    if (CLI.ANM1E.run(src=anm)):
                                        LOG.write(
                                            f'B4R[ANM] Edited: {s}')
                                    else:
                                        LOG.write(
                                            f'B4R[ANM] Error: Failed to edit {s}')
                            if SYSTEM.settings['auto_convert_py']:
                                pys = list(
                                    filter(lambda f: f.endswith('.py'), files))
                                pys = list(map(lambda f: pjoin(root, f), pys))
                                for py in pys:
                                    if (CLI.RITOBIN.run(src=py)):
                                        bin = py.split('.py')[0] + '.bin'
                                        s = prelpath(
                                            bin, pdirname(m.path)).replace('\\', '/')
                                        LOG.write(
                                            f'B4R[TOBIN] Converted: {s}')
                                    else:
                                        s = prelpath(
                                            py, pdirname(m.path)).replace('\\', '/')
                                        LOG.write(
                                            f'B4R[TOBIN] Error: Failed to convert {s}')

                        raws = list(
                            map(lambda f: pjoin(m.path, 'WAD', f), listdir(pjoin(m.path, 'WAD'))))
                        raws = list(filter(lambda f: pisdir(f), raws))
                        for raw in raws:
                            wad = f'{raw}.client' if raw.endswith(
                                '.wad') else f'{raw}.wad.client'
                            if pexists(wad):
                                remove(wad)
                            if (CLI.CSLOL.wad_make(src=raw, dst=wad)):
                                s = prelpath(wad, pdirname(m.path)
                                             ).replace('\\', '/')
                                LOG.write(
                                    f'B4R[TOBIN] Packed: {s}')
                            else:
                                s = prelpath(raw, pdirname(m.path)
                                             ).replace('\\', '/')
                                LOG.write(
                                    f'B4R[TOWAD] Error: Failed to pack {s}')

            def on_runmods(e):
                def run_thread():
                    SYSTEM.state = 'blocking'
                    try:
                        t = Prun('tasklist', creationflags=CREATE_NO_WINDOW,
                                 capture_output=True, check=True).stdout.decode()
                        if t.count('cslmao.exe') > 2:
                            LOG.write(
                                'Error: Found another cslmao running. Close all cslmao & restart the app.')
                            SYSTEM.state = 'idle'
                            self.topbar.itemconfig(
                                self.runbutton, image=GUI.cache['run'])
                            return
                        if t.count('cslol-manager.exe') > 0:
                            SYSTEM.state = 'blocking'
                            LOG.write(
                                'Error: Found cslol running. Close cslol & restart the app.')
                            SYSTEM.state = 'idle'
                            self.topbar.itemconfig(
                                self.runbutton, image=GUI.cache['run'])
                            return
                    except:
                        pass
                    mods = get_enabled_mods()
                    before_run(mods)
                    res = CLI.CSLOL.make_overlay(
                        src=PATH.RAW,
                        overlay=pjoin(PATH.DATA, 'overlay'),
                        game=SYSTEM.settings['game'],
                        mods=[pbasename(m.path) for m in mods],
                        noTFT=not SYSTEM.settings['extra_game_modes']
                    )
                    if res:
                        SYSTEM.state = 'running'
                        CLI.CSLOL.run_overlay(
                            overlay=pjoin(PATH.DATA, 'overlay'),
                            config=pjoin(
                                PATH.APP, 'data', 'config.ini'),
                            game=SYSTEM.settings['game']
                        )
                    else:
                        if SYSTEM.proc:
                            SYSTEM.proc.communicate()
                            SYSTEM.proc.kill()
                        SYSTEM.proc = None
                        self.topbar.itemconfig(
                            self.runbutton, image=GUI.cache['run'])
                        SYSTEM.state = 'idle'
                        LOG.write(
                            'Error: Make overlay failed, back to idling.')

                def run():
                    SYSTEM.save_profile()
                    Thread(
                        target=run_thread,
                        args=(),
                        daemon=True
                    ).start()

                def stop():
                    if SYSTEM.proc:
                        SYSTEM.proc.communicate()
                        SYSTEM.proc.kill()
                    SYSTEM.proc = None
                    SYSTEM.state = 'idle'
                    LOG.write('Status: Stopped running overlay, idling.')

                if SYSTEM.is_blocking():
                    return
                if not SYSTEM.is_running():
                    run()
                    self.topbar.itemconfig(
                        self.runbutton, image=GUI.cache['stop'])
                else:
                    stop()
                    self.topbar.itemconfig(
                        self.runbutton, image=GUI.cache['run'])

            GUI.load_image(
                path=pjoin('topbar', 'run.png'),
                key='run',
                w=32,
                h=32,
            )
            GUI.load_image(
                path=pjoin('topbar', 'stop.png'),
                key='stop',
                w=32,
                h=32,
            )
            self.runbutton = self.topbar.create_image(
                (32 + 24, 0),
                image=GUI.cache['run'],
                anchor=NW
            )
            self.topbar.tag_bind(self.runbutton, '<Button-1>', on_runmods)

        def create_multi_select_buttons():
            def create_all_button():
                def on_selectallmods(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return
                    for m in MOD.mods:
                        m.enable = True
                        self.modpage.itemconfig(
                            m.textbg, image=GUI.cache['activetextbg' + m.lenlines])
                        self.modpage.itemconfig(
                            m.border, image=GUI.cache['activeborder'])

                GUI.load_image(
                    path=pjoin('topbar', 'all.png'),
                    key='all',
                    w=32,
                    h=32,
                )
                self.allbutton = self.topbar.create_image(
                    (280, 0),
                    image=GUI.cache['all'],
                    anchor=NW
                )
                self.topbar.tag_bind(
                    self.allbutton, '<Button-1>', on_selectallmods)

            def create_non_button():
                def on_deselectallmods(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return
                    for m in MOD.mods:
                        m.enable = False
                        self.modpage.itemconfig(
                            m.textbg, image=GUI.cache['textbg' + m.lenlines])
                        self.modpage.itemconfig(
                            m.border, image=GUI.cache['border'])

                GUI.load_image(
                    path=pjoin('topbar', 'non.png'),
                    key='non',
                    w=32,
                    h=32,
                )
                self.nonbutton = self.topbar.create_image(
                    (324, 0),
                    image=GUI.cache['non'],
                    anchor=NW
                )
                self.topbar.tag_bind(
                    self.nonbutton, '<Button-1>', on_deselectallmods)

            create_all_button()
            create_non_button()

        def create_sort_buttons():
            def create_sortp_button():
                def on_sortpmods(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return
                    MOD.mods.sort(key=lambda m: m.path)
                    SYSTEM.save_profile()
                    if GUI.GLOBAL.refresh_mod_list:
                        GUI.GLOBAL.refresh_mod_list()

                GUI.load_image(
                    path=pjoin('topbar', 'sortp.png'),
                    key='sortp',
                    w=32,
                    h=32,
                )
                self.sortpbutton = self.topbar.create_image(
                    (368, 0),
                    image=GUI.cache['sortp'],
                    anchor=NW
                )
                self.topbar.tag_bind(
                    self.sortpbutton, '<Button-1>', on_sortpmods)

            def create_sortn_button():
                def on_sortnmods(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return
                    MOD.mods.sort(key=lambda m: m.infos['Name'])
                    SYSTEM.save_profile()
                    if GUI.GLOBAL.refresh_mod_list:
                        GUI.GLOBAL.refresh_mod_list()

                GUI.load_image(
                    path=pjoin('topbar', 'sortn.png'),
                    key='sortn',
                    w=32,
                    h=32,
                )
                self.sortnbutton = self.topbar.create_image(
                    (412, 0),
                    image=GUI.cache['sortn'],
                    anchor=NW
                )
                self.topbar.tag_bind(
                    self.sortnbutton, '<Button-1>', on_sortnmods)

            create_sortp_button()
            create_sortn_button()

        create_bar()

        create_minimize_button()
        create_close_button()
        create_tab_buttons()
        create_run_button()
        create_multi_select_buttons()
        create_sort_buttons()

    def create_mod_page(self):
        def create_bg():
            self.modpage = Canvas(
                master=self.root,
                height=634-64,
                highlightthickness=1,
                highlightbackground=GUI.configs['border_bg'],
                highlightcolor=GUI.configs['border_bg']
            )
            self.modpage.pack(fill=X)
            GUI.load_image(
                path=pjoin('modpage', 'bg.png'),
                key='modpage',
                w=1116,
                h=634-64
            )
            self.modpagebg = self.modpage.create_image(
                (0, 0),
                image=GUI.cache['modpage'],
                anchor=NW
            )

        def create_page():
            def create_import_button():
                def on_importmod(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return

                    def import_thread():
                        filenames = askopenfilenames(
                            title='Import FANTOME',
                            parent=self.root,
                            filetypes=[
                                ('FANTOME file', '*.fantome *.zip')
                            ]
                        )
                        if filenames != '':
                            SYSTEM.state = 'blocking'
                            for filename in filenames:
                                dst = pjoin(PATH.RAW, '.'.join(pbasename(
                                    filename).split('.')[:-1]))
                                res = CLI.CSLOL.import_fantome(
                                    src=filename,
                                    dst=dst,
                                    game=SYSTEM.settings['game'],
                                    noTFT=not SYSTEM.settings['extra_game_modes']
                                )
                                if res:
                                    new = True
                                    for m in MOD.mods:
                                        if m.path == dst:
                                            new = False
                                            break
                                    if new:
                                        MOD.mods.append(MOD(path=dst))
                                    SYSTEM.save_profile()
                                    LOG.write(f'Imported {filename}')
                                else:
                                    LOG.write(
                                        f'Import failed {filename}. File broken or not fantome file.')
                            SYSTEM.state = 'idle'
                            refresh_mod_list()

                    Thread(
                        target=import_thread,
                        args=(),
                        daemon=True
                    ).start()

                GUI.load_image(
                    path=pjoin('modpage', 'import.png'),
                    key='import',
                    w=128 - 6,
                    h=144
                )
                self.importbutton = self.modpage.create_image(
                    (12, 12),
                    image=GUI.cache['import'],
                    anchor=NW
                )
                self.modpage.tag_bind(
                    self.importbutton, '<Button-1>', on_importmod)

            def create_create_button():
                def on_createmod(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                        return

                    def create_create_window():
                        def create_topbar():
                            def create_bar():
                                def update_bar_gif():
                                    if self.createwindow:
                                        self.createwindow.topbar.current += 1
                                        if self.createwindow.topbar.current == self.createwindow.topbar.max:
                                            self.createwindow.topbar.current = 0
                                        self.createwindow.topbar.itemconfig(
                                            self.createwindow.topbarbg, image=GUI.cache['createtopbar'+str(self.createwindow.topbar.current)])
                                        self.createwindow.topbar.after(
                                            self.createwindow.topbar.delay, update_bar_gif)

                                self.createwindow.topbar = Canvas(
                                    master=self.createwindow,
                                    height=32,
                                    highlightthickness=1,
                                    highlightbackground=GUI.configs['border_bg'],
                                    highlightcolor=GUI.configs['border_bg']
                                )
                                self.createwindow.topbar.pack(
                                    side=TOP, fill=X)
                                if not GUI.configs['animated_topbar']:
                                    GUI.load_image(
                                        path=pjoin(
                                            'modpage', 'createwindow', 'topbar', 'bg.png'),
                                        key='createtopbar',
                                        w=1116,
                                        h=32+2
                                    )
                                    self.createwindow.topbar.create_image(
                                        (0, 0),
                                        image=GUI.cache['createtopbar'],
                                        anchor=NW
                                    )
                                else:
                                    GUI.load_image_gif(
                                        path=pjoin(
                                            'modpage', 'createwindow', 'topbar', 'bg.gif'),
                                        key='createtopbar',
                                        w=1116,
                                        h=32+2
                                    )
                                    self.createwindow.topbar.current = 0
                                    self.createwindow.topbar.max = GUI.cache['createtopbar#max']
                                    self.createwindow.topbar.delay = GUI.cache['createtopbar#delay']
                                    self.createwindow.topbarbg = self.createwindow.topbar.create_image(
                                        (0, 0),
                                        image=GUI.cache['createtopbar0'],
                                        anchor=NW
                                    )
                                    update_bar_gif()

                            def create_cancel_button():
                                def on_cancelwindow(e):
                                    self.createwindow.destroy()
                                    self.createwindow = None

                                GUI.load_image(
                                    path=pjoin('modpage', 'createwindow',
                                               'topbar', 'cancel.png'),
                                    key='createcancel',
                                    w=32,
                                    h=32
                                )
                                cancel = self.createwindow.topbar.create_image(
                                    (600-32-12, 0),
                                    image=GUI.cache['createcancel'],
                                    anchor=NW
                                )
                                self.createwindow.topbar.tag_bind(cancel,
                                                                  '<Button-1>', on_cancelwindow)

                            def create_confirm_button():
                                def on_confirmwindow(e):
                                    name = self.createwindow.nameentry.get()
                                    author = self.createwindow.authorentry.get()
                                    version = self.createwindow.versionentry.get()
                                    desc = self.createwindow.descentry.get()
                                    if name == '' or author == '' or version == '':
                                        return
                                    path = pjoin(
                                        PATH.APP, 'raw', name)
                                    if not pexists(path):
                                        mkdir(path)
                                    if not pexists(pjoin(path, 'META')):
                                        mkdir(pjoin(path, 'META'))
                                    if not pexists(pjoin(path, 'WAD')):
                                        mkdir(pjoin(path, 'WAD'))
                                    infos = {
                                        'Name': name,
                                        'Author': author,
                                        'Version': version,
                                        'Description': desc
                                    }
                                    with open(pjoin(path, 'META', 'info.json'), 'w+', encoding='utf-8') as f:
                                        jdump(infos, f, indent=4)

                                    if self.createwindow.image:
                                        copy(self.createwindow.image, pjoin(
                                            path, 'META', 'image.png'))
                                    MOD.mods.append(MOD(path=path))
                                    SYSTEM.save_profile()
                                    LOG.write(
                                        f'Created {pbasename(path)}')
                                    self.createwindow.destroy()
                                    self.createwindow = None

                                    refresh_mod_list()

                                GUI.load_image(
                                    path=pjoin('modpage', 'createwindow',
                                               'topbar', 'confirm.png'),
                                    key='createconfirm',
                                    w=32,
                                    h=32
                                )
                                confirm = self.createwindow.topbar.create_image(
                                    (600-64-24, 0),
                                    image=GUI.cache['createconfirm'],
                                    anchor=NW
                                )
                                self.createwindow.topbar.tag_bind(
                                    confirm, '<Button-1>', on_confirmwindow)

                            create_bar()
                            create_cancel_button()
                            create_confirm_button()

                        def create_create_page():
                            def on_changeimage(e):
                                self.createwindow.needfocus = False
                                filename = askopenfilename(
                                    title='Select PNG',
                                    parent=self.root,
                                    filetypes=[
                                        ('PNG files', '*.png')
                                    ]
                                )
                                if filename != '':
                                    self.createwindow.image = filename
                                    GUI.load_image(
                                        path=self.createwindow.image,
                                        key='createpreview',
                                        w=256,
                                        h=144,
                                        reload=True
                                    )
                                    self.createwindow.createpage.itemconfig(
                                        self.createwindow.createpage.createimage,
                                        image=GUI.cache['createpreview']
                                    )
                                else:
                                    self.createwindow.image = None
                                self.createwindow.needfocus = True
                                self.createwindow.focus_force()

                            def create_bg():
                                self.createwindow.createpage = Canvas(
                                    master=self.createwindow,
                                    height=360-32,
                                    highlightthickness=1,
                                    highlightbackground=GUI.configs['border_bg'],
                                    highlightcolor=GUI.configs['border_bg']
                                )
                                self.createwindow.createpage.pack(fill=BOTH)
                                GUI.load_image(
                                    path=pjoin('modpage', 'createwindow',
                                               'createpage', 'bg.png'),
                                    key='createpage',
                                    w=600,
                                    h=360+2
                                )
                                self.createwindow.createpagebg = self.createwindow.createpage.create_image(
                                    (0, 0),
                                    image=GUI.cache['createpage'],
                                    anchor=NW
                                )

                            def create_page():
                                self.createwindow.createpage.create_text(
                                    (12, 12),
                                    font=self.mainfont,
                                    text='Name:',
                                    anchor=NW,
                                    justify=LEFT,
                                    fill=GUI.configs['create_text_fg']
                                )
                                self.createwindow.createpage.create_text(
                                    (12, 50),
                                    font=self.mainfont,
                                    text='Author:',
                                    anchor=NW,
                                    justify=LEFT,
                                    fill=GUI.configs['create_text_fg']
                                )
                                self.createwindow.createpage.create_text(
                                    (12, 88),
                                    font=self.mainfont,
                                    text='Version:',
                                    anchor=NW,
                                    justify=LEFT,
                                    fill=GUI.configs['create_text_fg']
                                )
                                self.createwindow.createpage.create_text(
                                    (12, 126),
                                    font=self.mainfont,
                                    text='Description:',
                                    anchor=NW,
                                    justify=LEFT,
                                    fill=GUI.configs['create_text_fg']
                                )

                                self.createwindow.nameentry = Entry(
                                    master=self.createwindow.createpage,
                                    font=self.mainfont,
                                    width=42,
                                    bg=GUI.configs['textfield_bg'],
                                    fg=GUI.configs['create_text_fg'],
                                    insertbackground=GUI.configs['create_text_fg']
                                )
                                self.createwindow.authorentry = Entry(
                                    master=self.createwindow.createpage,
                                    font=self.mainfont,
                                    width=42,
                                    bg=GUI.configs['textfield_bg'],
                                    fg=GUI.configs['create_text_fg'],
                                    insertbackground=GUI.configs['create_text_fg']
                                )
                                self.createwindow.versionentry = Entry(
                                    master=self.createwindow.createpage,
                                    font=self.mainfont,
                                    width=42,
                                    bg=GUI.configs['textfield_bg'],
                                    fg=GUI.configs['create_text_fg'],
                                    insertbackground=GUI.configs['create_text_fg']
                                )
                                self.createwindow.descentry = Entry(
                                    master=self.createwindow.createpage,
                                    font=self.mainfont,
                                    width=42,
                                    bg=GUI.configs['textfield_bg'],
                                    fg=GUI.configs['create_text_fg'],
                                    insertbackground=GUI.configs['create_text_fg']
                                )

                                self.createwindow.createpage.create_window(
                                    (150, 12),
                                    window=self.createwindow.nameentry,
                                    anchor=NW
                                )
                                self.createwindow.createpage.create_window(
                                    (150, 50),
                                    window=self.createwindow.authorentry,
                                    anchor=NW
                                )
                                self.createwindow.createpage.create_window(
                                    (150, 88),
                                    window=self.createwindow.versionentry,
                                    anchor=NW
                                )
                                self.createwindow.createpage.create_window(
                                    (150, 126),
                                    window=self.createwindow.descentry,
                                    anchor=NW
                                )

                                self.createwindow.createpage.createimage = self.createwindow.createpage.create_image(
                                    ((600 - 256) // 2, 170),
                                    image=GUI.cache['nonimage'],
                                    anchor=NW
                                )
                                self.createwindow.createpage.tag_bind(
                                    self.createwindow.createpage.createimage,
                                    '<Button-1>',
                                    on_changeimage
                                )

                                self.createwindow.nameentry.bind(
                                    '<ButtonRelease-1>', lambda e: self.createwindow.nameentry.focus())
                                self.createwindow.authorentry.bind(
                                    '<ButtonRelease-1>', lambda e: self.createwindow.authorentry.focus())
                                self.createwindow.versionentry.bind(
                                    '<ButtonRelease-1>', lambda e: self.createwindow.versionentry.focus())
                                self.createwindow.descentry.bind(
                                    '<ButtonRelease-1>', lambda e: self.createwindow.descentry.focus())

                                def on_tab(e):
                                    w = self.createwindow.focus_get()
                                    if w is self.createwindow.nameentry:
                                        self.createwindow.createpage.focus_set()
                                        self.createwindow.createpage.after(
                                            10, lambda: self.createwindow.authorentry.focus())
                                    elif w is self.createwindow.authorentry:
                                        self.createwindow.createpage.focus_set()
                                        self.createwindow.createpage.after(
                                            10, lambda: self.createwindow.versionentry.focus())
                                    elif w is self.createwindow.versionentry:
                                        self.createwindow.createpage.focus_set()
                                        self.createwindow.createpage.after(
                                            10, lambda: self.createwindow.descentry.focus())
                                    else:
                                        self.createwindow.createpage.focus_set()
                                        self.createwindow.createpage.after(
                                            10, lambda: self.createwindow.nameentry.focus())
                                self.createwindow.unbind_all("<<NextWindow>>")
                                self.createwindow.unbind_all("<<PrevWindow>>")
                                self.createwindow.bind(
                                    '<<NextWindow>>', on_tab)

                            create_bg()
                            create_page()

                        def focus(e):
                            if self.createwindow.needfocus:
                                self.createwindow.focus_force()

                        if self.createwindow:
                            self.createwindow.destroy()

                        self.createwindow = Toplevel(
                            master=self.root,
                        )
                        self.createwindow.geometry(
                            f'{600}x{360}+{int((self.root.winfo_screenwidth() - 600) / 2)}+{int((self.root.winfo_screenheight() - 360) / 2)}')
                        self.createwindow.resizable(False, False)
                        self.createwindow.overrideredirect(True)
                        self.createwindow.needfocus = True
                        self.createwindow.bind('<FocusOut>', focus)
                        self.createwindow.image = None

                        create_topbar()
                        create_create_page()

                    create_create_window()

                GUI.load_image(
                    path=pjoin('modpage', 'create.png'),
                    key='create',
                    w=128 - 6,
                    h=144
                )
                self.createbutton = self.modpage.create_image(
                    (12 + 256/2 + 6, 12),
                    image=GUI.cache['create'],
                    anchor=NW
                )
                self.modpage.tag_bind(
                    self.createbutton, '<Button-1>', on_createmod)

            def vector_to_matrix(value, width):
                return (
                    (value // width),
                    (value % width)
                )

            def fit_text(text, width):
                if len(text) * 10 <= width:
                    return [text]
                m = width // 10
                lines = []
                temp = text
                while len(temp) > m:
                    lines.append(temp[:m])
                    temp = temp[m:]
                if temp != '':
                    lines.append(temp)
                if len(lines) > 3:
                    lines = lines[:3]
                    lines[2] = lines[2][:-3] + '...'
                return lines

            def on_mousewheel(e):
                scroll = -1 if e.delta > 0 else 1
                self.modpage.yview_scroll(scroll, 'units')
                y = int(self.modpage.yview()[0] *
                        self.modpage.bbox(self.old_tags)[3])
                self.modpage.coords(self.modpagebg, 0, y)
                self.modpage.coords(
                    self.modpage.scrollbarwindow, 1116-32, y)

            def on_selectmod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return
                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.border == t or m.textbg == t:
                        break
                m.enable = not m.enable

            def on_removemod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return

                SYSTEM.state = 'blocking'
                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.remove == t:
                        break

                MOD.mods.remove(m)
                rmtree(m.path)
                SYSTEM.save_profile()
                SYSTEM.state = 'idle'
                refresh_mod_list()
                LOG.write(f'Removed {pbasename(m.path)}')

            def on_locationmod(e):
                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.location == t:
                        break
                startfile(m.path)

            def on_editmod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return

                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.edit == t:
                        break

                def create_edit_window():
                    def create_topbar():
                        def create_bar():
                            def update_bar_gif():
                                if self.editwindow:
                                    self.editwindow.topbar.current += 1
                                    if self.editwindow.topbar.current == self.editwindow.topbar.max:
                                        self.editwindow.topbar.current = 0
                                    self.editwindow.topbar.itemconfig(
                                        self.editwindow.topbarbg, image=GUI.cache['edittopbar'+str(self.editwindow.topbar.current)])
                                    self.editwindow.topbar.after(
                                        self.editwindow.topbar.delay, update_bar_gif)

                            self.editwindow.topbar = Canvas(
                                master=self.editwindow,
                                height=32,
                                highlightthickness=1,
                                highlightbackground=GUI.configs['border_bg'],
                                highlightcolor=GUI.configs['border_bg']
                            )
                            self.editwindow.topbar.pack(side=TOP, fill=X)
                            if not GUI.configs['animated_topbar']:
                                GUI.load_image(
                                    path=pjoin('modpage', 'editwindow',
                                               'topbar', 'bg.png'),
                                    key='edittopbar',
                                    w=1116,
                                    h=32+2
                                )
                                self.editwindow.topbar.create_image(
                                    (0, 0),
                                    image=GUI.cache['edittopbar'],
                                    anchor=NW
                                )
                            else:
                                GUI.load_image_gif(
                                    path=pjoin('modpage', 'editwindow',
                                               'topbar', 'bg.gif'),
                                    key='edittopbar',
                                    w=1116,
                                    h=32+2
                                )
                                self.editwindow.topbar.current = 0
                                self.editwindow.topbar.max = GUI.cache['edittopbar#max']
                                self.editwindow.topbar.delay = GUI.cache['edittopbar#delay']
                                self.editwindow.topbarbg = self.editwindow.topbar.create_image(
                                    (0, 0),
                                    image=GUI.cache['edittopbar0'],
                                    anchor=NW
                                )
                                update_bar_gif()

                        def create_cancel_button():
                            def on_cancelwindow(e):
                                self.editwindow.destroy()
                                self.editwindow = None

                            GUI.load_image(
                                path=pjoin('modpage', 'editwindow',
                                           'topbar', 'cancel.png'),
                                key='editcancel',
                                w=32,
                                h=32
                            )
                            cancel = self.editwindow.topbar.create_image(
                                (600-32-12, 0),
                                image=GUI.cache['editcancel'],
                                anchor=NW
                            )
                            self.editwindow.topbar.tag_bind(cancel,
                                                            '<Button-1>', on_cancelwindow)

                        def create_confirm_button():
                            def on_confirmwindow(e):
                                name = self.editwindow.nameentry.get()
                                author = self.editwindow.authorentry.get()
                                version = self.editwindow.versionentry.get()
                                desc = self.editwindow.descentry.get()
                                if name == '' or author == '' or version == '':
                                    return
                                m.edit_infos(
                                    name=name,
                                    author=author,
                                    version=version,
                                    desc=desc
                                )
                                if self.editwindow.image:
                                    m.edit_image(self.editwindow.image)

                                self.editwindow.destroy()
                                self.editwindow = None
                                refresh_mod_list()

                            GUI.load_image(
                                path=pjoin('modpage', 'editwindow',
                                           'topbar', 'confirm.png'),
                                key='editconfirm',
                                w=32,
                                h=32
                            )
                            confirm = self.editwindow.topbar.create_image(
                                (600-64-24, 0),
                                image=GUI.cache['editconfirm'],
                                anchor=NW
                            )
                            self.editwindow.topbar.tag_bind(
                                confirm, '<Button-1>', on_confirmwindow)

                        create_bar()
                        create_cancel_button()
                        create_confirm_button()

                    def create_edit_page():
                        def on_changeimage(e):
                            self.editwindow.needfocus = False
                            filename = askopenfilename(
                                title='Select PNG',
                                parent=self.root,
                                filetypes=[
                                    ('PNG files', '*.png')
                                ]
                            )
                            if filename != '':
                                self.editwindow.image = filename
                                GUI.load_image(
                                    path=self.editwindow.image,
                                    key='editpreview',
                                    w=256,
                                    h=144,
                                    reload=True
                                )
                                self.editwindow.editpage.itemconfig(
                                    self.editwindow.editpage.editimage,
                                    image=GUI.cache['editpreview']
                                )
                            else:
                                self.editwindow.image = None
                            self.editwindow.needfocus = True
                            self.editwindow.focus_force()

                        def create_bg():
                            self.editwindow.editpage = Canvas(
                                master=self.editwindow,
                                height=360-32,
                                highlightthickness=1,
                                highlightbackground=GUI.configs['border_bg'],
                                highlightcolor=GUI.configs['border_bg']
                            )
                            self.editwindow.editpage.pack(fill=BOTH)
                            GUI.load_image(
                                path=pjoin('modpage', 'editwindow',
                                           'editpage', 'bg.png'),
                                key='editpage',
                                w=600,
                                h=360+2
                            )
                            self.editwindow.editpage.create_image(
                                (0, 0),
                                image=GUI.cache['editpage'],
                                anchor=NW
                            )

                        def create_page():
                            self.editwindow.editpage.create_text(
                                (12, 12),
                                font=self.mainfont,
                                text='Name:',
                                anchor=NW,
                                justify=LEFT,
                                fill=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.editpage.create_text(
                                (12, 50),
                                font=self.mainfont,
                                text='Author:',
                                anchor=NW,
                                justify=LEFT,
                                fill=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.editpage.create_text(
                                (12, 88),
                                font=self.mainfont,
                                text='Version:',
                                anchor=NW,
                                justify=LEFT,
                                fill=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.editpage.create_text(
                                (12, 126),
                                font=self.mainfont,
                                text='Description:',
                                anchor=NW,
                                justify=LEFT,
                                fill=GUI.configs['edit_text_fg']
                            )

                            self.editwindow.nameentry = Entry(
                                master=self.editwindow.editpage,
                                font=self.mainfont,
                                width=42,
                                bg=GUI.configs['textfield_bg'],
                                fg=GUI.configs['edit_text_fg'],
                                insertbackground=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.nameentry.insert(
                                0, m.infos['Name'])
                            self.editwindow.authorentry = Entry(
                                master=self.editwindow.editpage,
                                font=self.mainfont,
                                width=42,
                                bg=GUI.configs['textfield_bg'],
                                fg=GUI.configs['edit_text_fg'],
                                insertbackground=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.authorentry.insert(
                                0, m.infos['Author'])

                            self.editwindow.versionentry = Entry(
                                master=self.editwindow.editpage,
                                font=self.mainfont,
                                width=42,
                                bg=GUI.configs['textfield_bg'],
                                fg=GUI.configs['edit_text_fg'],
                                insertbackground=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.versionentry.insert(
                                0, m.infos['Version'])

                            self.editwindow.descentry = Entry(
                                master=self.editwindow.editpage,
                                font=self.mainfont,
                                width=42,
                                bg=GUI.configs['textfield_bg'],
                                fg=GUI.configs['edit_text_fg'],
                                insertbackground=GUI.configs['edit_text_fg']
                            )
                            self.editwindow.descentry.insert(
                                0, m.infos['Description'])

                            self.editwindow.editpage.create_window(
                                (150, 12),
                                window=self.editwindow.nameentry,
                                anchor=NW,

                            )
                            self.editwindow.editpage.create_window(
                                (150, 50),
                                window=self.editwindow.authorentry,
                                anchor=NW
                            )
                            self.editwindow.editpage.create_window(
                                (150, 88),
                                window=self.editwindow.versionentry,
                                anchor=NW
                            )
                            self.editwindow.editpage.create_window(
                                (150, 126),
                                window=self.editwindow.descentry,
                                anchor=NW
                            )

                            self.editwindow.editpage.editimage = self.editwindow.editpage.create_image(
                                ((600 - 256) // 2, 170),
                                image=GUI.cache[i] if m.image else GUI.cache['nonimage'],
                                anchor=NW
                            )
                            self.editwindow.editpage.tag_bind(
                                self.editwindow.editpage.editimage,
                                '<Button-1>',
                                on_changeimage
                            )

                            self.editwindow.nameentry.bind(
                                '<ButtonRelease-1>', lambda e: self.editwindow.nameentry.focus())
                            self.editwindow.authorentry.bind(
                                '<ButtonRelease-1>', lambda e: self.editwindow.authorentry.focus())
                            self.editwindow.versionentry.bind(
                                '<ButtonRelease-1>', lambda e: self.editwindow.versionentry.focus())
                            self.editwindow.descentry.bind(
                                '<ButtonRelease-1>', lambda e: self.editwindow.descentry.focus())

                            def on_tab(e):
                                w = self.editwindow.focus_get()
                                if w is self.editwindow.nameentry:
                                    self.editwindow.editpage.focus_set()
                                    self.editwindow.editpage.after(
                                        10, lambda: self.editwindow.authorentry.focus())
                                elif w is self.editwindow.authorentry:
                                    self.editwindow.editpage.focus_set()
                                    self.editwindow.editpage.after(
                                        10, lambda: self.editwindow.versionentry.focus())
                                elif w is self.editwindow.versionentry:
                                    self.editwindow.editpage.focus_set()
                                    self.editwindow.editpage.after(
                                        10, lambda: self.editwindow.descentry.focus())
                                else:
                                    self.editwindow.editpage.focus_set()
                                    self.editwindow.editpage.after(
                                        10, lambda: self.editwindow.nameentry.focus())
                            self.editwindow.unbind_all("<<NextWindow>>")
                            self.editwindow.unbind_all("<<PrevWindow>>")
                            self.editwindow.bind(
                                '<<NextWindow>>', on_tab)

                        create_bg()
                        create_page()

                    def focus(e):
                        if self.editwindow.needfocus:
                            self.editwindow.focus_force()

                    if self.editwindow:
                        self.editwindow.destroy()

                    self.editwindow = Toplevel(
                        master=self.root,
                    )
                    self.editwindow.geometry(
                        f'{600}x{360}+{int((self.root.winfo_screenwidth() - 600) / 2)}+{int((self.root.winfo_screenheight() - 360) / 2)}')
                    self.editwindow.resizable(False, False)
                    self.editwindow.overrideredirect(True)
                    self.editwindow.needfocus = True
                    self.editwindow.bind('<FocusOut>', focus)
                    self.editwindow.image = None

                    create_topbar()
                    create_edit_page()

                create_edit_window()

            def on_exportmod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return

                def export_thread():
                    t = e.widget.find_withtag('current')[0]
                    for i in range(0, len(MOD.mods)):
                        m = MOD.mods[i]
                        if m.export == t:
                            break

                    initialfile = f'{m.infos["Name"]} V{m.infos["Version"]} by {m.infos["Author"]}'
                    filetypes = [
                        ('FANTOME file', '.fantome')
                    ]
                    filename = asksaveasfilename(
                        title='Export FANTOME',
                        parent=self.root,
                        initialfile=initialfile,
                        filetypes=filetypes,
                        defaultextension=filetypes
                    )
                    if filename != '':
                        SYSTEM.state = 'blocking'
                        if pexists(filename):
                            remove(filename)
                        res = CLI.CSLOL.export_fantome(
                            src=m.path,
                            dst=filename,
                            game=SYSTEM.settings['game'],
                            noTFT=not SYSTEM.settings['extra_game_modes']
                        )
                        if res:
                            LOG.write(f'Exported {filename}')
                        else:
                            LOG.write(f'Export failed: {filename}')
                        SYSTEM.state = 'idle'

                Thread(
                    target=export_thread(),
                    args=(),
                    daemon=True
                ).start()

            def on_orderupmod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return
                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.left == t:
                        break
                if i != 0:
                    MOD.mods[i], MOD.mods[i -
                                          1] = MOD.mods[i-1], MOD.mods[i]
                    SYSTEM.save_profile()
                    refresh_mod_list()

            def on_orderdownmod(e):
                if SYSTEM.is_running() or SYSTEM.is_blocking() or self.editwindow or self.createwindow:
                    return
                t = e.widget.find_withtag('current')[0]
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    if m.right == t:
                        break
                if i != len(MOD.mods)-1:
                    MOD.mods[i], MOD.mods[i +
                                          1] = MOD.mods[i+1], MOD.mods[i]
                    SYSTEM.save_profile()
                    refresh_mod_list()

            def on_updatepage():
                for m in MOD.mods:
                    if m.enable:
                        self.modpage.itemconfig(
                            m.border, image=GUI.cache['activeborder'])
                        self.modpage.itemconfig(
                            m.textbg, image=GUI.cache['activetextbg' + m.lenlines])
                    else:
                        self.modpage.itemconfig(
                            m.border, image=GUI.cache['border'])
                        self.modpage.itemconfig(
                            m.textbg, image=GUI.cache['textbg' + m.lenlines])
                self.modpage.after(200, on_updatepage)

            def create_mod_list(tags):
                def on_entermod(e):
                    t = e.widget.find_withtag('current')[0]
                    for i in range(0, len(MOD.mods)):
                        m = MOD.mods[i]
                        temp = [
                            MOD.mods[i].border,
                            MOD.mods[i].textbg,
                            MOD.mods[i].text,
                            MOD.mods[i].remove,
                            MOD.mods[i].location,
                            MOD.mods[i].edit,
                            MOD.mods[i].export,
                            MOD.mods[i].left,
                            MOD.mods[i].right
                        ]
                        if t in temp:
                            break
                    if not m.state:
                        self.modpage.itemconfig(
                            m.location, state=NORMAL
                        )
                        self.modpage.itemconfig(
                            m.edit, state=NORMAL
                        )
                        self.modpage.itemconfig(
                            m.export, state=NORMAL
                        )
                        self.modpage.itemconfig(
                            m.remove, state=NORMAL
                        )
                        self.modpage.itemconfig(
                            m.left, state=NORMAL
                        )
                        self.modpage.itemconfig(
                            m.right, state=NORMAL
                        )
                        m.state = True

                def on_leavemod(e):
                    t = e.widget.find_withtag('current')[0]
                    for i in range(0, len(MOD.mods)):
                        m = MOD.mods[i]
                        temp = [
                            MOD.mods[i].border,
                            MOD.mods[i].textbg,
                            MOD.mods[i].text,
                            MOD.mods[i].remove,
                            MOD.mods[i].location,
                            MOD.mods[i].edit,
                            MOD.mods[i].export,
                            MOD.mods[i].left,
                            MOD.mods[i].right
                        ]
                        if t in temp:
                            break

                    if m.state:
                        self.modpage.itemconfig(
                            m.location, state=HIDDEN
                        )
                        self.modpage.itemconfig(
                            m.edit, state=HIDDEN
                        )
                        self.modpage.itemconfig(
                            m.export, state=HIDDEN
                        )
                        self.modpage.itemconfig(
                            m.remove, state=HIDDEN
                        )
                        self.modpage.itemconfig(
                            m.left, state=HIDDEN
                        )
                        self.modpage.itemconfig(
                            m.right, state=HIDDEN
                        )
                        m.state = False

                self.old_tags = tags
                GUI.load_image(
                    path=pjoin('modpage', 'border.png'),
                    key='border',
                    w=256,
                    h=144
                )
                GUI.load_image(
                    path=pjoin('modpage', 'activeborder.png'),
                    key='activeborder',
                    w=256,
                    h=144
                )
                GUI.load_image(
                    path=pjoin('modpage', 'textbg1.png'),
                    key='textbg1',
                    w=256,
                    h=18
                )
                GUI.load_image(
                    path=pjoin('modpage', 'textbg2.png'),
                    key='textbg2',
                    w=256,
                    h=36
                )
                GUI.load_image(
                    path=pjoin('modpage', 'textbg3.png'),
                    key='textbg3',
                    w=256,
                    h=54
                )
                GUI.load_image(
                    path=pjoin('modpage', 'activetextbg1.png'),
                    key='activetextbg1',
                    w=256,
                    h=18
                )
                GUI.load_image(
                    path=pjoin('modpage', 'activetextbg2.png'),
                    key='activetextbg2',
                    w=256,
                    h=36
                )
                GUI.load_image(
                    path=pjoin('modpage', 'activetextbg3.png'),
                    key='activetextbg3',
                    w=256,
                    h=54
                )
                GUI.load_image(
                    path=pjoin('modpage', 'nonimage.png'),
                    key='nonimage',
                    w=256,
                    h=144
                )
                GUI.load_image(
                    path=pjoin('modpage', 'remove.png'),
                    key='remove',
                    w=32,
                    h=32
                )
                GUI.load_image(
                    path=pjoin('modpage', 'location.png'),
                    key='location',
                    w=32,
                    h=32
                )
                GUI.load_image(
                    path=pjoin('modpage', 'edit.png'),
                    key='edit',
                    w=32,
                    h=32
                )
                GUI.load_image(
                    path=pjoin('modpage', 'export.png'),
                    key='export',
                    w=32,
                    h=32
                )
                GUI.load_image(
                    path=pjoin('modpage', 'left.png'),
                    key='left',
                    w=32,
                    h=32
                )
                GUI.load_image(
                    path=pjoin('modpage', 'right.png'),
                    key='right',
                    w=32,
                    h=32
                )
                for i in range(0, len(MOD.mods)):
                    m = MOD.mods[i]
                    r, c = vector_to_matrix(i+1, 4)
                    x = c * (256 + 12) + 12
                    y = r * (144 + 12) + 12
                    key = i
                    if m.image:
                        GUI.load_image(
                            path=m.image,
                            key=key,
                            w=256,
                            h=144,
                            reload=True
                        )
                    else:
                        key = 'nonimage'
                    MOD.mods[i].imagep = self.modpage.create_image(
                        (x, y),
                        image=GUI.cache[key],
                        anchor=NW,
                        tags=tags
                    )
                    MOD.mods[i].border = self.modpage.create_image(
                        (x, y),
                        image=GUI.cache['border'],
                        anchor=NW,
                        tags=tags
                    )
                    fixed = fit_text(m.infos['Name'], 256)
                    m.lenlines = str(len(fixed))
                    MOD.mods[i].textbg = self.modpage.create_image(
                        (x, y + 144 - len(fixed)*18),
                        image=GUI.cache['textbg'+m.lenlines],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].border, '<Button-1>', on_selectmod)
                    self.modpage.tag_bind(
                        MOD.mods[i].textbg, '<Button-1>', on_selectmod)
                    MOD.mods[i].text = self.modpage.create_text(
                        (x + 256 // 2, y + 144 - len(fixed)*18),
                        text='\n'.join(fixed),
                        anchor=N,
                        fill=GUI.configs['modname_text_fg'],
                        justify=CENTER,
                        font=self.mainfont,
                        tags=tags
                    )

                    MOD.mods[i].remove = self.modpage.create_image(
                        (x+256-32, y),
                        image=GUI.cache['remove'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].remove, '<Button-1>', on_removemod
                    )

                    MOD.mods[i].location = self.modpage.create_image(
                        (x, y),
                        image=GUI.cache['location'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].location, '<Button-1>', on_locationmod
                    )

                    MOD.mods[i].edit = self.modpage.create_image(
                        (x, y+32),
                        image=GUI.cache['edit'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].edit, '<Button-1>', on_editmod
                    )

                    MOD.mods[i].export = self.modpage.create_image(
                        (x, y+64),
                        image=GUI.cache['export'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].export, '<Button-1>', on_exportmod
                    )

                    MOD.mods[i].left = self.modpage.create_image(
                        (x+256-32, y+32),
                        image=GUI.cache['left'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].left, '<Button-1>', on_orderupmod
                    )

                    MOD.mods[i].right = self.modpage.create_image(
                        (x+256-32, y+64),
                        image=GUI.cache['right'],
                        anchor=NW,
                        tags=tags
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].right, '<Button-1>', on_orderdownmod
                    )

                    m.state = False
                    self.modpage.itemconfig(
                        m.location, state=HIDDEN
                    )
                    self.modpage.itemconfig(
                        m.edit, state=HIDDEN
                    )
                    self.modpage.itemconfig(
                        m.export, state=HIDDEN
                    )
                    self.modpage.itemconfig(
                        m.remove, state=HIDDEN
                    )
                    self.modpage.itemconfig(
                        m.left, state=HIDDEN
                    )
                    self.modpage.itemconfig(
                        m.right, state=HIDDEN
                    )

                    self.modpage.tag_bind(
                        MOD.mods[i].border,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].textbg,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].text,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].remove,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].location,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].edit,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].export,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].left,
                        '<Enter>', on_entermod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].right,
                        '<Enter>', on_entermod
                    )

                    self.modpage.tag_bind(
                        MOD.mods[i].border,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].textbg,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].text,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].remove,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].location,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].edit,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].export,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].left,
                        '<Leave>', on_leavemod
                    )
                    self.modpage.tag_bind(
                        MOD.mods[i].right,
                        '<Leave>', on_leavemod
                    )

                self.modpage.configure(
                    scrollregion=self.modpage.bbox('all')
                )
                self.modpage.bind('<MouseWheel>', on_mousewheel)
                on_updatepage()

            def refresh_mod_list():
                tag = self.old_tags
                create_mod_list(SYSTEM.now())
                self.modpage.delete(tag)
                self.modpage.update()
                self.modpage.configure(
                    scrollregion=self.modpage.bbox('all')
                )

            def create_scroll_bar():
                def on_clickscroll(e):
                    def update():
                        y = int(self.modpage.yview()[0] *
                                self.modpage.bbox(self.old_tags)[3])
                        self.modpage.coords(self.modpagebg, 0, y)
                        self.modpage.coords(
                            self.modpage.scrollbarwindow, 1116-32, y)

                    self.modpage.scrollbar.bind(
                        '<B1-Motion>', lambda e: self.modpage.after(10, update))

                def update_scrollbar_state():
                    if self.modpage.bbox('all')[3]-10 > 634-64:
                        self.modpage.itemconfig(
                            self.modpage.scrollbarwindow, state=NORMAL)
                    else:
                        self.modpage.itemconfig(
                            self.modpage.scrollbarwindow, state=HIDDEN)
                    self.modpage.after(200, update_scrollbar_state)

                self.modpage.scrollbar = Scrollbar(
                    master=self.modpage,
                    orient=VERTICAL,
                    command=self.modpage.yview,
                    style="My.Vertical.TScrollbar"
                )
                self.modpage.scrollbarwindow = self.modpage.create_window(
                    (1116-32, 0),
                    window=self.modpage.scrollbar,
                    anchor=NW,
                    height=634-64
                )
                self.modpage.configure(
                    yscrollcommand=self.modpage.scrollbar.set
                )
                self.modpage.scrollbar.bind('<MouseWheel>', lambda e: 'break')
                self.modpage.scrollbar.bind('<Button-1>', on_clickscroll)
                update_scrollbar_state()

            create_import_button()
            create_create_button()
            create_mod_list(SYSTEM.now())
            create_scroll_bar()
            GUI.GLOBAL.refresh_mod_list = refresh_mod_list

        create_bg()
        create_page()

    def create_log_page(self):
        def on_mousewheel(e):
            scroll = -1 if e.delta > 0 else 1
            self.logpage.yview_scroll(scroll, 'units')
            y = int(self.logpage.yview()[0] *
                    self.logpage.bbox(self.logtext)[3])
            self.logpage.coords(self.logpagebg, 0, y)
            self.logpage.coords(
                self.logpage.scrollbarwindow, 1116-32, y)

        def create_bg():
            self.logpage = Canvas(
                master=self.root,
                height=634-32,
                highlightthickness=1,
                highlightbackground=GUI.configs['border_bg'],
                highlightcolor=GUI.configs['border_bg']
            )
            self.logpage.pack(fill=BOTH)
            GUI.load_image(
                path=pjoin('logpage', 'bg.png'),
                key='logpage',
                w=1116,
                h=634-32
            )
            self.logpagebg = self.logpage.create_image(
                (0, 0),
                image=GUI.cache['logpage'],
                anchor=NW
            )
            self.logpage.bind('<MouseWheel>', on_mousewheel)

        def create_text():
            def update_text():
                lines = self.logpage.itemcget(self.logtext, 'text').split('\n')
                newlines = list(filter(lambda l: l not in lines, LOG.logs))
                if len(lines) > 0 and len(newlines) > 0 and self.tab == 1:
                    self.logpage.itemconfig(
                        self.logtext, text='\n'.join(lines + newlines))
                    self.logpage.update()
                    self.logpage.configure(
                        scrollregion=self.logpage.bbox('all')
                    )
                    self.logpage.yview_moveto(1.0)
                    y = int(self.logpage.yview()[
                            0] * self.logpage.bbox(self.logtext)[3])
                    self.logpage.coords(
                        self.logpagebg,
                        0,
                        y
                    )
                    self.logpage.coords(
                        self.logpage.scrollbarwindow,
                        1116-32,
                        y
                    )
                self.logpage.after(200, update_text)

            self.logtext = self.logpage.create_text(
                (12, 0),
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['log_text_fg'],
                width=1116
            )
            self.logpage.configure(
                scrollregion=self.logpage.bbox('all')
            )
            update_text()

        def create_scroll_bar():
            def on_clickscroll(e):
                def update():
                    y = int(self.logpage.yview()[0] *
                            self.logpage.bbox(self.logtext)[3])
                    self.logpage.coords(self.logpagebg, 0, y)
                    self.logpage.coords(
                        self.logpage.scrollbarwindow, 1116-32, y)

                self.logpage.scrollbar.bind(
                    '<B1-Motion>', lambda e: self.logpage.after(10, update))

            def update_scrollbar_state():
                if self.logpage.bbox('all')[3]-10 > 634-32:
                    self.logpage.itemconfig(
                        self.logpage.scrollbarwindow, state=NORMAL)
                else:
                    self.logpage.itemconfig(
                        self.logpage.scrollbarwindow, state=HIDDEN)
                self.logpage.after(200, update_scrollbar_state)

            self.logpage.scrollbar = Scrollbar(
                master=self.logpage,
                orient=VERTICAL,
                command=self.logpage.yview,
                style="My.Vertical.TScrollbar"
            )
            self.logpage.scrollbarwindow = self.logpage.create_window(
                (1116-32, 0),
                window=self.logpage.scrollbar,
                anchor=NW,
                height=634-32
            )
            self.logpage.configure(
                yscrollcommand=self.logpage.scrollbar.set
            )
            self.logpage.scrollbar.bind('<MouseWheel>', lambda e: 'break')
            self.logpage.scrollbar.bind('<Button-1>', on_clickscroll)
            update_scrollbar_state()

        create_bg()
        create_text()
        create_scroll_bar()

    def create_setting_page(self):
        def create_bg():
            self.settingpage = Canvas(
                master=self.root,
                height=634-64,
                highlightthickness=1,
                highlightbackground=GUI.configs['border_bg'],
                highlightcolor=GUI.configs['border_bg']
            )
            self.settingpage.pack(fill=BOTH)
            GUI.load_image(
                path=pjoin('settingpage', 'bg.png'),
                key='settingpage',
                w=1116,
                h=634 - 64
            )
            self.settingpage.create_image(
                (0, 0),
                image=GUI.cache['settingpage'],
                anchor=NW
            )

        def create_misc_settings():
            self.settingpage.create_text(
                (12, 12),
                font=self.mainfont,
                anchor=NW,
                fill=GUI.configs['setting_text_fg'],
                text='Misc'
            )

            def create_game_setting():
                def on_browsegame(e):
                    if SYSTEM.is_running() or SYSTEM.is_blocking():
                        return

                    dirname = askdirectory(
                        title='Select LoL\Game folder',
                        parent=self.root
                    )
                    if dirname != '':
                        dirname = dirname.replace('/', '\\')
                        if not pexists(pjoin(dirname, 'League of Legends.exe')):
                            LOG.write(
                                f'Error: No "League of Legends.exe" found in {dirname}'
                            )
                            return
                        SYSTEM.settings['game'] = dirname
                        self.settingpage.itemconfig(
                            self.gamelabel,
                            text=SYSTEM.settings['game']
                        )
                        LOG.write(f'Choosed Game folder {dirname}')
                        SYSTEM.save_settings()

                GUI.load_image(
                    path=pjoin('settingpage', 'browse.png'),
                    key='browse',
                    w=32,
                    h=32
                )
                self.browsebutton = self.settingpage.create_image(
                    (12, 40),
                    image=GUI.cache['browse'],
                    anchor=NW
                )
                text = 'no League of Legends\\Game folder selected'
                if SYSTEM.settings['game'] != '':
                    text = SYSTEM.settings['game']
                self.gamelabel = self.settingpage.create_text(
                    (32+24, 34+12),
                    anchor=NW,
                    font=self.mainfont,
                    text=text,
                    fill=GUI.configs['setting_text_fg']
                )
                self.settingpage.tag_bind(
                    self.browsebutton, '<Button-1>', on_browsegame)

            def create_extramodes_setting():
                def on_toggleextragamemodes(e):
                    SYSTEM.settings['extra_game_modes'] = not SYSTEM.settings['extra_game_modes']
                    self.settingpage.itemconfig(
                        self.settingpage.extragamemodestoggle,
                        image=GUI.cache['on'] if SYSTEM.settings['extra_game_modes'] else GUI.cache['off']
                    )
                    SYSTEM.save_settings()

                self.extramodes = self.settingpage.create_text(
                    (12, 76),
                    text='Extra game modes:',
                    anchor=NW,
                    font=self.mainfont,
                    fill=GUI.configs['setting_text_fg']
                )
                if SYSTEM.settings['extra_game_modes']:
                    self.settingpage.extragamemodestoggle = self.settingpage.create_image(
                        (300, 70),
                        image=GUI.cache['on'],
                        anchor=NW
                    )
                else:
                    self.settingpage.extragamemodestoggle = self.settingpage.create_image(
                        (300, 70),
                        image=GUI.cache['off'],
                        anchor=NW
                    )
                self.settingpage.tag_bind(
                    self.settingpage.extragamemodestoggle, '<Button-1>', on_toggleextragamemodes)

            create_game_setting()
            create_extramodes_setting()

        def create_theme_settings():
            def on_changetheme(e):
                themes = list(filter(lambda f: pisdir(
                    pjoin(PATH.UI, f)), listdir(PATH.UI)))
                if SYSTEM.settings['theme'] in themes:
                    i = themes.index(SYSTEM.settings['theme'])+1
                    if i == len(themes):
                        i = 0
                    SYSTEM.settings['theme'] = themes[i]
                else:
                    SYSTEM.settings['theme'] = themes[0]

                SYSTEM.save_settings()

                Popen([pjoin(PATH.APP, 'cslmao.exe')],
                      start_new_session=True)
                self.root.quit()

            self.settingpage.create_text(
                (554, 12),
                font=self.mainfont,
                anchor=NW,
                fill=GUI.configs['setting_text_fg'],
                text='Theme (restart needed)'
            )
            self.settingpage.themebutton = self.settingpage.create_text(
                (834, 12),
                font=self.mainfont,
                anchor=NW,
                fill=GUI.configs['setting_text_fg'],
                text=SYSTEM.settings['theme']
            )
            self.settingpage.tag_bind(
                self.settingpage.themebutton, '<Button-1>', on_changetheme)

            def on_toggleanimatedtopbar(e):
                GUI.configs['animated_topbar'] = not GUI.configs['animated_topbar']
                self.settingpage.itemconfig(
                    self.settingpage.animatedtopbar,
                    image=GUI.cache['on'] if GUI.configs['animated_topbar'] else GUI.cache['off']
                )
                GUI.save_configs()

            def on_changecolor(e):
                t = e.widget.find_withtag('current')[0]
                if t == self.settingpage.borderbg:
                    c = askcolor(
                        title='Select border color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.borderbg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.borderbg,
                            fill=c
                        )
                        GUI.configs['border_bg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.textfieldbg:
                    c = askcolor(
                        title='Select textfield color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.textfieldbg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.textfieldbg,
                            fill=c
                        )
                        GUI.configs['textfield_bg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.modnametextfg:
                    c = askcolor(
                        title='Select mod name color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.modnametextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.modnametextfg,
                            fill=c
                        )
                        GUI.configs['modname_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.edittextfg:
                    c = askcolor(
                        title='Select edit window text color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.edittextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.edittextfg,
                            fill=c
                        )
                        GUI.configs['edit_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.createtextfg:
                    c = askcolor(
                        title='Select create window text color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.createtextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.createtextfg,
                            fill=c
                        )
                        GUI.configs['create_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.logtextfg:
                    c = askcolor(
                        title='Select log text color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.logtextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.logtextfg,
                            fill=c
                        )
                        GUI.configs['log_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.minilogtextfg:
                    c = askcolor(
                        title='Select mini-log text color color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.minilogtextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.minilogtextfg,
                            fill=c
                        )
                        GUI.configs['minilog_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.settingtextfg:
                    c = askcolor(
                        title='Select setting text color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.settingtextfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.settingtextfg,
                            fill=c
                        )
                        GUI.configs['setting_text_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.scrollbarfg:
                    c = askcolor(
                        title='Select scrollbar foreground color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.scrollbarfg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.scrollbarfg,
                            fill=c
                        )
                        GUI.configs['scrollbar_fg'] = c
                        GUI.save_configs()
                elif t == self.settingpage.scrollbarbg:
                    c = askcolor(
                        title='Select scrollbar background color',
                        parent=self.root,
                        color=self.settingpage.itemcget(
                            self.settingpage.scrollbarbg, 'fill')
                    )[1]
                    if c:
                        self.settingpage.itemconfig(
                            self.settingpage.scrollbarbg,
                            fill=c
                        )
                        GUI.configs['scrollbar_bg'] = c
                        GUI.save_configs()

            self.settingpage.create_text(
                (554, 48),
                text='Animated topbar:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 84),
                text='Borders color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 120),
                text='Textfield color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 156),
                text='Mod name color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 192),
                text='Create window text color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 228),
                text='Edit window text color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 264),
                text='Log text color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 300),
                text='Mini-log text color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 336),
                text='Setting text color:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 372),
                text='Scrollbar foreground:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )
            self.settingpage.create_text(
                (554, 408),
                text='Scrollbar background:',
                anchor=NW,
                font=self.mainfont,
                fill=GUI.configs['setting_text_fg']
            )

            self.settingpage.animatedtopbar = self.settingpage.create_image(
                (834, 42),
                image=GUI.cache['on'] if GUI.configs['animated_topbar'] else GUI.cache['off'],
                anchor=NW
            )
            self.settingpage.borderbg = self.settingpage.create_rectangle(
                (834, 78, 834+32, 78+24),
                fill=GUI.configs['border_bg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.textfieldbg = self.settingpage.create_rectangle(
                (834, 114, 834+32, 114+24),
                fill=GUI.configs['textfield_bg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.modnametextfg = self.settingpage.create_rectangle(
                (834, 150, 834+32, 150+24),
                fill=GUI.configs['modname_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.createtextfg = self.settingpage.create_rectangle(
                (834, 186, 834+32, 186+24),
                fill=GUI.configs['create_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.edittextfg = self.settingpage.create_rectangle(
                (834, 222, 834+32, 222+24),
                fill=GUI.configs['edit_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.logtextfg = self.settingpage.create_rectangle(
                (834, 258, 834+32, 258+24),
                fill=GUI.configs['log_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.minilogtextfg = self.settingpage.create_rectangle(
                (834, 294, 834+32, 294+24),
                fill=GUI.configs['minilog_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.settingtextfg = self.settingpage.create_rectangle(
                (834, 330, 834+32, 330+24),
                fill=GUI.configs['setting_text_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.scrollbarfg = self.settingpage.create_rectangle(
                (834, 366, 834+32, 366+24),
                fill=GUI.configs['scrollbar_fg'],
                outline=GUI.configs['border_bg']
            )
            self.settingpage.scrollbarbg = self.settingpage.create_rectangle(
                (834, 402, 834+32, 402+24),
                fill=GUI.configs['scrollbar_bg'],
                outline=GUI.configs['border_bg']
            )

            self.settingpage.tag_bind(
                self.settingpage.animatedtopbar,
                '<Button-1>',
                on_toggleanimatedtopbar
            )
            self.settingpage.tag_bind(
                self.settingpage.borderbg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.textfieldbg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.modnametextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.edittextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.createtextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.logtextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.minilogtextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.settingtextfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.scrollbarfg,
                '<Button-1>',
                on_changecolor
            )
            self.settingpage.tag_bind(
                self.settingpage.scrollbarbg,
                '<Button-1>',
                on_changecolor
            )

        def create_beforerun_settings():
            self.settingpage.create_text(
                (12, 132),
                font=self.mainfont,
                anchor=NW,
                fill=GUI.configs['setting_text_fg'],
                text='Before running'
            )

            def on_toggleautopackraw(e):
                SYSTEM.settings['auto_pack_raw'] = not SYSTEM.settings['auto_pack_raw']
                self.settingpage.itemconfig(
                    self.settingpage.autopackrawtoggle,
                    image=GUI.cache['on'] if SYSTEM.settings['auto_pack_raw'] else GUI.cache['off']
                )
                if not SYSTEM.settings['auto_pack_raw']:
                    SYSTEM.settings['auto_update_skl'] = False
                    self.settingpage.itemconfig(
                        self.settingpage.autoupdateskltoggle,
                        image=GUI.cache['off']
                    )
                    SYSTEM.settings['auto_update_anm'] = False
                    self.settingpage.itemconfig(
                        self.settingpage.autoupdateanmtoggle,
                        image=GUI.cache['off']
                    )
                    SYSTEM.settings['auto_convert_py'] = False
                    self.settingpage.itemconfig(
                        self.settingpage.autoconvertpytoggle,
                        image=GUI.cache['off']
                    )
                SYSTEM.save_settings()

            def on_toggleautoupdateskl(e):
                SYSTEM.settings['auto_update_skl'] = not SYSTEM.settings['auto_update_skl']
                self.settingpage.itemconfig(
                    self.settingpage.autoupdateskltoggle,
                    image=GUI.cache['on'] if SYSTEM.settings['auto_update_skl'] else GUI.cache['off']
                )
                if SYSTEM.settings['auto_update_skl']:
                    SYSTEM.settings['auto_pack_raw'] = True
                    self.settingpage.itemconfig(
                        self.settingpage.autopackrawtoggle,
                        image=GUI.cache['on']
                    )
                SYSTEM.save_settings()

            def on_toggleautoupdateanm(e):
                SYSTEM.settings['auto_update_anm'] = not SYSTEM.settings['auto_update_anm']
                self.settingpage.itemconfig(
                    self.settingpage.autoupdateanmtoggle,
                    image=GUI.cache['on'] if SYSTEM.settings['auto_update_anm'] else GUI.cache['off']
                )
                if SYSTEM.settings['auto_update_anm']:
                    SYSTEM.settings['auto_pack_raw'] = True
                    self.settingpage.itemconfig(
                        self.settingpage.autopackrawtoggle,
                        image=GUI.cache['on']
                    )
                SYSTEM.save_settings()

            def on_toggleautoconvertpy(e):
                SYSTEM.settings['auto_convert_py'] = not SYSTEM.settings['auto_convert_py']
                self.settingpage.itemconfig(
                    self.settingpage.autoconvertpytoggle,
                    image=GUI.cache['on'] if SYSTEM.settings['auto_convert_py'] else GUI.cache['off']
                )
                if SYSTEM.settings['auto_convert_py']:
                    SYSTEM.settings['auto_pack_raw'] = True
                    self.settingpage.itemconfig(
                        self.settingpage.autopackrawtoggle,
                        image=GUI.cache['on']
                    )
                SYSTEM.save_settings()

            self.settingpage.autopackrawlabel = self.settingpage.create_text(
                (12, 168),
                text='Auto pack RAW to WAD',
                fill=GUI.configs['setting_text_fg'],
                font=self.mainfont,
                anchor=NW
            )
            self.settingpage.autoupdateskl = self.settingpage.create_text(
                (12, 204),
                text='Auto update SKL',
                fill=GUI.configs['setting_text_fg'],
                font=self.mainfont,
                anchor=NW
            )
            self.settingpage.autoupdateanm = self.settingpage.create_text(
                (12, 240),
                text='Auto fix ANM 1E byte',
                fill=GUI.configs['setting_text_fg'],
                font=self.mainfont,
                anchor=NW
            )
            self.settingpage.autoupdateanm = self.settingpage.create_text(
                (12, 278),
                text='Auto convert PY to BIN',
                fill=GUI.configs['setting_text_fg'],
                font=self.mainfont,
                anchor=NW
            )

            if SYSTEM.settings['auto_pack_raw']:
                self.settingpage.autopackrawtoggle = self.settingpage.create_image(
                    (300, 162),
                    image=GUI.cache['on'],
                    anchor=NW
                )
            else:
                self.settingpage.autopackrawtoggle = self.settingpage.create_image(
                    (300, 162),
                    image=GUI.cache['off'],
                    anchor=NW
                )
            self.settingpage.tag_bind(
                self.settingpage.autopackrawtoggle, '<Button-1>', on_toggleautopackraw)

            if SYSTEM.settings['auto_update_skl']:
                self.settingpage.autoupdateskltoggle = self.settingpage.create_image(
                    (300, 198),
                    image=GUI.cache['on'],
                    anchor=NW
                )
            else:
                self.settingpage.autoupdateskltoggle = self.settingpage.create_image(
                    (300, 198),
                    image=GUI.cache['off'],
                    anchor=NW
                )
            self.settingpage.tag_bind(
                self.settingpage.autoupdateskltoggle, '<Button-1>', on_toggleautoupdateskl)

            if SYSTEM.settings['auto_update_anm']:
                self.settingpage.autoupdateanmtoggle = self.settingpage.create_image(
                    (300, 234),
                    image=GUI.cache['on'],
                    anchor=NW
                )
            else:
                self.settingpage.autoupdateanmtoggle = self.settingpage.create_image(
                    (300, 234),
                    image=GUI.cache['off'],
                    anchor=NW
                )
            self.settingpage.tag_bind(
                self.settingpage.autoupdateanmtoggle, '<Button-1>', on_toggleautoupdateanm)

            if SYSTEM.settings['auto_convert_py']:
                self.settingpage.autoconvertpytoggle = self.settingpage.create_image(
                    (300, 270),
                    image=GUI.cache['on'],
                    anchor=NW
                )
            else:
                self.settingpage.autoconvertpytoggle = self.settingpage.create_image(
                    (300, 270),
                    image=GUI.cache['off'],
                    anchor=NW
                )
            self.settingpage.tag_bind(
                self.settingpage.autoconvertpytoggle, '<Button-1>', on_toggleautoconvertpy)

        create_bg()
        GUI.load_image(
            path=pjoin('settingpage', 'off.png'),
            key='off',
            w=32,
            h=32
        )
        GUI.load_image(
            path=pjoin('settingpage', 'on.png'),
            key='on',
            w=32,
            h=32
        )
        create_misc_settings()
        create_theme_settings()
        create_beforerun_settings()

    def create_mini_log(self):
        def create_bar():
            def on_clickminilog(e):
                self.tab = 1
                self.update_tab()

            self.minilog = Canvas(
                master=self.root,
                height=32,
                highlightthickness=1,
                highlightbackground=GUI.configs['border_bg'],
                highlightcolor=GUI.configs['border_bg']
            )
            self.minilog.pack(side=BOTTOM, fill=X)
            GUI.load_image(
                path=pjoin('minilog', 'bg.png'),
                key='minilog',
                w=1116,
                h=32+2,
            )
            self.minilog.create_image(
                (0, 0),
                image=GUI.cache['minilog'],
                anchor=NW
            )
            self.minilog.bind('<Button-1>', on_clickminilog)

        def create_text():
            self.minitext = self.minilog.create_text(
                (12, 6),
                text='',
                font=self.mainfont,
                justify=CENTER,
                anchor=NW,
                fill=GUI.configs['minilog_text_fg']
            )

        def update_mini_log():
            if len(LOG.logs) > 0:
                self.minilog.itemconfig(self.minitext, text=LOG.logs[-1])
            self.minilog.after(100, update_mini_log)

        create_bar()
        create_text()
        update_mini_log()

    def update_tab(self):
        if self.editwindow:
            self.editwindow.destroy()
            self.editwindow = None
        if self.createwindow:
            self.createwindow.destroy()
            self.createwindow = None

        self.modpage.pack_forget()
        self.logpage.pack_forget()
        self.settingpage.pack_forget()
        self.minilog.pack_forget()
        if self.tab == 0:
            self.minilog.pack(side=BOTTOM, fill=X)
            self.modpage.pack(fill=BOTH)
            self.topbar.itemconfig(self.runbutton, state=NORMAL)
            self.topbar.itemconfig(self.allbutton, state=NORMAL)
            self.topbar.itemconfig(self.nonbutton, state=NORMAL)
            self.topbar.itemconfig(self.sortpbutton, state=NORMAL)
            self.topbar.itemconfig(self.sortnbutton, state=NORMAL)
            self.topbar.itemconfig(
                self.tabbutton, image=GUI.cache['log'])
        elif self.tab == 1:
            self.logpage.pack(fill=BOTH)
            self.topbar.itemconfig(self.runbutton, state=HIDDEN)
            self.topbar.itemconfig(self.allbutton, state=HIDDEN)
            self.topbar.itemconfig(self.nonbutton, state=HIDDEN)
            self.topbar.itemconfig(self.sortpbutton, state=HIDDEN)
            self.topbar.itemconfig(self.sortnbutton, state=HIDDEN)
            self.topbar.itemconfig(
                self.tabbutton, image=GUI.cache['setting'])
        else:
            self.minilog.pack(side=BOTTOM, fill=X)
            self.settingpage.pack(fill=BOTH)
            self.topbar.itemconfig(self.runbutton, state=HIDDEN)
            self.topbar.itemconfig(self.allbutton, state=HIDDEN)
            self.topbar.itemconfig(self.nonbutton, state=HIDDEN)
            self.topbar.itemconfig(self.sortpbutton, state=HIDDEN)
            self.topbar.itemconfig(self.sortnbutton, state=HIDDEN)
            self.topbar.itemconfig(
                self.tabbutton, image=GUI.cache['home'])

    def set_appwindow(self):
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, -20)
        style = style & ~0x00000080
        style = style | 0x00040000
        windll.user32.SetWindowLongW(hwnd, -20, style)
        self.root.wm_withdraw()
        self.root.after(10, self.root.wm_deiconify)

    def create_scrollbar_style(self):
        style = Style()
        style.element_create(
            "My.Vertical.TScrollbar.trough", "from", "clam")
        style.element_create(
            "My.Vertical.TScrollbar.thumb", "from", "clam")
        style.element_create(
            "My.Vertical.TScrollbar.grip", "from", "clam")

        style.layout("My.Vertical.TScrollbar",
                     [('My.Vertical.TScrollbar.trough',
                       {'children': [('My.Vertical.TScrollbar.thumb',
                                      {'unit': '1',
                                          'children':
                                          [('My.Vertical.TScrollbar.grip',
                                           {'sticky': ''})],
                                          'sticky': 'nswe'})
                                     ],
                           'sticky': 'ns'})])

        style.configure("My.Vertical.TScrollbar", gripcount=0, background=GUI.configs['scrollbar_fg'],
                        troughcolor=GUI.configs['scrollbar_bg'], borderwidth=1, bordercolor=GUI.configs['border_bg'],
                        lightcolor=GUI.configs['scrollbar_fg'], darkcolor=GUI.configs['scrollbar_fg'],
                        arrowsize=32)

    def __init__(self):
        try:
            t = Prun('tasklist', creationflags=CREATE_NO_WINDOW,
                     capture_output=True, check=True).stdout.decode()
            if t.count('cslmao.exe') > 2:
                sexit()
        except:
            pass
        self.tab = 0
        if 'game' not in SYSTEM.settings or SYSTEM.settings['game'] == '':
            self.tab = 2
            LOG.write('No Game folder selected')
        self.create_root()
        self.mainfont = Font(family='Courier New', size=12)
        self.editwindow = None
        self.createwindow = None
        self.create_scrollbar_style()
        self.create_top_bar()
        self.create_log_page()
        self.create_mod_page()
        self.create_setting_page()
        self.create_mini_log()
        self.update_tab()
        self.root.after(10, self.set_appwindow)
        self.root.mainloop()


def main():
    SYSTEM.ensure_folder()
    SYSTEM.load_settings()
    SYSTEM.load_profile()
    GUI.load_configs()
    GUI()


main()
sexit()
