from Bio import SeqIO
import pysam

#import plotly.express as px
import plotly.graph_objects as go

from math import log
import os.path
import sys

if __name__ == "__main__":

    if(len(sys.argv) < 2):
        sys.exit(1)

    dataset_sizes = [0.369211314,
                     0.402193959,
                     0.363206853,
                     0.183602223,
                     0.226892212,
                     0.414064482,
                     16.506755978,
                     153.718152889]

    #Get aclame, iceberg, and plasmid finder lengths for coverage
    gene_lengths = {}
    aclame_reference_fasta_filename = "/home/noyes046/shared/databases/aclame/aclame_genes_all_0.4.fasta"
    iceberg_reference_fasta_filename = "/home/noyes046/shared/databases/ice_berg/ICEberg_seq.fasta"
    pf_reference_fasta_filename = "/home/noyes046/shared/databases/plasmid_finder/plasmids_combined.fsa"

    for rec in SeqIO.parse(aclame_reference_fasta_filename, "fasta"):
        gene_lengths[rec.name] = len(rec.seq)

    for rec in SeqIO.parse(iceberg_reference_fasta_filename, "fasta"):
        gene_lengths[rec.name] = len(rec.seq)

    for rec in SeqIO.parse(pf_reference_fasta_filename, "fasta"):
        gene_lengths[rec.name] = len(rec.seq)

    #Input is text file with list of sam files
    sam_files = []
    with open(sys.argv[1], 'r') as input_handle:
        for line in input_handle:
            sam_files.append(pysam.AlignmentFile(line[:-1], 'r'))

    absolute_abundances = {}
    for sam_file in sam_files:
        sample_absolute_abundance = {}
        #Iterate through every read. Accumulate number of reads while recording read length
        for read in sam_file.fetch():
            if read.is_unmapped or read.is_secondary or read.is_supplementary:
                continue
                
            #check coverage
            if (float(read.reference_length) / gene_lengths[read.reference_name]) > 0.5:
                if not read.reference_name in sample_absolute_abundance:
                    sample_absolute_abundance[read.reference_name] = 0
                sample_absolute_abundance[read.reference_name] += 1

        filename = str(sam_file.filename, 'utf-8')
        sam_file.close()
        absolute_abundances[filename] = sample_absolute_abundance

    relative_abundances = {}
    i = 0
    #Convert absolute abundances to relative abundance
    for filename in absolute_abundances:
        sample_relative_abundance = {}
        for gene_name in absolute_abundances[filename]:
            sample_relative_abundance[gene_name] = log(absolute_abundances[filename][gene_name] / float( gene_lengths[gene_name] * dataset_sizes[i]))

        relative_abundances[filename] = sample_relative_abundance
        i +=1

    fig = go.Figure()
    for filename in relative_abundances:
        if "MOCK" in filename:
            fig.add_trace(go.Violin(y=list(relative_abundances[filename].values()),
                                    box_visible=True,
                                    name=os.path.basename(filename)[0:8],
                                    points="all"))
        elif "ERR" in filename:
            fig.add_trace(go.Violin(y=list(relative_abundances[filename].values()),
                                    box_visible=True,
                                    name=os.path.basename(filename)[0:12],
                                    points="all"))
        else:
            fig.add_trace(go.Violin(y=list(relative_abundances[filename].values()),
                                    box_visible=True,
                                    name=os.path.basename(filename)[0:3],
                                    points="all"))

    fig.update_xaxes(title_text="Samples")
    fig.update_yaxes(title_text="Log Relative Abundance")
    fig.write_image("mobilome_violin.png")

    sys.exit(0)
