import hook
import os
import sys
import time
import threading
import style

@hook.command('divert', perm='admin')
def divert(prefix, chan, params):

    bot.config.get('divert', {})[params[0]] = params[1]

    bot.save()

    
@hook.command('undivert', perm='admin')
def undivert(prefix, chan, params):

    del bot.config.get('divert', {}).get(params[0])

    bot.save()


@hook.command('say', perm='admin')
def say(prefix, chan, params):

    bot.say(params[0], ' '.join(params[1:]))


@hook.command('announce', perm='admin')
def announce(prefix, chan, params):

    for ch in bot.chans:

        bot.say(ch, '%s: %s' % (style.color('Ann', style.RED), ' '.join(params)))


@hook.command('act', perm='admin')
def act(prefix, chan, params):

    bot.ctcp(params[0], 'ACTION', ' '.join(params[1:]))


@hook.command('flood', perm='admin')
def flood(prefix, chan, params):

    for i in range(int(params[1])):

        bot.say(params[0], ' '.join(params[2:]))


@hook.command('raw', perm='admin')
def raw(prefix, chan, params):

    bot.send(' '.join(params))


@hook.command('ignore', perm='staff')
def ignore(prefix, chan, params):

    bot.config.get('ignore', []).append(params[0])

    bot.save()


@hook.command('unignore', perm='staff')
def unignore(prefix, chan, params):

    if params[0] in bot.config.get('ignore', []):

        bot.config.get('ignore').remove(params[0])

        bot.save()


@hook.command('restart', perm='admin')
def restart(prefix, chan, params):

    bot.do('QUIT', ' '.join(params))

    bot.oqueue.join()

    os.execl(sys.executable, sys.executable, * sys.argv)


@hook.command('reload', perm='admin')
def reload(prefix, chan, params):

    bot.load()


@hook.command('nick', perm='admin')
def nick(prefix, chan, params):

    bot.do('NICK', params[0])


@hook.command('quit', perm='admin')
def quit(prefix, chan, params):

    bot.disconnect()


@hook.command('oper', perm='admin')
def oper(prefix, chan, params):

    bot.oper()


@hook.command('join', perm='admin')
def join_chan(prefix, chan, params):

    bot.join(params)


@hook.command('part', perm='admin')
def part_chan(prefix, chan, params):

    if len(params):

        bot.part(params)

    else:

        bot.part([chan])


@hook.command('sys', perm='admin')
def sysinfo(prefix, chan, params):

    seconds = time.time() - bot.start_time

    times = []

    days = seconds // 86400
    hours = seconds // 3600 % 24
    minutes = seconds // 60 % 60
    seconds = seconds % 60

    if days: times.append('%s days' % int(days))
    if hours: times.append('%s hours' % int(hours))
    if minutes: times.append('%s minutes' % int(minutes))
    if seconds: times.append('%s seconds' % int(seconds))

    bot.say(chan, 'Uptime: %s Threads: %s' % (
        ', '.join(times),
        threading.activeCount()
        ))
