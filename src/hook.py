import inspect

def command(*args, **kwargs):

    def set_command(func):

        if inspect.isfunction(func):

            if not hasattr(func, '_command'):

                func._command = []

            for kw in kwargs:

                setattr(func, '_' + kw, kwargs.get(kw, False))

            for arg in args:

                if arg not in func._command:

                    func._command.append(arg)

        return func

    return set_command


def event(*args, **kwargs):

    def set_event(func):

        if inspect.isfunction(func):

            if not hasattr(func, '_event'):

                func._event = []

            for kw in kwargs:

                setattr(func, '_' + kw, kwargs.get(kw, False))

            for arg in args:

                if arg not in func._event:

                    func._event.append(arg)

        return func

    return set_event
