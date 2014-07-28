#!/usr/bin/python3
import gi
import signal
import sys, inspect
from pprint import pprint

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

class Main:
	def __init__(self):
		self.pipeline = Gst.Pipeline()

		print("decoder")
		self.decoder = Gst.ElementFactory.make('uridecodebin', 'decoder')
		self.decoder.set_property("uri", "http://video.blendertestbuilds.de/download.blender.org/ED/ED_1280.avi")
		self.decoder.connect("pad-added", self.OnDynamicPad)
		self.pipeline.add(self.decoder)

		# decoder -> converter will be linked on dynamic pad creation

		print("converter")
		self.converter = Gst.ElementFactory.make('videoconvert', 'converter')
		self.pipeline.add(self.converter)

		print("videorate")
		self.rate = Gst.ElementFactory.make('videorate', 'rate')
		self.pipeline.add(self.rate)
		self.converter.link(self.rate)

		print("encodercaps")
		self.encodercaps = Gst.ElementFactory.make('capsfilter', 'encodercaps')
		self.encodercaps.set_property('caps', Gst.Caps.from_string('video/x-raw, framerate=25/1'))
		self.pipeline.add(self.encodercaps)
		self.rate.link(self.encodercaps)

		print("encoder")
		self.encoder = Gst.ElementFactory.make('avenc_mpeg2video', 'encoder')
		self.pipeline.add(self.encoder)
		self.encodercaps.link(self.encoder)

		print("muxer")
		self.muxer = Gst.ElementFactory.make('mpegtsmux', 'muxer')
		self.pipeline.add(self.muxer)
		self.encoder.link(self.muxer)

		print("filesink")
		self.filesink = Gst.ElementFactory.make('filesink', 'filesink')
		self.filesink.set_property("location", "test.ts")
		self.pipeline.add(self.filesink)
		self.muxer.link(self.filesink)

		print("PLAYING")
		self.pipeline.set_state(Gst.State.PLAYING)

	def OnDynamicPad(self, uridecodebin, src_pad):
		caps = src_pad.query_caps(None).to_string()
		srcname = uridecodebin.get_name()
		print("{0}-source of {1} online".format(caps.split(',')[0], srcname))

		if caps.startswith('video/'):
			sinkpad = self.converter.get_static_pad("sink")

			# link the first audio-stream and be done
			if not sinkpad.is_linked():
				src_pad.link(sinkpad)


def runmain():
	GObject.threads_init()
	Gst.init(None)

	signal.signal(signal.SIGINT, signal.SIG_DFL)
	start=Main()
	Gtk.main()

if __name__ == '__main__':
	runmain()
