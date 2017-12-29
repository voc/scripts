#!/usr/bin/env python3
import gi
import signal
import logging
import sys

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GObject

# import local classes
from lib.loghandler import LogHandler

# check min-version
minGst = (1, 5)
minPy = (3, 0)

Gst.init([])
if Gst.version() < minGst:
    raise Exception('GStreamer version', Gst.version(),
                    'is too old, at least', minGst, 'is required')

if sys.version_info < minPy:
    raise Exception('Python version', sys.version_info,
                    'is too old, at least', minPy, 'is required')


# init GObject & Co. before importing local classes
GObject.threads_init()

# main class
class DecklinkToTcp(object):

    def __init__(self):
        self.log = logging.getLogger('DecklinkToTcp')
        self.log.debug('creating GObject-MainLoop')
        self.mainloop = GObject.MainLoop()

        from lib.args import Args

        pipeline = """
            decklinkvideosrc
                device-number={device}
                connection={connection}
                mode={mode}
                name=v !
            queue ! mux.

            decklinkaudiosrc
                {channels}
                device-number={device}
                connection={audioconnection} !
            queue ! mux.

            matroskamux name=mux streamable=true !
                tcpserversink
                blocksize=1048576
                buffers-max=10000
                sync-method=next-keyframe
                port=20000
                host=0.0.0.0
        """.format(
            device=Args.device,
            connection=Args.connection,
            audioconnection=Args.audioconnection,
            mode=Args.mode,
            channels="channels={}".format(Args.channels)
                if Args.channels > 2 else ""
        )

        self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
        pipeline = Gst.parse_launch(pipeline)

        self.log.debug('Launching Mixing-Pipeline')
        pipeline.set_state(Gst.State.PLAYING)

    def run(self):
        self.log.info('running GObject-MainLoop')
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self):
        self.log.info('quitting GObject-MainLoop')
        self.mainloop.quit()


# run mainclass
def main():
    # parse command-line args
    from lib import args
    args.parse()

    from lib.args import Args
    docolor = (Args.color == 'always') or (Args.color == 'auto' and
                                           sys.stderr.isatty())

    handler = LogHandler(docolor, Args.timestamp)
    logging.root.addHandler(handler)

    if Args.verbose >= 2:
        level = logging.DEBUG
    elif Args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.root.setLevel(level)

    # make killable by ctrl-c
    logging.debug('setting SIGINT handler')
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.info('Python Version: %s', sys.version_info)
    logging.info('GStreamer Version: %s', Gst.version())

    # init main-class and main-loop
    logging.debug('initializing DecklinkToTcp')
    main = DecklinkToTcp()

    logging.debug('running DecklinkToTcp')
    main.run()


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)
