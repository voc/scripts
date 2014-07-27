#!/usr/bin/python3
import gi
import signal

gi.require_version('Gst', '1.0')
from gi.repository import Gst, Gtk, GObject

GObject.threads_init()
Gst.init(None)

signal.signal(signal.SIGINT, signal.SIG_DFL)

class Main:
	def __init__(self):
		self.pipeline = Gst.Pipeline()

		self.uridecoder = Gst.ElementFactory.make('uridecodebin', 'uridecoder')
		self.uridecoder.set_property("uri", "http://video.blendertestbuilds.de/download.blender.org/ED/ED_1280.avi")
		self.uridecoder.connect("pad-added", self.OnDynamicPad)
		self.pipeline.add(self.uridecoder)

		self.monitorvideosink = Gst.ElementFactory.make('autovideosink', 'monitorvideosink')
		self.pipeline.add(self.monitorvideosink)
		
		self.monitoraudiosink = Gst.ElementFactory.make('autoaudiosink', 'monitoraudiosink')
		self.pipeline.add(self.monitoraudiosink)

		self.pipeline.set_state(Gst.State.PLAYING)


	def OnDynamicPad(self, uridecodebin, src_pad):
		caps = src_pad.query_caps(None).to_string()
		if caps.startswith('audio/'):
			src_pad.link(self.monitoraudiosink.get_static_pad("sink"))
		else:
			src_pad.link(self.monitorvideosink.get_static_pad("sink"))

start=Main()
Gtk.main()
