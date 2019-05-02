#!/usr/bin/env python3
import sys
import json
import multiprocessing
import time
from collections import defaultdict


import param
from util import *


def process(sample_pileup_path):
    tsprint(f"{sample_pileup_path}: Processing sample pileup path")
    sample_name = chomp(sample_pileup_path, ".pileup")
    paramstr = f"gcb{param.MIN_GENOME_COVERED_BASES}.dp{param.MIN_DEPTH}.sr{param.MAX_SITE_RATIO}"
    output_path_site_id = f"{sample_name}.sites.{paramstr}.tsv"
    output_path_contig_stats = f"{sample_name}.contig_stats.tsv"
    output_path_genome_stats = f"{sample_name}.genome_stats.tsv"
    t_start = time.time()

    sites_count = 0
    contig_depth = defaultdict(int)
    genome_covered_bases = defaultdict(int)
    genome_depth = defaultdict(int)
    contig_covered_bases  = defaultdict(int)
    table_iterator = parse_table(tsv_rows(sample_pileup_path), param.sample_pileup_schema)
    columns = next(table_iterator)
    # Get integer keys for columns
    c_ref_id = columns["ref_id"]
    c_depth = columns["depth"]
    c_ref_pos = columns["ref_pos"]
    c_ref_allele = columns["ref_allele"]
    c_A = columns["A"]
    c_C = columns["C"]
    c_G = columns["G"]
    c_T = columns["T"]
    for line, row in enumerate(table_iterator):
        if line % (1000*1000) == 0:
            tsprint(f"{sample_pileup_path}: Processing {line}.")
        if line == param.MAX_LINES:
            break
        contig_id = row[c_ref_id]
        row_depth = row[c_depth]
        # Add derived columns
        site_id = contig_id + "|" + str(row[c_ref_pos]) + "|" + str(row[c_ref_allele])
        genome_id = contig_id.split("_", 1)[0]
        # Index and aggregate rows
        sites_count += 1
        contig_depth[contig_id] += row_depth
        contig_covered_bases[contig_id] += 1
        genome_covered_bases[genome_id] += 1
        genome_depth[genome_id] += row_depth
        if line < 10:
            tsprint(("\n" + json.dumps(dict(zip(columns.keys(), row)), indent=4)).replace("\n", "\n" + sample_pileup_path + ": "))
    # print_top(contig_depth)
    # print_top(contig_covered_bases)
    # print_top(genome_covered_bases)
    with open(output_path_contig_stats, "w") as o2:
        o2.write("contig_id\tgenome_id\tcontig_total_depth\tcontig_covered_bases\n")
        for contig_id, contig_total_depth in contig_depth.items():
            covered_bases = contig_covered_bases[contig_id]
            genome_id = contig_id.split("_", 1)[0]
            o2.write(f"{contig_id}\t{genome_id}\t{contig_total_depth}\t{covered_bases}\n")
    with open(output_path_genome_stats, "w") as o3:
        o3.write("genome_id\tgenome_total_depth\tgenome_covered_bases\n")
        for genome_id, genome_total_depth in genome_depth.items():
            covered_bases = genome_covered_bases[genome_id]
            o3.write(f"{genome_id}\t{genome_total_depth}\t{covered_bases}\n")
    t_end = time.time()
    # tsprint(f"{sample_pileup_path}: Output {output_sites} sites passing filters, out of {len(sites)} total sites.  Pass rate: {output_sites/len(sites)*100:3.1f} percent.")
    tsprint(f"{sample_pileup_path}: Run time {t_end - t_start} seconds, or {sites_count/(t_end - t_start):.1f} sites per second.")
    return "it worked"


if __name__ == "__main__":
    assert len(sys.argv) > 1
    mp = multiprocessing.Pool((multiprocessing.cpu_count() + 1) // 2)
    status = mp.map(process, sys.argv[1:])
    assert all(s == "it worked" for s in status)
