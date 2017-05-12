import gi
import smtplib
import threading
import time

from datetime import datetime
from email.mime.text import MIMEText
from pulsectl import Pulse

from galicaster.core import context

gi.require_version('GUdev', '1.0')
from gi.repository import GLib, GUdev # noqa


conf = context.get_conf()
dispatcher = context.get_dispatcher()
logger = context.get_logger()
recorder = context.get_recorder()

pulse = Pulse('galicaster-plugin-unplugged')
udev = GUdev.Client(subsystems=['usb'])


def init():
    Unplugged()


class WatchedDevice(object):
    def __init__(self, device_name, device_info):
        self.name = device_name
        self.vendor_id = device_info.get('vendor_id')
        self.device_id = device_info.get('device_id')
        self.switch_on_connect = device_info.get('switch_on_connect')
        self.switch_on_disconnect = device_info.get('switch_on_disconnect')
        self._unplugged_since = False
        self.plugged_in

    @property
    def plugged_in(self):
        enum = GUdev.Enumerator.new(udev)
        enum.add_match_property('ID_VENDOR_ID', self.vendor_id)
        enum.add_match_property('ID_MODEL_ID', self.device_id)
        plugged_in = bool(enum.execute())
        if plugged_in:
            self._unplugged_since = False
        elif not self._unplugged_since:
            self._unplugged_since = datetime.now()
        return plugged_in

    @property
    def status(self):
        return {True: 'plugged in', False: 'unplugged'}.get(self.plugged_in)

    @property
    def unplugged_since(self):
        return self._unplugged_since

    @property
    def unplugged_for(self):
        return datetime.now() - self._unplugged_since

    def __repr__(self):
        return ('<WatchedDevice: name="{0.name}", vendor_id="{0.vendor_id}", '
                'device_id="{0.device_id}", plugged_in={0.plugged_in}, '
                'switch_on_connect="{0.switch_on_connect}", '
                'switch_on_disconnect="{0.switch_on_disconnect}", '
                'unplugged_since="{0.unplugged_since}">'.format(self))


class Unplugged(object):

    def __init__(self):
        # resend_every = how many minutes to resend email if still unplugged
        self.resend_every = conf.get_int('unplugged', 'resend_every', 60) * 60
        self.resend_every -= 3  # just to make sure ;)

        self.switch = {}

        self.last_check = time.time()

        # devices to watch, can be multiple, inthe form:
        # {'display name': {'vendor_id': '0a1b', device_id: '3c4d'}}
        devices_conf = conf.get_json('unplugged', 'devices')
        self.devices = []
        for d in devices_conf:
            dev = WatchedDevice(d, devices_conf[d])
            # senf email immediately if unplugged on startup
            if not dev.plugged_in:
                self.send_email(dev)
            self.devices.append(dev)
            logger.debug("watching: {}".format(dev))

        udev.connect('uevent', self._handle_event)
        dispatcher.connect('timer-long', self._handle_timer)

    def send_email(self, device):
        host = conf.get_hostname()
        threading.Thread(target=self._send_email,
                         args=(host, device,)).start()

    def _send_email(self, host, device):
        logger.info('sending "{0.status}" email for "{0.name}"'.format(device))

        to = conf.get('unplugged', 'mailto')
        fr = conf.get('unplugged', 'mailfrom')
        smtpserver = conf.get('unplugged', 'smtpserver')

        txt = '{0.name} is {0.status}!\n\n'.format(device)
        if not device.plugged_in:
            # TODO: will still say "just" if starting up...
            if device.unplugged_for.total_seconds() < 10:
                txt += 'It has just been unplugged.'
            else:
                txt += ('It has been unplugged for {0.unplugged_for} '
                        '(since {0.unplugged_since})'.format(device))
        msg = MIMEText(txt)
        msg['To'] = to
        msg['From'] = fr
        msg['Subject'] = '[{0}] {1.name} {1.status}'.format(host, device)

        s = None
        try:
            s = smtplib.SMTP(smtpserver)
            s.sendmail(fr, to.split(','), msg.as_string())
        except Exception:
            logger.error('problem sending email', exc_info=True)
        finally:
            if s:
                s.quit()

        logger.debug('sent "{0.status}" email for "{0.name}"'.format(device))

    def switch_input(self, switch_to, device=None):
        logger.info('switching pulse input to {}'.format(switch_to))
        for source in pulse.source_list():
            if source.name == switch_to:
                for recording in pulse.source_output_list():
                    if (pulse.client_info(recording.client).name
                            == 'run_galicaster.py'):
                        pulse.source_output_move(recording.index, source.index)
                        if device:
                            self.switch[device.name] = None
                        return False
        logger.warning('could not switch to {}'.format(switch_to))
        return True

    def translate_action(self, action):
        return {'add': 'plugged in', 'remove': 'unplugged'}.get(action)

    def _handle_timer(self, sender):
        # resend notification emails if still unplugged
        now = time.time()
        if self.last_check < now - self.resend_every:
            self.last_check = now
            for d in self.devices:
                if not d.plugged_in:
                    self.send_email(d)

    def _handle_event(self, client, action, device):
        for d in self.devices:
            if (device.get_property('ID_VENDOR_ID') == d.vendor_id and
                    device.get_property('ID_MODEL_ID') == d.device_id):
                logger.info("%s was %s", d.name, self.translate_action(action))
                self.send_email(d)
                switch_to = {'add': d.switch_on_connect,
                             'remove': d.switch_on_disconnect}.get(action)

                if ((action == 'add' and d.switch_on_connect) or
                        (action == 'remove' and d.switch_on_disconnect)):
                    if self.switch.get(d.name):
                        GLib.source_remove(self.switch.get(d.name))
                        self.switch[d.name] = None
                    self.switch[d.name] = GLib.timeout_add_seconds(
                                    1, self.switch_input, switch_to, d)
