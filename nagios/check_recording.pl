#!/usr/bin/env perl

use v5.14;
use warnings;

use File::Find;

my $threshold = 60;

my $okay = 0;
my $delta_okay;
my $name_okay;

sub test {
        my $name = $File::Find::name;

        return unless -f $name;
        return unless $name =~ /\.dv/i;

        my $mtime = (stat($name))[9];

        my $delta = time - $mtime;

        if($delta < $threshold) {
                $okay = 1;
                $delta_okay = $delta;
                $name_okay = $name;
        }
}

{
        no warnings;
        find({no_chdir => 1, wanted => \&test}, $AR
}

if($okay) {
        say "OK delta is $delta_okay (current file:
        exit 0;
} else {
        say "CRITICAL no recordings for more than $
        exit 2;
}
