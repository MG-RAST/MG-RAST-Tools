package mglib;

use strict;
use warnings;
no warnings('once');

use File::Basename;
use Data::Dumper;
use JSON;
use LWP::UserAgent;

1;


sub new {
    my ($class, %h) = @_;
    
	
    my $agent = LWP::UserAgent->new;
    my $json = JSON->new;
    $json = $json->utf8();
    $json->max_size(0);
    $json->allow_nonref;
    
    my $self = {
        json => $json,
        agent => $agent,
        api_server => $h{api_server} || 'http://api.metagenomics.anl.gov',
        token => $h{token} || ''
    };
   

    bless $self, $class;
    return $self;
}

sub json {
    my ($self) = @_;
    return $self->{json};
}
sub agent {
    my ($self) = @_;
    return $self->{agent};
}
sub api_server {
    my ($self) = @_;
    return $self->{api_server};
}
sub token {
    my ($self) = @_;
    return $self->{token};
}



sub create_url {
	my ($self, $version, $resource, $request, %hash) = @_;
	
	my $api_url = $self->api_server . "/$version/$resource/$request";
	
	if (defined $self->token) {
		$hash{'auth'}=$self->token;
	}
	
	
	my $first=1;
	foreach my $key (keys %hash) {
		my $value = $hash{$key};
		
		my @values=();
		if (ref($value) eq 'ARRAY') {
			@values=@$value;
		} else {
			@values=($value);
		}
		
		foreach my $value (@values) {
			if ($first==1) {
				$api_url .= '?';
				$first=0;
			} else {
				$api_url .= '&';
			}
			$api_url .= $key.'='.$value;
		}
	}
	
	return $api_url;
}


#get_hash example:
#my $biom = $mg->get_hash(1, 'matrix', 'function' ,
#'id' =>['mgm4447943.3', 'mgm4447192.3', 'mgm4447103.3', 'mgm4447102.3', 'mgm4447101.3', 'mgm4447971.3', 'mgm4447970.3', 'mgm4447903.3'],
#'result_type'=>'abundance',
#'source'=> 'COG',
#'evalue'=>10
#);
sub get_hash {
	my ($self) = @_;
	
	my $content = get(@_) || return undef;
		
	my $hash = $self->json->decode( $content );
	
	return $hash;
}

sub get {
	my ($self, $version, $resource, $request, %hash) = @_;
	
	my $api_url = create_url(@_);
	
	print "$api_url\n";
	
    my $content = undef;
    eval {
        my $get = undef;
        
        $get = $self->agent->get(	$api_url );
       
        $content = $get->content;
    };
    
    if ($@) {
        print STDERR "[error] unable to connect to API ".$api_url ."\n";
        return undef;
    } elsif (ref($content) && exists($content->{error}) && $content->{error}) {
        print STDERR "[error] unable to GET from API: ".$content->{error}[0]."\n";
		
        return undef;
    } else {
        return $content;
    }

	
}

sub download {
	my ($self, $path, $request, %hash) = @_;
	
	my $api_url = create_url($self, 1, 'download', $request, %hash);
		
	print "$api_url\n";
	
    my $content = undef;
    eval {
        my $get = undef;
        open(OUTF, ">$path") || die "Can not open file $path: $!\n";
		
		
        
        $get = $self->agent->get(	$api_url ,
									':read_size_hint' => 8192,
									':content_cb'     => sub{ my ($chunk) = @_; print OUTF $chunk; } );
        close OUTF;
        $content = $get->content;
    };
    
    if ($@) {
        print STDERR "[error] unable to connect to API ".$api_url ."\n";
		unlink($path);
        return undef;
    } elsif (ref($content) && exists($content->{error}) && $content->{error}) {
        print STDERR "[error] unable to GET file from API: ".$content->{error}[0]."\n";
		unlink($path);
        return undef;
    } elsif (! -s $path) {
        print STDERR "[error] unable to download to $path: $!\n";
		unlink($path);
        return undef;
    } else {
        return $path;
    }
	
}

