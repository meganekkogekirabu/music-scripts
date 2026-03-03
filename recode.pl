#!/usr/bin/env perl

use strict;
use warnings;

use File::Copy;
use Getopt::Long;

my $dry = 0;
my $format = "wav";

GetOptions
  "dry"      => \$dry,
  "format=s" => \$format,
;

# maybe convert to a whitelist instead?
my @ignore = (
  "jpg", "jpeg", "png",
  "ogg", "wav", "mp3", "m4a",
);

my $args = ". -type f ! \\( ";
$args .= join " -o ", map { "-name '*.$_'" } @ignore;
$args .= " \\) -not -path ./.scripts/*";

my @toRecode = split "\n", `find $args`;

sub recode
{
  my $original = $_[0];
  my $new = $original =~ s/^(.+)\..+$/$1.$format/r;

  if ( $new eq $original )
  {
    move $original, "$original.old";
    $original .= ".old";
  }

  my @args = ("-i", $original, "-y", $new);

  system "ffmpeg", @args
    unless $dry;
}

recode $_ foreach @toRecode;
