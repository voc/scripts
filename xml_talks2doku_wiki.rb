#!/usr/bin/env ruby
# encoding: utf-8

require 'rexml/document'
require 'net/http'

url          = URI.parse('https://hannover.ccc.de/frab/en/hackover13/public/schedule.xml')
http         = Net::HTTP.new(url.host, url.port)
http.use_ssl = (url.scheme == 'https')
response     = http.start {|http| http.request( Net::HTTP::Get.new(url.path) )}

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
    puts "| #{event.attribute(:id).value} | #{event.get_elements('slug').last.text.gsub(':', '_')} | | | | | |"
  end
end
