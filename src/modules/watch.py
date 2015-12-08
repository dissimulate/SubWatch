import praw
import time
import hook
import style
import re
import sys
import math
import traceback
import types

from queue import Queue
from threading import Thread, activeCount


r = praw.Reddit(user_agent = 'IRC SubWatch by /u/Dissimulate')

try:

    r.refresh_access_information()

except:

    sys.exit('Failed to refresh access information.')

if r.user == None:

    sys.exit('Failed to auth.')

else:

    print('Authed as %s.' % r.user)


names = []
subs = Queue()

todel = []

shrink = Queue()

start_count = 4
thread_count = 0


def get_submissions(num):

    global subs
    global resize


    r = praw.Reddit(user_agent = 'IRC SubWatch by /u/Dissimulate')

    try:

        r.refresh_access_information()

    except:

        print('Failed to refresh access information, exiting thread %s.' % num)

        return


    if r.user == None:

        print('Failed to auth, exiting thread %s.' % num)

        return


    print('Watch thread %s started.' % num)


    start = bot.load_time


    while not bot.connected and start == bot.load_time:

        time.sleep(3)


    while bot.connected and start == bot.load_time:

        try:

            shrink.get_nowait()

            break

        except: pass


        names = []

        tocheck = {}


        while len(tocheck) < min(subs.qsize(), 25) and bot.connected and start == bot.load_time:

            sub = subs.get()

            if sub['name'] in todel:

                continue


            elapsed = time.time() - sub['checked']

            if elapsed < 30:

                subs.put(sub)

                time.sleep(2)

                continue

            elif elapsed > 60 and elapsed < 1400000000:

                print('DELAY: %s' % elapsed)


            names.append(sub['name'])

            tocheck[sub['name']] = sub


        if not len(tocheck):

            time.sleep(5)

            continue


        try:

            new_threads = []

            multisub = r.get_subreddit('+'.join(tocheck.keys()))


            for sub in tocheck:

                tocheck[sub]['checked'] = time.time()


            for thread in reversed(list(multisub.get_new(limit = len(tocheck) * 4))):

                sub = thread.subreddit.display_name

                if thread.created_utc > tocheck[sub.lower()]['thread']:

                    new_threads.append(thread)

                    tocheck[sub.lower()]['thread'] = thread.created_utc


            for thread in new_threads:

                sub = thread.subreddit.display_name

                prefix = 'Self post:' if thread.is_self else 'Link post:'

                message = '%s "%s" posted in /r/%s by %s. %s%s' % (
                    style.color(prefix, style.GREEN),
                    thread.title,
                    sub,
                    thread.author,
                    thread.short_link,
                    style.color(' NSFW', style.RED) if thread.over_18 else ''
                )

                for chan in bot.config['watch'][sub.lower()]:

                    if chan in bot.config['stopped']: continue

                    # channel has keywords set

                    if len(bot.config['watch'][sub.lower()][chan]):

                        words = bot.config['watch'][sub.lower()][chan]

                        minus = [x.lstrip('-') for x in words if x.startswith('-')]

                        if minus:

                            regex = re.compile(r'\b(%s)\b' % '|'.join(minus), re.I)

                            if re.search(regex, thread.title):

                                bot.say(chan, thread.title)

                                continue

                        plus = [x.lstrip('+') for x in words if x.startswith('+')]

                        if plus:

                            regex = re.compile(r'\b(%s)\b' % '|'.join(plus), re.I)

                            if re.search(regex, thread.title):

                                def repl(match):

                                    return style.bold(match.group(0))

                                new_title = re.sub(regex, repl, thread.title)

                                bot.say(chan, message.replace(thread.title, new_title))

                    else:

                        bot.say(chan, message)

        except:

            traceback.print_exc()

            print('Failed to fetch new posts. %s' % time.strftime('%H:%M:%S'))


        for sub in tocheck:

            subs.put(tocheck[sub])

        time.sleep(2)


def print_help(chan):

    bot.say(chan, 'Recent changes to syntax have been made, see: http://snoonet.org/SubWatch or join #subwatch for help.')


def process_params(params):

    items = {}

    last = ''

    for param in params:

        param = param.lower()

        if param.startswith('+') or param.startswith('-'):

            if not last: return False

            items[last].append(param)

        else:

            items[param] = []

            last = param

    return items


def access_denied(sub):

    global r

    try:

        public = r.get_subreddit(sub).subreddit_type

    except Exception as e:

        if isinstance(e, praw.errors.InvalidSubreddit):

            return 'fail'

        if isinstance(e, praw.errors.Forbidden):

            return 'denied'

        return 'fail'

    return 'private' if public != 'public' else False


def check_wiki(sub, chan):

    global r

    try:

        wiki = r.get_wiki_page(sub, 'subwatch').content_md

    except:

        return False

    chans = [x.strip().lower() for x in wiki.split(',')]

    if chan.lower() not in chans:

        return False

    return True


@hook.command('add', flags='%@')
def add_sub(prefix, chan, params):

    if chan == bot.nick: return

    try:

        items = process_params(params)

        if not items: raise

    except:

        print_help(chan)

        return


    updated_subs = []
    added_subs = []
    failed_subs = []
    denied_subs = []
    wiki_subs = []


    for sub in items:

        words = items[sub]

        # sub has previously been checked

        if sub in bot.config['watch']:

            if chan in bot.config['watch'][sub]:

                updated = False

                for word in words:

                    if word not in bot.config['watch'][sub][chan]:

                        bot.config['watch'][sub][chan].append(word)

                        updated = True

                if updated and sub not in updated_subs:

                    updated_subs.append(sub)

                continue

            else:

                denied = access_denied(sub)

                if denied == 'fail':

                    failed_subs.append(sub)

                    continue

                elif denied == 'denied':

                    denied_subs.append(sub)

                    continue

                elif denied == 'private' and not check_wiki(sub, chan):

                    wiki_subs.append(sub)

                    continue

                bot.config['watch'][sub][chan] = []

                for word in words:

                    bot.config['watch'][sub][chan].append(word)

                if sub not in added_subs:

                    added_subs.append(sub)

                continue


        # check if sub is private, doesn't exist or lacks permission

        denied = access_denied(sub)

        if denied == 'fail':

            failed_subs.append(sub)

            continue

        elif denied == 'denied':

            denied_subs.append(sub)

            continue

        elif denied == 'private' and not check_wiki(sub, chan):

            wiki_subs.append(sub)

            continue

        # add the sub to the channel

        bot.config['watch'][sub] = {}

        bot.config['watch'][sub][chan] = []

        for word in words:

            bot.config['watch'][sub][chan].append(word)

        if sub not in names:

            subs.put({'name': sub, 'thread': time.time(), 'checked': 0})

            names.append(sub)

        added_subs.append(sub)

    if added_subs:

        bot.say(chan, 'Added sub(s) %s.' % ', '.join(added_subs))

    if updated_subs:

        bot.say(chan, 'Updated keywords for %s.' % ', '.join(updated_subs))

    if failed_subs:

        bot.say(chan, 'Unable to add sub(s) %s.' % ', '.join(failed_subs))

    if denied_subs:

        bot.say(chan, 'Could not access sub(s) %s. /u/SnoonetSubWatch must be an approved submitter.' % ', '.join(denied_subs))

    if wiki_subs:

        bot.say(chan, 'Please add "%s" to /wiki/subwatch on %s. Multiple channels can be separated with a comma.' % (chan, ', '.join(wiki_subs)))

    bot.save()


@hook.command('del', flags='%@')
def del_sub(prefix, chan, params):

    if chan == bot.nick: return

    global todel

    try:

        items = process_params(params)

        if not items: raise

    except:

        print_help(chan)

        return


    removed_subs = []
    updated_subs = []


    for sub in items:

        words = items[sub]


        if sub not in bot.config['watch'] or chan not in bot.config['watch'][sub]:

            continue


        if words:

            updated = False

            for word in words:

                if word in bot.config['watch'][sub][chan]:

                    bot.config['watch'][sub][chan].remove(word)

                    updated = True

            if updated:

                updated_subs.append(sub)

            continue


        del bot.config['watch'][sub][chan]

        removed_subs.append(sub)

        if not bot.config['watch'][sub]:

            del bot.config['watch'][sub]

            todel.append(sub)


    if removed_subs:

        bot.say(chan, 'Removed sub(s) %s.' % ', '.join(removed_subs))

    if updated_subs:

        bot.say(chan, 'Updated keywords for %s.' % ', '.join(updated_subs))

    bot.save()


@hook.command('clear', flags='%@')
def clear(prefix, chan, params):

    if chan == bot.nick: return

    global todel

    for sub in list(bot.config['watch'].keys()):

        if chan in bot.config['watch'][sub]:

            del bot.config['watch'][sub][chan]

            if not bot.config['watch'][sub]:

                del bot.config['watch'][sub]

                todel.append(sub)

    bot.save()

    bot.say(chan, 'The watch list for %s has been cleared.' % chan)


@hook.command('list')
def list_sub(prefix, chan, params):

    if chan == bot.nick: return

    sublist = []

    for sub in bot.config['watch']:

        if chan in bot.config['watch'][sub]:

            if bot.config['watch'][sub][chan]:

                sub += ' (%s)' % ', '.join(bot.config['watch'][sub][chan])

            sublist.append(sub)

    sublist = ', '.join(sublist) if len(sublist) else 'None'

    bot.say(chan, 'Watched subs: %s' % sublist)


@hook.command('stop', flags='%@')
def stop(prefix, chan, params):

    if chan == bot.nick: return

    if chan not in bot.config['stopped']:

        bot.config['stopped'].append(chan)

        bot.save()

        bot.say(chan, 'SubWatch has been paused in %s.' % chan)


@hook.command('start', flags='%@')
def start(prefix, chan, params):

    if chan == bot.nick: return

    if chan in bot.config['stopped']:

        bot.config['stopped'].remove(chan)

        bot.save()

        bot.say(chan, 'SubWatch has been unpaused in %s.' % chan)


@hook.command('help')
def showhelp(prefix, chan, params):

    if chan == bot.nick: return

    print_help(chan)


@hook.event('PRIVMSG')
def pm(prefix, chan, params):

    if chan == bot.nick:

        print_help(prefix[0])


def grow_threads(self):

    global thread_count

    thread_count += 1

    print('Expanded thread count (%s)' % thread_count)

    self.thread(get_submissions, (thread_count,))

bot.grow_threads = types.MethodType(grow_threads, bot)


def shrink_threads(self):

    global shrink
    global thread_count

    thread_count -= 1

    print('Shrunk thread count (%s)' % thread_count)

    shrink.put(1)

bot.shrink_threads = types.MethodType(shrink_threads, bot)


def init():

    global subs
    global start_count
    global thread_count

    for sub in bot.config['watch']:

        subs.put({'name': sub, 'thread': time.time(), 'checked': 0})

        names.append(sub)

    print('Starting watch threads...')

    for i in range(start_count):

        thread_count += 1

        bot.thread(get_submissions, (thread_count,))

        time.sleep(1)


def wait():

    while not bot.nick:

        time.sleep(1)

    init()

bot.thread(wait)
