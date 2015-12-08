import re
import sys
import time
import glob
import json
import os
import socket
import ssl
import style
import fnmatch
import traceback

from threading import Thread
from queue import Queue


class DissBot():

    config_file = 'config.json'

    debug = False

    conn = None

    connected = False

    iqueue = Queue()
    oqueue = Queue()

    config = {}

    events = {}
    commands = {}

    load_time = 0
    start_time = 0

    ibuffer = ''
    obuffer = b''

    m_times = {}

    nick = ''

    chans = []

    flood_check = {}

    perms_check = []


    def __init__(self):

        if not self.load():

            sys.exit('Exiting...')

        self.connect()

        self.thread(self.send_loop)
        self.thread(self.parse_loop)


    def thread(self, func, args=()):

        return Thread(target=func, args=args).start()


    def load(self):

        self.load_time = time.time()

        print('Loading config...')

        try:

            with open(self.config_file, 'r') as fp:

                self.config = json.load(fp)

        except:

            traceback.print_exc()

            print('ERROR: failed to load %s' % self.config_file)

            return False

        print('Loading modules...')

        self.commands = {}
        self.events = {}

        try:

            files = set(glob.glob(os.path.join('modules', '*.py')))

            for file in files:

                with open(file, 'r') as fp:

                    code = compile(fp.read(), file, 'exec')

                namespace = {'bot': self}

                eval(code, namespace)

                commands = []
                events = []

                for obj in namespace.values():

                    if hasattr(obj, '_command'):

                        for command in obj._command:

                            if command not in self.commands:

                                self.commands[command] = []

                            self.commands[command].append(obj)

                    if hasattr(obj, '_event'):

                        for event in obj._event:

                            if event not in self.events:

                                self.events[event] = []

                            self.events[event].append(obj)

                print('Module loaded: %s' % file)

        except:

            traceback.print_exc()

            print('ERROR: failed to load modules')

            return False

        print('Successfully loaded.')

        return True


    def save(self):

        with open(self.config_file, 'w') as fp:

            json.dump(self.config, fp, indent=4, sort_keys=True)


    def die(self):

        self.disconnect()

        self.iqueue.put('')


    def disconnect(self):

        if self.connected:

            self.connected = False

            self.do('QUIT')

            self.socket.close()


    def connect(self):

        print('Connecting to IRC...')

        self.start_time = time.time()

        ip = socket.AF_INET6 if self.config['ipv6'] else socket.AF_INET

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket = ssl.wrap_socket(s) if self.config['ssl'] else s

        self.socket.connect((self.config.get('server', ''), self.config.get('port', 6667)))

        if self.config.get('pass', False):

            self.send('PASS %s' % self.config['pass'])

        self.send('NICK %s' % self.config.get('nick', 0))

        self.send('USER %s 3 * :%s' % (
            self.config.get('ident', 'DissBot'),
            self.config.get('realname', 'DissBot')
        ))

        self.connected = True

        self.thread(self.recv_loop)

    # loops

    def parse_loop(self):

        while self.connected:

            msg = self.iqueue.get()

            if msg == StopIteration:

                self.connect()

                continue

            if self.debug and msg: print(msg)

            regex = re.compile(
            r'^(:([^@!\ ]*)(?:(?:\!([^@]*))?@([^\ ]*))?\ )?([^\ ]+)\ ?((?:[^:\ ]*){0,14})(?:\ :?(.*))?$')

            try:

                prefix, nick, ident, host, type, chan, message = re.findall(regex, msg)[0]

            except: continue

            message = style.remove(message)

            params = message.split(' ')

            prefix = prefix.lstrip(':').strip()

            # do events

            if type in self.events:

                for func in self.events[type]:

                    self.thread(func, ((nick, ident, host), chan, params))

            # do commands

            if type == 'PRIVMSG' and params[0].startswith(self.config.get('prefix', '$')):

                command = params[0][1:]

                params.pop(0)

                ignore = self.config.get('ignore', [])

                if command in self.commands and not self.match(ignore, prefix):

                    self.log('%s %s called by %s in %s (%s)' % (
                        style.color('Command:', style.GREEN),
                        command,
                        nick,
                        chan,
                        ', '.join(params)
                        ))

                    if chan == self.nick:

                        chan = nick

                    for func in self.commands[command]:

                        # must be performed in specific channel

                        if hasattr(func, '_channel'):

                            if getattr(func, '_channel') != chan:

                                continue

                        # command can or must be diverted

                        where = chan

                        divert = bot.config.get('divert', {})

                        if hasattr(func, '_divert') or hasattr(func, '_control'):

                            if chan in redirect:

                                where = divert[chan]

                            elif hasattr(func, '_control'):

                                continue

                            if where not in self.chans:

                                continue

                        # admin perm overrides all

                        admin = self.config['perms'].get('admin', {})

                        if self.match(admin, prefix):

                            pass

                        # user must have permission, overrides flags

                        elif hasattr(func, '_perm'):

                            perm = getattr(func, '_perm')

                            if perm not in self.config['perms']:

                                continue

                            if not self.match(self.config['perms'][perm], prefix):

                                continue

                        # user must have specific flag(s)

                        elif hasattr(func, '_flags'):

                            self.perms_check.append({
                                'nick': nick,
                                'func': func,
                                'perm': getattr(func, '_flags'),
                                'chan': where,
                                'args': ((nick, ident, host), where, params)
                            })

                            self.do('WHO', where)

                            continue

                        self.thread(func, args=((nick, ident, host), where, params))

        print('Exited parse loop.')


    def recv_loop(self):

        recv_time = time.time()

        while self.connected:

            try:

                data = self.socket.recv(4096)

                self.ibuffer += data.decode()

                if data:

                    recv_time = time.time()

                else:

                    if time.time() - recv_time > self.config.get('timeout', 60):

                        self.iqueue.put(StopIteration)

                        self.socket.close()

                        break

                    time.sleep(1)

            except: continue

            while '\r\n' in self.ibuffer:

                line, self.ibuffer = self.ibuffer.split('\r\n', 1)

                self.iqueue.put(line)

        print('Exited recv loop.')


    def send_loop(self):

        while self.connected:

            line = self.oqueue.get().splitlines()[0][:510]

            self.obuffer += line.encode('utf-8', 'replace') + b'\r\n'

            while self.obuffer:

                try:

                    sent = self.socket.send(self.obuffer)

                    self.obuffer = self.obuffer[sent:]

                except: break

            self.oqueue.task_done()

        print('Exited send loop.')


    def match(self, patterns, str):

        if not isinstance(patterns, list):

            patterns = [patterns]

        match = [n for n in patterns if fnmatch.fnmatch(str, n)]

        return match

    # irc actions

    def join(self, chans):

        if not isinstance(chans, list):

            chans = [chans]

        for chan in chans:

            print('JOIN', chan)

            self.do('JOIN', chan)


    def part(self, chans):

        if not isinstance(chans, list):

            chans = [chans]

        for chan in chans:

            print('PART', chan)

            self.do('PART', chan)


    def oper(self):

        if self.config.get('oper_name') and self.config.get('oper_pass'):

            self.do('OPER', self.config['oper_name'], self.config['oper_pass'])

    # output

    def log(self, text):

        if self.config.get('log', False):

            self.say(self.config['log'], text)

        print(style.remove(text))


    def say(self, target, text, notice=False):


        mode = 'NOTICE' if notice else 'PRIVMSG'


        if target not in self.flood_check:

            self.flood_check[target] = [time.time(), 0]


        diff = time.time() - self.flood_check[target][0]

        delay = self.config.get('flood_delay', 0.2)

        limit = self.config.get('flood_limit', 10)


        if diff < delay:

            self.flood_check[target][1] += 1

        else:

            self.flood_check[target][1] -= min(int(diff / delay), self.flood_check[target][1])


        self.flood_check[target][0] = time.time()


        if self.flood_check[target][1] >= limit:

            if self.flood_check[target][1] == limit:

                self.log('Flood triggered in %s.' % target)

        else:

            self.do(mode, target, text)


    def ctcp(self, target, ctcp, text):

        self.do('PRIVMSG', target, '\x01%s %s\x01' % (ctcp, text))


    def do(self, command, *args):

        self.send(command + ' ' + ' '.join(args))


    def send(self, str):

        self.oqueue.put(str)
