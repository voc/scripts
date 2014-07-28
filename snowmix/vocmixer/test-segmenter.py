#!/usr/bin/python3
import gi
import signal
import sys, inspect
from pprint import pprint

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

GObject.threads_init()
Gst.init(None)

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

		print("NewElement")
		self.newElement = NewElement()
		self.pipeline.add(self.newElement)
		self.muxer.link(self.newElement)

		print("multifilesink")
		self.filesink = Gst.ElementFactory.make('multifilesink', 'filesink')
		self.filesink.set_property("location", "test-%d.ts")
		self.filesink.set_property("next-file", 2)
		self.pipeline.add(self.filesink)
		self.newElement.link(self.filesink)

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

class VocSchnipselsSink(Gst.Element):
	pass

class NewElement(Gst.Element):
	""" A basic, buffer forwarding gstreamer element """

	#here we register our plugin details
	__gstmetadata__ = (
		"NewElement plugin",
		"newelement.py",
		"gst.Element, that passes a buffer from source to sink (a filter)",
		"Stephen Griffiths <scgmk5@gmail.com>")

	#source pad (template): we send buffers forward through here
	_srctemplate = Gst.PadTemplate.new('src',
		Gst.PadDirection.SRC,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.new_any())

	#sink pad (template): we recieve buffers from our sink pad
	_sinktemplate = Gst.PadTemplate.new('sink',
		Gst.PadDirection.SINK,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.new_any())

	#register our pad templates
	__gsttemplates__ = (_srctemplate, _sinktemplate)

	def __init__(self, *args, **kwargs):
		#initialise parent class
		Gst.Element.__init__(self, *args, **kwargs)

		#source pad, outgoing data
		self.srcpad = Gst.Pad.new_from_template(self._srctemplate, "src")

		#sink pad, incoming data
		self.sinkpad = Gst.Pad.new_from_template(self._sinktemplate, "sink")
		self.sinkpad.set_chain_function_full(self._sink_chain, None)

		#make pads available
		self.add_pad(self.srcpad)
		self.add_pad(self.sinkpad)

	def _sink_chain(self, pad, parent, buf):
		#this is where we do filtering
		#and then push a buffer to the next element, returning a value saying
		#it was either successful or not.
		print("buf of ", buf.get_size(), "bytes for pts ", buf.pts)
		return self.srcpad.push(buf)

def runmain():
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	start=Main()
	Gtk.main()

if __name__ == '__main__':
	runmain()
