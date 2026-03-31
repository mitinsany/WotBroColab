# -*- coding: utf-8 -*-

import os
import json
import time
import glob
import socket
import hashlib
import threading
import atexit
import random

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
    PLAYER_LOGIN: u'РІС…РѕРґ РІ РёРіСЂСѓ',
    PLAYER_LOGOUT: u'РІС‹С…РѕРґ РёР· РёРіСЂС‹',
    BATTLE_START: u'РЅР°С‡Р°Р»Рѕ Р±РѕСЏ',
    BATTLE_END: u'Р·Р°РІРµСЂС€РµРЅРёРµ Р±РѕСЏ',
}

BOT_TOKEN = ''
CHAT_ID = ''
TIMEOUT_SECONDS = 3.0
QUEUE_SIZE = 128

_EVENT_QUEUE = None
_WORKER = None
_POLL_WORKER = None
_STOP_EVENT = threading.Event()
_LOG_FILE = None
_COMPUTER_NAME = 'UNKNOWN-PC'
_UPDATE_INFO = None
_UPDATE_NOTICE_SHOWN = False
_PLAYER_LOGGED_IN = False
_UPDATE_NOTICE_RETRY_SCHEDULED = False
_LAST_EVENT_AT = {}
_LAST_UPDATE_ID = None
_IN_BATTLE = False
_LAST_KNOWN_PLAYER = 'unknown_player'
_CURRENT_ACCOUNT_NAME = None


def _log(msg):
    try:
        print '[WotBroColab] %s' % msg
    except Exception:
        pass
    try:
        if _LOG_FILE:
            f = open(_LOG_FILE, 'a')
            try:
                f.write('%s [WotBroColab] %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), msg))
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
    raw = ''
    try:
        raw = socket.gethostname() or ''
    except Exception:
        raw = ''
    if not raw:
        raw = (os.environ.get('COMPUTERNAME') or '').strip()
    if not raw:
        raw = 'UNKNOWN-PC'
    try:
        data = raw
        try:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
        except Exception:
            pass
        digest = hashlib.sha256(data).hexdigest()[:2]
        if digest:
            return digest
    except Exception:
        pass
    return '000000'


def _safe_player_name(value):
    try:
        if value is None:
            return None
        if not isinstance(value, basestring):
            value = str(value)
        value = value.strip()
        if not value:
            return None
        low = value.lower()
        if low in ('none', 'unknown', 'unknown_player', 'mod_init'):
            return None
        return value
    except Exception:
        return None


def _player_name_from_obj(obj):
    if obj is None:
        return None
    for attr in ('name', 'playerName', '_PlayerAvatar__name', '_name', 'userName'):
        try:
            val = getattr(obj, attr, None)
            val = _safe_player_name(val)
            if val:
                return val
        except Exception:
            pass
    return None


def _current_player_name():
    try:
        import BigWorld
        player = BigWorld.player()
        name = _player_name_from_obj(player)
        if name:
            return name
    except Exception:
        pass
    return None


def _remember_player_name(name):
    global _LAST_KNOWN_PLAYER
    safe = _safe_player_name(name)
    if safe:
        _LAST_KNOWN_PLAYER = safe
    return _LAST_KNOWN_PLAYER


def _resolve_player_name(context_obj=None, args=None):
    name = _player_name_from_obj(context_obj)
    if name:
        return name

    if args:
        for item in args:
            name = _player_name_from_obj(item)
            if name:
                return name

    name = _current_player_name()
    if name:
        return _remember_player_name(name)
    return _LAST_KNOWN_PLAYER or 'unknown_player'


def _format_event_time(ts):
    try:
        return time.strftime('%d.%m.%y %H:%M:%S', time.localtime(float(ts)))
    except Exception:
        return time.strftime('%d.%m.%y %H:%M:%S', time.localtime())


def _escape_markdown_v2(text):
    try:
        if text is None:
            return u''
        if not isinstance(text, unicode):
            text = unicode(str(text), 'utf-8', 'ignore')
        for ch in u'\\_[]()~`>#+-=|{}.!*':
            text = text.replace(ch, u'\\' + ch)
        return text
    except Exception:
        try:
            return unicode(text)
        except Exception:
            return u''


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
        text = u'[WotBroColab] Р”РѕСЃС‚СѓРїРЅР° РЅРѕРІР°СЏ РІРµСЂСЃРёСЏ РјРѕРґР°: %s -> %s. РћР±РЅРѕРІРёС‚Рµ РјРѕРґ РєРѕРјР°РЅРґРѕР№ git pull.' % (
        _UPDATE_INFO.get('local'),
        _UPDATE_INFO.get('remote'),
    )
    if _push_system_message(text):
        _UPDATE_NOTICE_SHOWN = True
        _log('In-game update notice shown')
    else:
        _schedule_update_notice_retry()


def _on_player_login(player_name=None):
    _reconcile_account_state(_current_player_name())


def _on_player_logout(player_name=None, immediate=False):
    global _PLAYER_LOGGED_IN, _CURRENT_ACCOUNT_NAME
    if not _PLAYER_LOGGED_IN:
        return
    player_name = _safe_player_name(player_name) or _CURRENT_ACCOUNT_NAME or _LAST_KNOWN_PLAYER
    _PLAYER_LOGGED_IN = False
    _CURRENT_ACCOUNT_NAME = None
    if immediate:
        _send_event_immediate(PLAYER_LOGOUT, player_name=player_name)
    else:
        _queue_event(PLAYER_LOGOUT, player_name=player_name)


def _reconcile_account_state(observed_name=None):
    global _CURRENT_ACCOUNT_NAME, _PLAYER_LOGGED_IN
    name = _safe_player_name(observed_name) or _current_player_name() or None
    if name:
        _remember_player_name(name)
    current = _CURRENT_ACCOUNT_NAME

    if current is None and name:
        _CURRENT_ACCOUNT_NAME = name
        _PLAYER_LOGGED_IN = True
        _queue_event(PLAYER_LOGIN, player_name=name)
        _try_show_update_notice()
        return

    if current and name and current != name:
        _send_event_immediate(PLAYER_LOGOUT, player_name=current)
        _CURRENT_ACCOUNT_NAME = name
        _PLAYER_LOGGED_IN = True
        _queue_event(PLAYER_LOGIN, player_name=name)
        _try_show_update_notice()
        return

    if current and name and current == name:
        _PLAYER_LOGGED_IN = True
        return

    if current and not name:
        _PLAYER_LOGGED_IN = True


def _format_message(event_type, payload):
    player = payload.get('player') or 'unknown_player'
    player_md = _escape_markdown_v2(player)
    ts_text = _format_event_time(payload.get('timestamp'))
    prefix = u'\\[%s\\]\\[%s\\]\\[%s\\]' % (
        _escape_markdown_v2(_COMPUTER_NAME),
        _escape_markdown_v2(ts_text),
        player_md
    )
    if event_type == PLAYER_LOGIN:
        msg = u'%s Вошел в игру' % prefix
    elif event_type == PLAYER_LOGOUT:
        msg = u'%s Вышел из игры' % prefix
    elif event_type == BATTLE_START:
        msg = u'%s Зашел в бой' % prefix
    elif event_type == BATTLE_END:
        msg = u'%s Вышел из боя' % prefix
    else:
        label = EVENT_LABELS.get(event_type, event_type)
        msg = u'%s Событие: %s' % (prefix, _escape_markdown_v2(label))
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


def _prefix_now(player_name=None):
    player = _safe_player_name(player_name) or _current_player_name() or 'unknown_player'
    return u'\\[%s\\]\\[%s\\]\\[%s\\]' % (
        _escape_markdown_v2(_COMPUTER_NAME),
        _escape_markdown_v2(_format_event_time(time.time())),
        _escape_markdown_v2(player)
    )


def _send_to_telegram(text):
    url = 'https://api.telegram.org/bot%s/sendMessage' % BOT_TOKEN
    payload = urllib.urlencode({
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'MarkdownV2',
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


def _telegram_api_call(method, params=None):
    if urllib is None or urllib2 is None:
        raise RuntimeError('urllib unavailable')
    if not BOT_TOKEN:
        raise RuntimeError('empty bot token')
    url = 'https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, method)
    payload = urllib.urlencode(params or {})
    req = urllib2.Request(url, payload)
    resp = urllib2.urlopen(req, timeout=TIMEOUT_SECONDS)
    body = resp.read()
    try:
        data = json.loads(body)
    except Exception:
        raise RuntimeError('invalid telegram json')
    if not isinstance(data, dict) or not data.get('ok'):
        raise RuntimeError(str(data.get('description') if isinstance(data, dict) else 'telegram error'))
    return data.get('result')


def _ensure_bot_commands():
    commands = json.dumps([{'command': 'ping', 'description': 'Проверка статуса мода в игре'}], ensure_ascii=False)
    try:
        _telegram_api_call('setMyCommands', {'commands': commands})
        _log('Bot menu command /ping registered')
    except Exception as e:
        _log('setMyCommands failed: %s' % e)


def _sync_updates_offset():
    global _LAST_UPDATE_ID
    try:
        result = _telegram_api_call('getUpdates', {'limit': '1'})
        if isinstance(result, list) and len(result) > 0:
            upd = result[-1]
            upd_id = upd.get('update_id')
            if upd_id is not None:
                _LAST_UPDATE_ID = int(upd_id) + 1
                _log('Update offset initialized: %s' % _LAST_UPDATE_ID)
    except Exception as e:
        _log('Initial getUpdates failed: %s' % e)


def _status_text():
    in_battle = False
    try:
        import BigWorld
        player = BigWorld.player()
        if player is not None:
            arena = getattr(player, 'arena', None)
            if arena is not None:
                in_battle = True
    except Exception:
        in_battle = False
    if in_battle:
        return u'В бою'
    if _PLAYER_LOGGED_IN:
        return u'в игре'
    return u'вне игры'


def _handle_ping_command():
    try:
        username = _current_player_name() or _CURRENT_ACCOUNT_NAME or _LAST_KNOWN_PLAYER or 'unknown_player'
        _remember_player_name(username)
        msg = u'%s %s' % (_prefix_now(username), _escape_markdown_v2(_status_text()))
        _send_to_telegram(msg)
        _log('Ping response sent')
    except Exception as e:
        _log('Ping response failed: %s' % e)


def _poll_commands_once():
    global _LAST_UPDATE_ID
    params = {'limit': '25'}
    if _LAST_UPDATE_ID is not None:
        params['offset'] = str(_LAST_UPDATE_ID)
    result = _telegram_api_call('getUpdates', params)
    if not isinstance(result, list):
        return
    for upd in result:
        upd_id = upd.get('update_id')
        if upd_id is not None:
            try:
                upd_id_int = int(upd_id)
                if _LAST_UPDATE_ID is None or upd_id_int >= _LAST_UPDATE_ID:
                    _LAST_UPDATE_ID = upd_id_int + 1
            except Exception:
                pass
        msg_obj = upd.get('message') or upd.get('edited_message') or {}
        text = (msg_obj.get('text') or '').strip()
        if not text:
            continue
        cmd = text.split(' ', 1)[0].strip().lower()
        if not (cmd == '/ping' or cmd.startswith('/ping@')):
            continue
        chat = msg_obj.get('chat') or {}
        chat_id = str(chat.get('id') or '').strip()
        if CHAT_ID and chat_id and chat_id != CHAT_ID:
            continue
        _handle_ping_command()


def _command_poll_loop():
    while not _STOP_EVENT.is_set():
        delay = random.uniform(5.0, 10.0)
        if _STOP_EVENT.wait(delay):
            break
        try:
            _reconcile_account_state(_current_player_name())
            _poll_commands_once()
        except Exception as e:
            _log('Command poll failed: %s' % e)


def _send_event_immediate(event_type, player_name=None, meta=None):
    if not _enabled():
        return
    player = _safe_player_name(player_name) or _current_player_name() or _LAST_KNOWN_PLAYER or 'unknown_player'
    _remember_player_name(player)
    now = time.time()
    if event_type in (PLAYER_LOGIN, PLAYER_LOGOUT):
        key = '%s|%s' % (event_type, player)
        last_ts = _LAST_EVENT_AT.get(key)
        if last_ts is not None and (now - last_ts) < 8.0:
            _log('Duplicate immediate event skipped: %s player=%s' % (event_type, player))
            return
        _LAST_EVENT_AT[key] = now
    payload = {
        'type': event_type,
        'timestamp': now,
        'player': player,
        'meta': meta or {},
    }
    try:
        text = _format_message(event_type, payload)
        _send_to_telegram(text)
        _log('Sent immediately: %s' % event_type)
    except Exception as e:
        _log('Immediate send failed (%s): %s' % (event_type, e))


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
    global _EVENT_QUEUE, _WORKER, _POLL_WORKER
    if _EVENT_QUEUE is None:
        _EVENT_QUEUE = queue_mod.Queue(QUEUE_SIZE)
    if _WORKER is not None and _WORKER.is_alive():
        pass
    else:
        _STOP_EVENT.clear()
        _WORKER = threading.Thread(target=_worker_loop)
        _WORKER.setDaemon(True)
        _WORKER.start()

    if _POLL_WORKER is not None and _POLL_WORKER.is_alive():
        return
    _STOP_EVENT.clear()
    _POLL_WORKER = threading.Thread(target=_command_poll_loop)
    _POLL_WORKER.setDaemon(True)
    _POLL_WORKER.start()


def _queue_event(event_type, player_name=None, meta=None):
    if not _enabled():
        return
    player = _safe_player_name(player_name) or _current_player_name() or _LAST_KNOWN_PLAYER or 'unknown_player'
    _remember_player_name(player)
    now = time.time()
    if event_type in (PLAYER_LOGIN, PLAYER_LOGOUT):
        key = '%s|%s' % (event_type, player)
        last_ts = _LAST_EVENT_AT.get(key)
        if last_ts is not None and (now - last_ts) < 8.0:
            _log('Duplicate event skipped: %s player=%s' % (event_type, player))
            return
        _LAST_EVENT_AT[key] = now

    payload = {
        'type': event_type,
        'timestamp': now,
        'player': player,
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
            if _wrap_method(
                account_cls,
                'onBecomePlayer',
                lambda self, args, kwargs, result: _reconcile_account_state(_current_player_name())
            ):
                installed += 1
            if _wrap_method(
                account_cls,
                '_doCmdLogin',
                lambda self, args, kwargs, result: _reconcile_account_state(_current_player_name())
            ):
                installed += 1
            if _wrap_method(
                account_cls,
                'onBecomeNonPlayer',
                lambda self, args, kwargs, result: _reconcile_account_state(None)
            ):
                installed += 1
    except Exception as e:
        _log('Account hooks not installed: %s' % e)

    try:
        import Avatar
        avatar_cls = getattr(Avatar, 'PlayerAvatar', None)
        if avatar_cls is not None:
            if _wrap_method(
                avatar_cls,
                '_PlayerAvatar__startGUI',
                lambda self, args, kwargs, result: _on_battle_start(
                    player_name=_resolve_player_name(self, args)
                )
            ):
                installed += 1
            if _wrap_method(
                avatar_cls,
                '_PlayerAvatar__destroyGUI',
                lambda self, args, kwargs, result: _on_battle_end(
                    player_name=_resolve_player_name(self, args)
                )
            ):
                installed += 1
    except Exception as e:
        _log('Avatar hooks not installed: %s' % e)

    _log('Hooks installed: %s' % installed)


def _on_battle_start(player_name=None):
    global _IN_BATTLE
    _IN_BATTLE = True
    _reconcile_account_state(_current_player_name())
    _queue_event(BATTLE_START, player_name=player_name)


def _on_battle_end(player_name=None):
    global _IN_BATTLE
    _IN_BATTLE = False
    _reconcile_account_state(_current_player_name())
    _queue_event(BATTLE_END, player_name=player_name)


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
        _ensure_bot_commands()
        _sync_updates_offset()
        _start_worker()
        try:
            atexit.register(
                lambda: _on_player_logout(
                    player_name=_current_player_name() or _CURRENT_ACCOUNT_NAME or _LAST_KNOWN_PLAYER,
                    immediate=True
                ) if _PLAYER_LOGGED_IN else None
            )
        except Exception as e:
            _log('atexit register failed: %s' % e)
    _install_hooks()
    _log('Mod initialized')


init()
