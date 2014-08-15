#!/bin/bash
./abundance_matrix.pl > abundance_matrix.out 
./access_control.pl > access_control.out 
./download_metagenome_sequences.pl mgm4440442.5 > download_metagenome_sequences.out 
./extract_sequences.pl > extract_sequences.out 
./firmicutes_annotations.pl > firmicutes_annotations.out 
./gene_abundance_info.pl > gene_abundance_info.out 
./get_cog_abundance.pl > get_cog_abundance.out 
./retrieve_uniprot_for_sequence.pl > retrieve_uniprot_for_sequence.out 
./species_abundance_biom.pl mgm4440026.3 GenBank > species_abundance_biom.out 
