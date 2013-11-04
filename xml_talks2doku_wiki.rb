#!/usr/bin/env ruby
# encoding: utf-8

# This script can be used to create a doku wiki table to track the status of recorded events.

require 'rexml/document'
require 'net/http'
require 'optparse'

# option parsing
options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: #{$0} [options]"

  opts.on("-u", "--url URL", String, "Frab url to xml schedule") do |url|
    options[:url] = url
  end

  opts.on("-r", "--rooms x,y,z", Array, "List of rooms for pattern matching") do |rooms|
    options[:rooms] = rooms
  end

  opts.separator ""

  opts.on_tail("-e", "--example", "Show example script call") do
    puts "ruby #{$0} -u https://hannover.ccc.de/frab/en/hackover13/public/schedule.xml -r '1\.4,2\.1'"
    exit
  end

  opts.on_tail("-h", "--help", "Show this message") do
    puts opts
    exit
  end

  if ARGV.size == 0 || ARGV.size > 4
    puts opts
    exit
  end
end.parse!

# http schedule request
url          = URI.parse(options[:url])
http         = Net::HTTP.new(url.host, url.port)
http.use_ssl = (url.scheme == 'https')
response     = http.start {|http| http.request( Net::HTTP::Get.new(url.path) )}

# parse xml
xml_data   = REXML::Document.new( response.body )
conference = REXML::XPath.first(xml_data, '//conference/title').text
days       = REXML::XPath.match(xml_data, '//*/day')

puts "~~NOTOC~~"
puts
puts "= #{conference}"

days.each do |day|
  puts "== #{day.attribute(:date).value}"
  puts "^ ID ^ Slug ^ h264 ^ webm ^ opus ^ mp3  ^ Comment ^"

  day.get_elements('./*/event').each do |event|
    room =  event.get_elements('./room')[0].text
    slug =  event.get_elements('slug').last.text.gsub(':', '_')
    id   =  event.attribute(:id).value

    next unless room =~ /#{options[:rooms].join('|')}/

    puts "| #{id} | #{slug} | | | | | |"
  end
end