#!/usr/bin/env python
# coding: utf-8
from os.path import exists

import Security, CoreFoundation
from CoreWLAN import CWInterface
import argparse, configparser

import getpass

from pyfrc.mains.cli_deploy import PyFrcDeploy
from subprocess import Popen, PIPE
from ctypes import POINTER

kSecClass = Security.kSecClass.encode("utf-8")
kSecClassGenericPassword = Security.kSecClassGenericPassword.encode("utf-8")
kSecAttrAccount = Security.kSecAttrAccount.encode("utf-8")
kSecMatchLimit = Security.kSecMatchLimit.encode("utf-8")
kSecReturnAttributes = Security.kSecReturnAttributes.encode("utf-8")
kSecReturnData = Security.kSecReturnData.encode("utf-8")
kCFBooleanTrue = CoreFoundation.kCFBooleanTrue
kSecValueData = Security.kSecValueData


class FRCUtilDeploy:
    def __init__(self, parser):
        self.deploy = PyFrcDeploy(parser)
        parser.add_argument("-r", "--reconnect", action="store_true")
        parser.add_argument("-w", "--wifi", action="store_true")
        parser.add_argument("--ssid")
        self.parser = parser

    def getCurrentWifiNetwork(self):
        iface = CWInterface.interfaceNames()
        for iname in iface:
            ssid = CWInterface.interfaceWithName_(iname).ssid()
        return ssid

    def getWifiPassword(self, ssid):
        def CFDictionaryAddStringKeyValue(d, k, v):
            if type(v) is not bool:
                ck = CoreFoundation.CFStringCreateWithBytes(None, k, len(k), 0, 0)
                cv = CoreFoundation.CFStringCreateWithBytes(None, v, len(v), 0, 0)
                CoreFoundation.CFDictionaryAddValue(d, ck, cv)
                CoreFoundation.CFRelease(ck)
                CoreFoundation.CFRelease(cv)
            else:
                ck = CoreFoundation.CFStringCreateWithBytes(None, k, len(k), 0, 0)
                CoreFoundation.CFDictionaryAddValue(d, ck, v)
                CoreFoundation.CFRelease(ck)

        query = CoreFoundation.CFDictionaryCreateMutable(None, 0, None, None)
        CFDictionaryAddStringKeyValue(query, kSecClass, kSecClassGenericPassword)
        CFDictionaryAddStringKeyValue(query, kSecAttrAccount, ssid.encode("utf-8"))
        CFDictionaryAddStringKeyValue(query, kSecReturnData, kCFBooleanTrue)
        _, keychain_item = Security.SecItemCopyMatching(query, None)
        try:
            return keychain_item.bytes().tobytes().decode("utf-8")
        except AttributeError:
            print(
                "Could not find wifi password for ssid {}. Please enter it".format(ssid)
            )
            return getpass.getpass()

    def findNetwork(self, ssid=None):
        iface = CWInterface.interface()
        while True:
            networks, _ = iface.scanForNetworksWithName_error_(None, None)
            if networks is None:
                print("Could not locate wifi network. Please enter SSID")
                ssid = input("SSID: ")
                continue
            matching_networks = []
            for network in networks:
                if ssid in network.ssid():
                    matching_networks.append(network)
            if len(matching_networks) > 1:
                print("Found multiple matching networks. Please select the correct one")
                for i, e in enumerate(matching_networks):
                    print("[{}] {}".format(i, e.ssid()))
                choice = -1
                while choice not in range(0, len(matching_networks)):
                    try:
                        choice = int(input("Choose: "))
                    except ValueError:
                        pass
                return matching_networks[choice]
            elif len(matching_networks) == 1:
                return matching_networks[0]
            print("Could not locate wifi network. Please enter SSID")
            ssid = input("SSID: ")

    def getTeamNumber(self, hostname=None):
        dirty = True
        cfg = configparser.ConfigParser()
        cfg.setdefault("auth", {})

        if exists(".deploy_cfg"):
            cfg.read(".deploy_cfg")
            dirty = False

        if hostname is not None:
            dirty = True
            cfg["auth"]["hostname"] = str(hostname)

        hostname = cfg["auth"].get("hostname")

        if not hostname:
            dirty = True

            print("Robot setup (hit enter for default value):")
            while not hostname:
                hostname = input("Team number: ")

            cfg["auth"]["hostname"] = hostname

        if dirty:
            with open(".deploy_cfg", "w") as fp:
                cfg.write(fp)
        return hostname

    def run(self, options, robot_class, **static_options):
        STARTING_WIFI_NETWORK = self.getCurrentWifiNetwork()
        if STARTING_WIFI_NETWORK is not None:
            STARTING_WIFI_NETWORK_PSK = self.getWifiPassword(STARTING_WIFI_NETWORK)
        hostname_or_team = options.robot
        if not hostname_or_team and options.team:
            hostname_or_team = options.team
        team_number = self.getTeamNumber(hostname=hostname_or_team)
        team_network = self.findNetwork(team_number)

        _, _ = CWInterface.interface().associateToNetwork_password_error_(
            team_network, self.getWifiPassword(team_network.ssid()), None
        )
        try:
            self.deploy.run(options, robot_class, **static_options)
        finally:
            print(STARTING_WIFI_NETWORK)
            orig_network = self.findNetwork(STARTING_WIFI_NETWORK)
            _, _ = CWInterface.interface().associateToNetwork_password_error_(
                orig_network, STARTING_WIFI_NETWORK_PSK, None
            )
