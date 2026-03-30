# -*- coding: utf-8 -*-

import os
import json
import time
import glob
import socket
import threading

try:
    _marker_path = os.path.join(os.getcwd(), 'logs', 'wot_tg_import_marker.log')
    _marker_dir = os.path.dirname(_marker_path)
    if not os.path.isdir(_marker_dir):
        os.makedirs(_marker_dir)
    _mf = open(_marker_path, 'a')
    try:
        _mf.write('%s import reached\n' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    finally:
        _mf.close()
except Exception:
    pass

try:
    import Queue as queue_mod
except Exception:
    import queue as queue_mod

try:
    import urllib
    import urllib2
except Exception:
    urllib = None
    urllib2 = None

MOD_ID = 'wot.telegram.notifier'
MOD_VERSION = '__MOD_VERSION__'
VERSION_CHECK_URL = 'https://mitinsany.github.io/WotBroColab/version.json'

PLAYER_LOGIN = 'PLAYER_LOGIN'
PLAYER_LOGOUT = 'PLAYER_LOGOUT'
BATTLE_START = 'BATTLE_START'
BATTLE_END = 'BATTLE_END'

EVENT_LABELS = {
    PLAYER_LOGIN: u'вход в игру',
    PLAYER_LOGOUT: u'выход из игры',
    BATTLE_START: u'начало боя',
    BATTLE_END: u'завершение боя',
}

BOT_TOKEN = ''
CHAT_ID = ''
TIMEOUT_SECONDS = 3.0
QUEUE_SIZE = 128

_EVENT_QUEUE = None
_WORKER = None
_STOP_EVENT = threading.Event()
_LOG_FILE = None
_COMPUTER_NAME = 'UNKNOWN-PC'
_UPDATE_INFO = None
_UPDATE_NOTICE_SHOWN = False
_PLAYER_LOGGED_IN = False
_UPDATE_NOTICE_RETRY_SCHEDULED = False


def _log(msg):
    try:
        print '[WoT TG] %s' % msg
    except Exception:
        pass
    try:
        if _LOG_FILE:
            f = open(_LOG_FILE, 'a')
            try:
                f.write('%s [WoT TG] %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), msg))
            finally:
                f.close()
    except Exception:
        pass


def _init_file_log():
    global _LOG_FILE
    try:
        root = os.getcwd()
        logs_dir = os.path.join(root, 'logs')
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
        _LOG_FILE = os.path.join(logs_dir, 'wot_tg_mod.log')
        _log('File log initialized: %s' % _LOG_FILE)
    except Exception:
        _LOG_FILE = None


def _read_env_file_candidates():
    result = []
    seen = set()

    def _add(path):
        if not path:
            return
        ap = os.path.abspath(path)
        if ap in seen:
            return
        seen.add(ap)
        result.append(ap)

    try:
        root = os.getcwd()
        _add(os.path.join(root, '.env'))
        _add(os.path.join(root, 'mods', '.env'))
        for path in glob.glob(os.path.join(root, 'mods', '*', '.env')):
            _add(path)
        for path in glob.glob(os.path.join(root, 'res_mods', '*', '.env')):
            _add(path)
        for path in glob.glob(os.path.join(root, 'res_mods', '*', 'mods', '.env')):
            _add(path)
    except Exception:
        pass

    try:
        base = os.path.dirname(os.path.abspath(__file__))
        for _ in range(7):
            _add(os.path.join(base, '.env'))
            _add(os.path.join(base, 'mods', '.env'))
            parent = os.path.dirname(base)
            if parent == base:
                break
            base = parent
    except Exception:
        pass

    return result


def _load_dotenv_if_present():
    for path in _read_env_file_candidates():
        if not os.path.isfile(path):
            continue
        try:
            f = open(path, 'r')
            try:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            finally:
                f.close()
            _log('Loaded .env from %s' % path)
            return
        except Exception as e:
            _log('Failed to read .env %s: %s' % (path, e))


def _safe_int(val, default):
    try:
        return int(val)
    except Exception:
        return default


def _safe_float(val, default):
    try:
        v = float(val)
        if v <= 0:
            return default
        return v
    except Exception:
        return default


def _load_config():
    global BOT_TOKEN, CHAT_ID, TIMEOUT_SECONDS, QUEUE_SIZE
    _load_dotenv_if_present()

    BOT_TOKEN = (os.getenv('WOT_TG_BOT_TOKEN') or '').strip()
    CHAT_ID = (os.getenv('WOT_TG_CHAT_ID') or '').strip()
    TIMEOUT_SECONDS = _safe_float((os.getenv('WOT_TG_TIMEOUT_SECONDS') or '3.0').strip(), 3.0)
    QUEUE_SIZE = _safe_int((os.getenv('WOT_TG_QUEUE_SIZE') or '128').strip(), 128)
    if QUEUE_SIZE < 1:
        QUEUE_SIZE = 1


def _enabled():
    return bool(BOT_TOKEN and CHAT_ID and urllib is not None and urllib2 is not None)


def _resolve_computer_name():
    try:
        name = socket.gethostname()
        if name:
            return name
    except Exception:
        pass
    return (os.environ.get('COMPUTERNAME') or 'UNKNOWN-PC').strip() or 'UNKNOWN-PC'


def _to_int_list(version_text):
    parts = []
    for chunk in str(version_text or '').split('.'):
        digits = ''.join([c for c in chunk if c.isdigit()])
        if not digits:
            parts.append(0)
        else:
            try:
                parts.append(int(digits))
            except Exception:
                parts.append(0)
    return parts


def _is_remote_newer(local_version, remote_version):
    left = _to_int_list(local_version)
    right = _to_int_list(remote_version)
    size = max(len(left), len(right))
    while len(left) < size:
        left.append(0)
    while len(right) < size:
        right.append(0)
    return right > left


def _fetch_remote_version():
    if urllib2 is None:
        return None
    req = urllib2.Request(VERSION_CHECK_URL)
    resp = urllib2.urlopen(req, timeout=TIMEOUT_SECONDS)
    body = resp.read()
    data = json.loads(body)
    if isinstance(data, dict):
        return str(data.get('version') or '').strip()
    return None


def _queue_update_check():
    global _UPDATE_INFO
    try:
        remote_version = _fetch_remote_version()
        if not remote_version:
            _log('Update check: remote version is empty')
            return
        if _is_remote_newer(MOD_VERSION, remote_version):
            _UPDATE_INFO = {
                'local': MOD_VERSION,
                'remote': remote_version,
            }
            _log('Update available: local=%s remote=%s' % (MOD_VERSION, remote_version))
        else:
            _log('Update check: up-to-date (local=%s remote=%s)' % (MOD_VERSION, remote_version))
    except Exception as e:
        _log('Update check failed: %s' % e)


def _push_system_message(text):
    try:
        import gui.SystemMessages as SystemMessages
        msg_type = getattr(SystemMessages.SM_TYPE, 'Information', None)
        if msg_type is None:
            msg_type = getattr(SystemMessages.SM_TYPE, 'Warning', None)
        if msg_type is None:
            SystemMessages.pushMessage(text)
        else:
            SystemMessages.pushMessage(text, msg_type)
        return True
    except Exception as e:
        _log('Unable to show in-game message: %s' % e)
        return False


def _schedule_update_notice_retry():
    global _UPDATE_NOTICE_RETRY_SCHEDULED
    if _UPDATE_NOTICE_RETRY_SCHEDULED:
        return
    try:
        import BigWorld
        _UPDATE_NOTICE_RETRY_SCHEDULED = True

        def _retry():
            global _UPDATE_NOTICE_RETRY_SCHEDULED
            _UPDATE_NOTICE_RETRY_SCHEDULED = False
            _try_show_update_notice()

        BigWorld.callback(5.0, _retry)
    except Exception as e:
        _log('Unable to schedule update notice retry: %s' % e)


def _try_show_update_notice():
    global _UPDATE_NOTICE_SHOWN
    if _UPDATE_NOTICE_SHOWN:
        return
    if not _PLAYER_LOGGED_IN:
        return
    if not _UPDATE_INFO:
        return
    text = u'[WoT TG] Доступна новая версия мода: %s -> %s. Обновите мод командой git pull.' % (
        _UPDATE_INFO.get('local'),
        _UPDATE_INFO.get('remote'),
    )
    if _push_system_message(text):
        _UPDATE_NOTICE_SHOWN = True
        _log('In-game update notice shown')
    else:
        _schedule_update_notice_retry()


def _on_player_login():
    global _PLAYER_LOGGED_IN
    _PLAYER_LOGGED_IN = True
    _queue_event(PLAYER_LOGIN)
    _try_show_update_notice()


def _format_message(event_type, payload):
    label = EVENT_LABELS.get(event_type, event_type)
    player = payload.get('player') or 'unknown_player'

    msg = u'[%s] Событие: %s, игрок: %s' % (_COMPUTER_NAME, label, player)
    if event_type == BATTLE_END:
        meta = payload.get('meta') or {}
        details = []
        result = meta.get('result') if isinstance(meta, dict) else None
        duration = meta.get('duration') if isinstance(meta, dict) else None
        if result:
            details.append(u'результат: %s' % result)
        if duration is not None:
            details.append(u'длительность: %sс' % duration)
        if details:
            msg = u'%s, %s' % (msg, u', '.join(details))
    return msg


def _send_to_telegram(text):
    url = 'https://api.telegram.org/bot%s/sendMessage' % BOT_TOKEN
    payload = urllib.urlencode({
        'chat_id': CHAT_ID,
        'text': text,
        'disable_web_page_preview': 'true',
    })
    req = urllib2.Request(url, payload)
    resp = urllib2.urlopen(req, timeout=TIMEOUT_SECONDS)
    body = resp.read()
    try:
        data = json.loads(body)
        if not data.get('ok'):
            raise RuntimeError(str(data.get('description') or 'telegram error'))
    except Exception:
        # If parse fails, do not crash the game.
        pass


def _worker_loop():
    while not _STOP_EVENT.is_set():
        try:
            item = _EVENT_QUEUE.get(True, 0.5)
        except Exception:
            continue

        if item is None:
            break

        event_type, payload = item
        try:
            text = _format_message(event_type, payload)
            _send_to_telegram(text)
            _log('Sent: %s' % event_type)
        except Exception as e:
            _log('Send failed (%s): %s' % (event_type, e))


def _start_worker():
    global _EVENT_QUEUE, _WORKER
    if _EVENT_QUEUE is None:
        _EVENT_QUEUE = queue_mod.Queue(QUEUE_SIZE)
    if _WORKER is not None and _WORKER.is_alive():
        return
    _STOP_EVENT.clear()
    _WORKER = threading.Thread(target=_worker_loop)
    _WORKER.setDaemon(True)
    _WORKER.start()


def _queue_event(event_type, player_name=None, meta=None):
    if not _enabled():
        return
    payload = {
        'type': event_type,
        'timestamp': time.time(),
        'player': player_name or 'unknown_player',
        'meta': meta or {},
    }
    try:
        _EVENT_QUEUE.put_nowait((event_type, payload))
    except Exception:
        _log('Queue full. Dropped event: %s' % event_type)


def _wrap_method(cls, method_name, after_callback):
    orig = getattr(cls, method_name, None)
    if orig is None:
        return False
    marker = '__wot_tg_wrapped__'
    if getattr(orig, marker, False):
        return True

    def wrapped(self, *args, **kwargs):
        result = orig(self, *args, **kwargs)
        try:
            after_callback(self, args, kwargs, result)
        except Exception as e:
            _log('Hook callback failed %s.%s: %s' % (cls.__name__, method_name, e))
        return result

    setattr(wrapped, marker, True)
    setattr(cls, method_name, wrapped)
    return True


def _install_hooks():
    installed = 0

    try:
        import Account
        account_cls = getattr(Account, 'Account', None)
        if account_cls is not None:
            if _wrap_method(account_cls, '_doCmdLogin', lambda *_: _on_player_login()):
                installed += 1
            if _wrap_method(account_cls, 'onBecomeNonPlayer', lambda *_: _queue_event(PLAYER_LOGOUT)):
                installed += 1
    except Exception as e:
        _log('Account hooks not installed: %s' % e)

    try:
        import Avatar
        avatar_cls = getattr(Avatar, 'PlayerAvatar', None)
        if avatar_cls is not None:
            if _wrap_method(avatar_cls, '_PlayerAvatar__startGUI', lambda *_: _queue_event(BATTLE_START)):
                installed += 1
            if _wrap_method(avatar_cls, '_PlayerAvatar__destroyGUI', lambda *_: _queue_event(BATTLE_END)):
                installed += 1
    except Exception as e:
        _log('Avatar hooks not installed: %s' % e)

    _log('Hooks installed: %s' % installed)


def init():
    global _COMPUTER_NAME
    _init_file_log()
    _COMPUTER_NAME = _resolve_computer_name()
    _load_config()
    _log('Init started')
    _queue_update_check()
    if not BOT_TOKEN or not CHAT_ID:
        _log('Config missing WOT_TG_BOT_TOKEN/WOT_TG_CHAT_ID; notifier disabled')
    elif urllib is None or urllib2 is None:
        _log('urllib/urllib2 not available; notifier disabled')
    else:
        _start_worker()
        _queue_event(PLAYER_LOGIN, player_name='mod_init', meta={'stage': 'startup'})
    _install_hooks()
    _log('Mod initialized')


init()
