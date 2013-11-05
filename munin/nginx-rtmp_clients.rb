#!/usr/bin/env ruby
# encoding: utf-8

require 'rexml/document'
require 'net/http'

def get_xml(url)
  url          = URI.parse(url)
  http         = Net::HTTP.new(url.host, url.port)
  http.use_ssl = (url.scheme == 'https')
  response     = http.start { |http| http.request( Net::HTTP::Get.new(url.path) ) }
end

def parse_stat_xml(url)
  xml_data = REXML::Document.new( get_xml(url).body )
  clients = { }
  clients[:push] = REXML::XPath.match(xml_data, '//client/publishing').count
  clients[:pull] = REXML::XPath.match(xml_data, '//client').count - clients[:push]
end

def get_clients
  all = 0

  URLS.each_with_index do |url, index|
    count = parse_stat_xml(url)
    puts "#{index}.value #{count}"
    all += count
  end

  puts "all.value #{all}"
end

# show config
def show_config
  puts "graph_title Nginx rtmp clients count"
  puts 'graph_category nginx'
  puts 'graph_vlabel Count'
  puts 'all.label all'
  URLS.each_with_index do |url, index|
    puts "#{index}.label #{URI.parse(url).host}"
  end
end


if ENV['urls'].nil?
  puts "Configure urls:"
  puts "  [nginx-nrpe_*]"
  puts "    env.urls http://example.com/stats,http://exam.ple/stats"
  exit 1
else
  URLS = ENV['urls'].split(',')
end

if ARGV[0] == "config"
  show_config
else
  get_clients
end