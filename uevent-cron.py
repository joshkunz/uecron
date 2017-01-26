#!/usr/bin/env python

import re
import socket
from collections import namedtuple, defaultdict
import shlex
import os
import subprocess

# This value seems to be pretty damn stable across versions of the linux kernel.
# Unfortunately, it's a #define and it's not exported by python's socket library,
# so, to get it programmaticially we would either have to do something fragile
# (grep) or something heavyweight (compile a test program). Just hardcoding it
# as 15 seems to be an ok-enough solution.
NETLINK_KOBJECT_UEVENT = 15

Rule = namedtuple("Rule", ["device", "action", "command"])

class Config(object):
    WS = re.compile(r"\s+")

    @classmethod
    def from_file(kls, f):
        config = kls()
        for line in f:
            line = line.strip()
            if line[0] == '#':
                continue
            device, action, command = kls.WS.split(line, 2)
            rule = Rule(device, action, command)
            config.add_rule(rule)
        return config

    def add_rule(self, rule):
        self.rules[rule.device][rule.action].append(rule)

    def __init__(self, rules=[]):
        self.rules = defaultdict(lambda: defaultdict(list))

        for rule in rules:
            self.add_rule(rule)

    def match(self, device, action):
        return self.rules.get(device, {}).get(action, [])


class Manager(object):
    # it's what's used in the netlink(7) manpage
    RECV_BUFFER_SIZE = 4096

    def __init__(self, config):
        self.config = config

    def connect(self):
        sock = socket.socket(socket.AF_NETLINK, 
                             socket.SOCK_RAW, 
                             NETLINK_KOBJECT_UEVENT)

        # bind the sock to a kernel-assigned PID and 
        # the KOBJECT_UEVENT group
        sock.bind((0, NETLINK_KOBJECT_UEVENT))
        return sock

    @classmethod
    def _next_msg(kls, sock):
        while True:
            msg, ctl, flags, addr = sock.recvmsg(kls.RECV_BUFFER_SIZE)
            if msg.startswith(b"libudev"):
                continue
            msg = str(msg, "utf-8")
            fields = msg.split("\0")[1:-2]
            parsed = {}
            for field in fields:
                key, value = field.split("=", 1)
                parsed[key] = value
            return parsed

    def handle_msg(self, msg, timeout=30):
        rules = self.config.match(msg["DEVPATH"], msg["ACTION"])
        for rule in rules:
            command = shlex.split(rule.command)
            new_env = dict(os.environ)
            new_env.update(msg)
            with subprocess.Popen(command, env=new_env) as proc:
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutException:
                    proc.terminate()

    def run(self):
        sock = self.connect()
        while True:
            msg = self._next_msg(sock)
            self.handle_msg(msg)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", required=True, nargs=1,
                        type=argparse.FileType('r'),
                        help="Path to configuration file")
    args = parser.parse_args()
    conf = Config.from_file(args.config[0])
    manager = Manager(conf)
    manager.run()
