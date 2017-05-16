galicaster-plugin-unplugged
===========================

Send email when someone plugs/unplugs a USB device from a device running
Galicaster_. Reminder emails can be sent at regular intervals if the device is
not plugged back in.

This can also be used to switch Pulseaudio_ inputs when a device is plugged in
or unplugged. This can be useful when using USB microphones, making sure that
even if the microphone is not plugged in when Galicaster starts, or is
unplugged in the middle of a recording, things will start working again as soon
as the microphone is plugged back in. You can also use it to switch to a backup
microphone when the USB one is unplugged.

Installation
------------

Install using ``sudo pip2 install .`` in this directory. The plugin depends on
the pulsectl_ python module, and it should be installed automatically by pip
as needed.

You can also install manually by copying ``galicaster_plugin_unplugged/`` into
the Galicaster plugins directory, renaming it as ``unplugged/`` and then
installing the dependency with ``sudo pip2 install pulsectl``.

However you install the plugin, also required is the GObject introspection data
for ``libgudev``. On Ubuntu 16.04 this can be installed with ``sudo apt-get
install gir1.2-gudev-1.0``.


Configuration
-------------

Enable the plugin with the following in your Galicaster ``conf.ini`` file:

::

    [plugins]
    unplugged = True

    [unplugged]
    mailfrom = galicaster@example.com
    mailto = itsupport@example.com,avsupport@example.com
    resend_every = 120
    smtpserver = smtp.example.com
    devices = {"USB Microphone": {"vendor_id": "17a0", "device_id": "0101", "switch_on_connect": "alsa_input.usb-Samson_Technologies_Samson_UB1-00.analog-stereo", "switch_on_disconnect": "alsa_input.pci-0000_01_00.0.analog-stereo"}, "Flashing light": {"vendor_id": "20a0", "device_id": "41e5"}}

Here are all the options:

+--------------+---------+------------------------------------------------------------------+-----------------+
| Setting      | Type    | Description                                                      | Default         |
+==============+=========+==================================================================+=================+
| mailfrom     | string  | Address to send email from                                       | *required*      |
+--------------+---------+------------------------------------------------------------------+-----------------+
| mailto       | string  | Address(es) to send email to (comma separated list for multiple) | *required*      |
+--------------+---------+------------------------------------------------------------------+-----------------+
| smtpserver   | string  | SMTP server to use to send email                                 | *required*      |
+--------------+---------+------------------------------------------------------------------+-----------------+
| resend_every | integer | Check for unplugged devices and resend email every X minutes     | 60 (1 hour)     |
+--------------+---------+------------------------------------------------------------------+-----------------+
| devices      | json    | Details of devices to watch                                      | {} (do nothing) |
|              |         |                                                                  |                 |
|              |         | ::                                                               |                 |
|              |         |                                                                  |                 |
|              |         |   {                                                              |                 |
|              |         |     "Display Name": {                                            |                 |
|              |         |       "vendor_id": "1234",                                       |                 |
|              |         |       "device_id": "abcd",                                       |                 |
|              |         |       "switch_on_connect": "pulse.source",                       |                 |
|              |         |       "switch_on_disconnect": "pulse.source",                    |                 |
|              |         |     }, ...                                                       |                 |
|              |         |   }                                                              |                 |
|              |         |                                                                  |                 |
|              |         | ``Display Name`` will appear in emails about this device         |                 |
|              |         |                                                                  |                 |
|              |         | ``vendor_id`` is the vendor hex code of the device to be watched |                 |
|              |         | (see ``lsusb``)                                                  |                 |
|              |         |                                                                  |                 |
|              |         | ``device_id`` is the device hex code of the device to be watched |                 |
|              |         | (see ``lsusb``)                                                  |                 |
|              |         |                                                                  |                 |
|              |         | ``switch_on_connect`` [optional] is a Pulseaudio source name to  |                 |
|              |         | switch the recording input to when this device connects (see     |                 |
|              |         | ``pactl list sources``)                                          |                 |
|              |         |                                                                  |                 |
|              |         | ``switch_on_disconnect`` [optional] is a Pulseaudio source name  |                 |
|              |         | to switch the recording input to when this device connects (see  |                 |
|              |         | ``pactl list sources``)                                          |                 |
|              |         |                                                                  |                 |
|              |         | Multiple devices may be specified. Audio input switching is      |                 |
|              |         | optional. I am leaving the default input in the Galicaster       |                 |
|              |         | recording profile and switching to the correct input when the    |                 |
|              |         | USB microphone is plugged in so that the profile never fails if  |                 |
|              |         | the microphone is unplugged at any point.                        |                 |
+--------------+---------+------------------------------------------------------------------+-----------------+

Source
------

Source code is available at https://github.com/ppettit/galicaster-plugin-unplugged

.. _Galicaster: https://github.com/teltek/Galicaster
.. _Pulseaudio: https://www.freedesktop.org/wiki/Software/PulseAudio/
.. _pulsectl:   https://pypi.python.org/pypi/pulsectl
