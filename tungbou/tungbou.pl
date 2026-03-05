#!/usr/bin/perl

use strict;
use warnings;
no warnings "utf8";

use TOML::Tiny;
use Getopt::Long;
use Net::Ping;
use Path::Tiny;

my $config_path = "/etc/tungbou.conf";
my $dry = 0;

GetOptions
  'config=s' => \$config_path,
  'dry'      => \$dry,
;

if ( $dry )
{
  warn "running in dry mode, nothing will be changed\n"
}

my $config_text = path($config_path)->slurp_utf8;
my $config = from_toml $config_text;

my @roots = @{$config->{roots}};

foreach my $parent ( @roots )
{
  my @children = @{$parent->{children}};
  my $parent_dir = $parent->{dir} =~ s/~/$ENV{HOME}/r;
  print "$parent_dir\n";

  foreach my $child ( @children )
  {
    my $child_dir = $child->{dir};
    my $host = "$child->{hostname}.local";

    if ( not defined $child_dir )
    {
      warn "no directory configured for $host, skipping...\n";
      next;
    }

    my $command = "rsync -avhz --progress \"$parent_dir\" $host:\"$child_dir\"";

    if ( $dry )
    {
      print "$command\n";
    }
    else
    {
      print "testing connectivity to $host...\n";
      my $p = Net::Ping->new("tcp");

      die "$host is not reachable\n"
        unless $p->ping($host, 5);

      print "$command..? [Y/n]: ";
      my $answer = <STDIN>;
      chomp $answer;

      if ( $answer =~ /\Ano?\z/i )
      {
        warn "skipping sync for $host...\n";
        next;
      }
      else
      {
        system $command;
      }
    }
  }
}
