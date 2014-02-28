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
        token => $h{'auth'}
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
	
	if (defined($self->token) && $self->token ne '') {
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

sub pretty {
	my ($self, $hash) = @_;
	
	return $self->json->pretty->encode ($hash);
}


sub request {
	#print 'request: '.join(',',@_)."\n";
	my ($self, $version, $method, $resource, $query, $headers, $returntype) = @_;
	
	
	unless (defined $returntype) {
		$returntype = 'json';
	}
	
	unless ($returntype eq 'json' || $returntype eq 'stream') {
		die "return type \"$returntype\" unknown";
	}
	
	my $my_url = $self->create_url($version, $resource, (defined($query)?%$query:()));
	
	print "url: $my_url\n";
	
	
	
	my @method_args = ($my_url);
	
	if (defined $headers) {
		push(@method_args, %$headers);
	}
	
	#print 'method_args: '.join(',', @method_args)."\n";
	
	my $response_content = undef;
    my $response_object = undef;
	
    eval {
		
       
		
        if ($method eq 'GET') {
			$response_object = $self->agent->get(@method_args );
		} elsif ($method eq 'DELETE') {
			$response_object = $self->agent->delete(@method_args );
		} elsif ($method eq 'POST') {
			$response_object = $self->agent->post(@method_args );
		} else {
			die "not implemented yet";
		}
		
		#print "content: ".$response_object->content."\n";
		
		if ($returntype eq 'json') {
			$response_content = $self->json->decode( $response_object->content );
		} else {
			$response_content = {}; # fake it
		}
        
    };
    
	if ($@ || (! ref($response_content))) {
        print STDERR "[error] unable to connect to MG-RAST API ".$self->api_server."\n";
        return undef;
    } elsif (exists($response_content->{error}) && $response_content->{error}) {
        print STDERR "[error] unable to send $method request to MG-RAST API: ".$response_content->{error}[0]."\n";
		return undef;
    } else {
		#print "response_content: $response_content\n";
		#my $jhash = $self->json->decode( $response_content );
		
        #return $jhash;
		if ($returntype eq 'json') {
			return $response_content;
		} else {
			return $response_object->content;
		}
    }
	
}


sub status {
	my ($self, $id) = @_;
	
	unless (defined $id) {
		die;
	}
	#my $api_url = $self->create_url(1, 'status/'.$id);
	my $status_obj = $self->get('1', 'status/'.$id );
	
	if (defined($status_obj) && $status_obj->{'status'} eq 'done') {
		return $status_obj->{'data'};
	}
	return undef;
}

sub get {
	my ($self, $version, $resource, $query, $headers) = @_;
	
	return $self->request($version, 'GET', $resource, $query, $headers);

	
}



sub download {
	my ($self, $path, $mg_id, %hash) = @_;
	
	my $api_url = create_url($self, 1, 'download/'.$mg_id, %hash);
		
	print "$api_url\n";
	
    my $content = undef;
    eval {
        my $get = undef;
		
		
		if (-e $path) {
			die "error: file \"$path\" already exists.";
		}
		
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

