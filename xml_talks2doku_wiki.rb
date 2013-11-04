#!/usr/bin/env ruby
# encoding: utf-8

require 'open-uri'
require 'nokogiri'

xml_data = Nokogiri::XML(open("https://hannover.ccc.de/frab/en/hackover13/public/schedule.xml"))

conference = xml_data.xpath('//conference/title').text
days       = xml_data.xpath('//*/day')

puts "~~NOTOC~~"
puts
puts "= #{conference}"

days.each do |day|
  puts "== #{day[:date]}"
  puts "^ ID ^ Slug ^ h264 ^ webm ^ opus ^ mp3  ^ Comment ^"

  day.xpath('./*/event').each do |event|
    puts "| #{event[:id]} | #{event.at_xpath('slug').text.gsub(':', '_')} | | | | | |"
  end
end
