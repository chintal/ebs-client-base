#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2021 Chintalagiri Shashank
#
# This file is part of EBS Client Base.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import importlib

from tendril.utils.versions import get_namespace_package_names
from tendril.asynchronous.utils.engines import AsyncEngineBase

from ebs.client.detect.manager import DetectionManager


class DeviceManager(AsyncEngineBase):
    def __init__(self, prefix, *args, **kwargs):
        super(DeviceManager, self).__init__(*args, **kwargs)
        self._prefix = prefix
        self._supported_devices = {}
        self._connected_devices = {}
        self._autoconnect = True
        self._load_devices()
        self._detection_manager = DetectionManager('ebs.client.detect', prefix, self)

    def _start(self):
        self.log.info("Starting Device Manager")
        self._detection_manager.start()
        self._detection_manager.install_handler("connect:*", self._handle_device_connect)

    def _stop(self):
        self.log.info("Stopping Device Manager")

    def _handle_device_connect(self, name, parameters):
        if name not in self._supported_devices.keys():
            raise ValueError("Device with name '{}' is not recognized".format(name))
        if parameters['heuristic'].domain == 'serial':
            _device_key = parameters['port']
            _device_class = self._supported_devices[name]
            _device_params = {
                'parent': self,
                'port': parameters['port'],
            }
            self._connected_devices[_device_key] = _device_class(**_device_params)
            if self._autoconnect:
                self._connected_devices[_device_key].connect()

    def _handle_device_disconnect(self):
        pass

    def _load_devices(self):
        self.log.info("Installing device modules from {0}".format(self._prefix))
        modules = list(get_namespace_package_names(self._prefix))
        for m_name in modules:
            if m_name in [
                __name__,
                'ebs.client.devices.base',
                'ebs.client.devices.manager',
                'ebs.client.devices.serial'
            ]:
                continue
            m = importlib.import_module(m_name)
            m.install_devices(self)
        self.log.info("Done installing device modules from {0}".format(self._prefix))

    def install_device(self, name, device):
        self.log.info("Installing device '{0}' using '{1}'".format(name, device))
        self._supported_devices[name] = device

    def __getattr__(self, item):
        if item == '__path__':
            return None
        if item == '__len__':
            return len(self._supported_devices.keys())
        if item == '__all__':
            return list(self._supported_devices.keys()) + \
                   ['', 'install_device']
        return self._supported_devices[item]
