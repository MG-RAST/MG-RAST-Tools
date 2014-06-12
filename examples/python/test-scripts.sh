#!/bin/bash
./abundance_matrix.py  > abundance_matrix.out
./compare_annotations.py > compare_annotations.out
./download_metagenome_sequences.py MGR4440613.3 > download_metagenome_sequences.out
./sequences_with_annotations.py > sequences_with_annotations.out
