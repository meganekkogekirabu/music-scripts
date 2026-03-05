#!/usr/bin/perl

use strict;
use warnings;

use Config::Any::TOML;
use Getopt::Long;
use Net::Ping;

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

my $config = Config::Any::TOML->load($config_path);

my $parent = $config->{parent};
my @children = $parent->{children}[0];
my $parent_dir = glob $parent->{dir};

foreach my $child ( @children )
{
  my $child_dir = $child->{dir};

  if ( not defined $child_dir )
  {
    warn "no directory configured for $child, skipping...\n";
    next;
  }

  my $host = "$child->{hostname}.local";
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
      warn "skipping sync for $child...\n";
      next;
    }
    else
    {
      system $command;
    }
  }
}
