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

from .base import DetectorBase


class DetectionManager(DetectorBase):
    def __init__(self, prefix, *args, **kwargs):
        super(DetectionManager, self).__init__(*args, **kwargs)
        self._prefix = prefix
        self._detectors = {}
        self._load_modules()
        self._load_devices()

    def _start(self):
        self.log.info("Starting Device Detectors")
        for name, detector in self._detectors.items():
            detector.start()

    def _stop(self):
        self.log.info("Stopping Device Detectors")
        for name, detector in self._detectors.items():
            detector.stop()

    def _load_modules(self):
        self.log.info("Installing detection modules from {0}".format(self._prefix))
        modules = list(get_namespace_package_names(self._prefix))
        for m_name in modules:
            if m_name == __name__:
                continue
            if m_name == 'ebs.client.detect.heuristics':
                continue
            if m_name == 'ebs.client.detect.devices':
                continue
            m = importlib.import_module(m_name)
            m.install(self)
        self.log.info("Done installing detection modules from {0}".format(self._prefix))

    def install_detector(self, name, detector: DetectorBase):
        self.log.info("Installing detection module '{0}' using '{1}'".format(name, detector.__class__))
        detector.install_handler(event='connect:*', handler=self.on_connect)
        detector.install_handler(event='disconnect:*', handler=self.on_disconnect)
        self._detectors[name] = detector

    def _load_devices(self):
        prefix = '.'.join([self._prefix, 'devices'])
        self.log.info("Installing device heuristics from {0}".format(prefix))
        modules = list(get_namespace_package_names(prefix))
        for m_name in modules:
            m = importlib.import_module(m_name)
            m.install(self)
        self.log.info("Done installing device heuristics from {0}".format(prefix))

    def install_device_heuristic(self, name, heuristic):
        super(DetectionManager, self).install_device_heuristic(name, heuristic)
        if heuristic.domain in self._detectors.keys():
            self._detectors[heuristic.domain].install_device_heuristic(name, heuristic)

    def __getattr__(self, item):
        if item == '__path__':
            return None
        if item == '__len__':
            return len(self._detectors.keys())
        if item == '__all__':
            return list(self._detectors.keys()) + \
                   ['', 'install_detector']
        print(dir(self))
        return self._detectors[item]

    def __repr__(self):
        return "<DetectionManager>"
