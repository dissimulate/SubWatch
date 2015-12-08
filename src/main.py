import sys
import signal

from bot import DissBot

if __name__ == "__main__":

    bot = DissBot()

    # bot.debug = True

<<<<<<< HEAD

=======
>>>>>>> upstream/master
    def signal_handler(signal, frame):

        print('\nShutting down...')

        bot.die()

        sys.exit()


    signal.signal(signal.SIGINT, signal_handler)


    while 1:

        try:

            line = sys.stdin.readline().strip()

        except KeyboardInterrupt:

            break

        if not line: break

        if line == 'debug':

            bot.debug = not bot.debug

        elif line == 'dc':

            bot.disconnect()
<<<<<<< HEAD

        elif line == 'grow':

            bot.grow_threads()

        elif line == 'shrink':

            bot.shrink_threads()
=======
>>>>>>> upstream/master
