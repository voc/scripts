#!/usr/bin/env ruby
# encoding: utf-8

require 'pathname'

VERBOSE = false

WIKI_PAGE       = Pathname.new(Pathname.pwd + 'examples/git.txt')
NEW_WIKI_PAGE   = Pathname.new(Pathname.pwd + 'git.txt.result')
GITOLITE_CONFIG = Pathname.new(Pathname.pwd + 'examples/gitolite.conf')

# final data hashes
@repos  = {}
@groups = {}
# pattern for file manipulastion
@pattern = { start: "********** Managed by Script **********", end: "********** END **********" }

# Converts groups into dokuwiki table.
#
# @param [Hash]
# @return [Array]
def groups_to_dokuwiki_table(groups)
  table = [ "^ Gruppen Name ^ Mitglieder ^" ]

  groups.keys.sort.each do |group|
    table << "| #{group} | #{groups[group][:users].sort.map{ |u| "''#{u}''" }.join(', ') } |"
  end

  table
end

# Converts repositories into a dokuwiki table.
#
# @param [Hash]
# @return [Array]
def repositories_to_dokuwiki_table(repositories)
  table = [ "^ Name ^ Berechtigungen ^ Hooks ^ Kommentare ^" ]

  repositories.keys.sort.each do |repo|
    line = ''
    # repo name
    line << "| #{repo} | "
    # read-write permissions
    line << "read-write: #{repositories[repo][:write_access].map{ |u| "''#{u}''"}.join(', ')}\\\\ "
    # read permissions
    line << "read: #{repositories[repo][:read_access].map{ |u| "''#{u}''"}.join(', ')} | "
    # hooks
    line << "#{repositories[repo][:hooks].sort.map{ |h| "''#{h}''"}.join(', ')} | "
    # comment
    line << "#{repositories[repo][:comment].join(' ')} |"

    table << add_color(line, repositories[repo][:public])
  end

  table
end

def add_color(line, public_status)
  color = ''

  case public_status
    when /github/
      color = '@lightgreen:'
    when /http/
      color = '@lightsalmon:'
    else
      color = '@lightcoral:'
  end

  line.gsub!('| ', "| #{color}")
end

# Parse gitolite gitolite.conf file.
def parse_gitolite_config
  # variables for current status of parsing
  prev_line = { type: '', content: '' }
  current_repos, comments_to_repo = [], []

  File.read(GITOLITE_CONFIG).each_line do |line|
    case line
    # REPOSITORIES
    when /^\s*repo/
      repos = line.split(' ') - ['repo']
      repos.each do |repo|
        @repos[repo] = { read_access: [], write_access: [], hooks: [], comment: comments_to_repo, public: 'false' }
      end

      prev_line     = { type: 'repo', content: line }
      current_repos = repos
      comments_to_repo = []
    # GROUPS
    when /^\@/
      group = line.match(/(\@.*?\s)/)[0].strip
      users = line.split(' ') - [group, '=']

      @groups[group] = { users: users }
      prev_line = { type: 'group', content: line }
    # READ ONLY
    when /^\s+R\s/
      current_repos.each do |repo|
        @repos[repo][:read_access] = line.split - ['=', 'R']

        if @repos[repo][:read_access].include? "daemon"
          @repos[repo][:public] = 'http'
        end
      end

      prev_line = { type: 'permission', content: line }
    # WRITE ONLY
    when /^\s+RW[\s+]/
      current_repos.each do |repo|
        @repos[repo][:write_access] = line.split - ['=', 'RW', "RW+"]
      end

      prev_line = { type: 'permission', content: line }
    # COMMENTS
    when /^\s*\#/
      line.gsub!('#', '')
      comments_to_repo << line.strip

      prev_line = { type: 'comment', content: line }
    # HOOKS
    when /^\s*config\shooks\.run/
      line.sub!(/config\shooks.run\s*\=/, '')

      current_repos.each do |repo|
        @repos[repo][:hooks] = line.split(' ')
        if line =~ /github/
          @repos[repo][:public] = 'github'
        end
      end
    else
      next
    end
  end
end

# Extracts
#
# return [Array]
def read_original_content
  content, skip = [], false

  File.read(WIKI_PAGE).each_line do |line|
    if line =~ /#{@pattern[:start].gsub('*', '\*')}/
      skip = true
      content << line
    elsif line =~ /#{@pattern[:end].gsub('*', '\*')}/
      skip = false
    end

    next if skip

    content << line
  end

  content
end

# Inserts parsed data into original content.
#
# @param [Array]
# @return [Array]
def insert_into_original(content)
  new_content = []

  content.each do |con|
    if con =~ /#{@pattern[:start].gsub('*', '\*')}/
      new_content << con
      new_content << "" # newline
      new_content << "=== Gruppen"
      new_content << "" # newline
      new_content << groups_to_dokuwiki_table(@groups)
      new_content << "" # newline
      new_content << "=== Repositories"
      new_content << "" # newline
      new_content << repositories_to_dokuwiki_table(@repos)
      new_content << "" # newline
    else
      new_content << con
    end
  end

  new_content
end

# Writes new git.txt file
def write_to_file
  content = read_original_content

  File.open(NEW_WIKI_PAGE, 'w') do |file|
    insert_into_original(content).each do |line|
      file.puts line
    end
  end
end

begin
  parse_gitolite_config

  # stdout OUTPUT
  if VERBOSE
    puts "# parsed repos"
    p @repos
    puts "# parsed groups"
    p @groups
  end

  write_to_file
end
