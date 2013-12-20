package mglib;

use strict;
use warnings;
no warnings('once');

use File::Basename;
use Data::Dumper;
use JSON;
use LWP::UserAgent;
use URI::Escape;

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


#multiple values for the same key can given as array ref: "key => [value1, value2]"
#example: (1, 'matrix/function', 'id' =>['mgm4447943.3', 'mgm4447192.3'])
sub create_url {
	my ($self, $version, $resource, %query) = @_;
	
	my $api_url = $self->api_server . "/$version/$resource";
	
	if (defined $self->token) {
		$query{'auth'}=$self->token;
	}
	
	#build query string:
	my $query_string = "";
	
	foreach my $key (keys %query) {
		my $value = $query{$key};
		
		my @values=();
		if (ref($value) eq 'ARRAY') {
			@values=@$value;
		} else {
			@values=($value);
		}
		
		foreach my $value (@values) {
			if ((length($query_string) != 0)) {
				$query_string .= '&';
			}
			$query_string .= $key.'='.$value;
		}
	}
	
	
	if (length($query_string) != 0) {
		$api_url .= uri_escape('?'.$query_string);
	}
	
	
	return $api_url;
}


#get_hash example:
#my $biom = $mg->get_hash(1, 'matrix/function' ,
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
	my ($self, $version, $resource, %hash) = @_;
	
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
	my ($self, $path, $mg_id, %hash) = @_;
	
	my $api_url = create_url($self, 1, 'download/'.$mg_id, %hash);
		
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

