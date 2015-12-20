#!/usr/bin/env perl

use v5.12;
use strict;
use warnings;

use lib qw(lib/);

use LWP::Simple;
use Fahrplan;

sub get_schedule {
	my ($url) = @_;

	my $data = get($url) or die "getting schedule failed";

	return Fahrplan->new(string => $data);
}

if(@ARGV != 1) {
	say STDERR "usage: $0 frab-base-url";
	say STDERR "";
	say STDERR "e.g. $0 https://events.ccc.de/congress/2015/Fahrplan/";

	exit 1;
}

my $baseurl = $ARGV[0];

my $fahrplan = get_schedule("${baseurl}/schedule.xml");

foreach my $event (@{$fahrplan->events}) {
	if($event->{"recording.optout"} ne 'false') {
		printf "* [%s %s]\n", $baseurl . "events/" . $event->{id}, $event->{title};
	}
}
