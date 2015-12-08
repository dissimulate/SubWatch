import hook
import time

from threading import Thread

@hook.event('PRIVMSG')
def pm(prefix, chan, params):

    if chan == bot.nick:

        bot.log('%s: %s' % (prefix[0], ' '.join(params)))


@hook.event('PING')
def ping(prefix, chan, params):

    bot.do('PONG', params[0])


@hook.event('INVITE')
def invited(prefix, chan, params):

    bot.do('JOIN', params[0])


@hook.event('001')
def logged_in(prefix, chan, params):

    bot.nick = chan

    print('Connected to IRC.')

    time.sleep(2)

    if bot.config.get('oper', False):

        bot.oper()

    bot.join(bot.config['chans'])


@hook.event('NICK')
def nick_changed(prefix, chan, params):

    if prefix[0] == bot.nick:

        bot.nick = chan


@hook.event('JOIN')
def bot_joined(prefix, destination, params):

    if prefix[0] == bot.nick:

        bot.chans.append(params[0])

        if params[0] not in bot.config['chans']:

            bot.config['chans'].append(params[0])

            bot.save()


@hook.event('PART')
def bot_parted(prefix, destination, params):

    if prefix[0] == bot.nick:

        bot.chans.remove(destination)

        if destination in bot.config['chans']:

            bot.config['chans'].remove(destination)

            bot.save()


@hook.event('KICK')
def bot_kicked(prefix, destination, params):

    if params[0] == bot.nick:

        bot.chans.remove(destination)

        if destination in bot.config['chans']:

            bot.config['chans'].remove(destination)

            bot.save()

# check user status for flag requirements

@hook.event('352')
def check_ops(prefix, chan, params):

    # [channel, ident, host, server, nick, status (* staff, !@%+, G away), hopcount, realname]

    if len(params) < 8: return

    nick = params[4]
    chan = params[0]
    stat = params[5]

    for thing in bot.perms_check:

        if thing['nick'] == nick and thing['chan'] == chan:

            for perm in thing['perm']:

                if perm in stat:

                    Thread(target=thing['func'], args=thing['args']).start()

                    bot.perms_check.remove(thing)

                    return

            bot.perms_check.remove(thing)
