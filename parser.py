#!/usr/bin/env python3
"""
Parse CNU statistics from a text file of networking device logs.

Usage:
    parse_cnu.py <input_file> [-d] [-o <outfile>]

    -d / --debug         Enables printing of "NO MATCH" lines at the end.
    -o / --output FILE   Write all parsed output (and optional debug info) to FILE;
                         otherwise, print to stdout.
"""

import re
import sys
import argparse

# ------------------------------------------------------------------------------
# Regular expression to match the lines containing CNU stats
# ------------------------------------------------------------------------------
line_regex = re.compile(
    r'^\s*'                     # Allow leading spaces
    r'(\d+):'                   # (1) Identifier
    r'([\d\.]+):'               # (2) Linux timestamp
    r'(\w+):'                   # (3) Level for trace
    r'(\w+):'                   # (4) Module
    r'\s*([^\s:]+)\s*:\s*'      # (5) Function (can be more flexible than just (\w+))
    r'(\d+):\s*'                # (6) Source line number
    r'<(\d+):([^>]+)>,<(\d+),([^>]+)>,<(\d+)>\s*'  # (7,8,9,10,11)
    r'<Rx Good/Bad,Percent\s+(\d+)\/\s+(\d+),\s+([\d\.]+)%>'
    r'.*?per channel\s*(.*)$'
)

# Regex for channel sets:
channel_regex = re.compile(
    r'<(\d+):\s*'     # (15) band index
    r'(\d+)\/'        # (16) rxBitsPerSym
    r'(-?\d+)\/'      # (17) rxPower (can be negative)
    r'(\d+)\/'        # (18) rxSNR
    r'(\d+),'         # (19) rxPhyRate
    r'(\d+)\/'        # (20) txBitsPerSym
    r'(\d+)>'         # (21) txPhyRate
)

def parse_cnu_line(line):
    """
    Attempt to parse a single line of the log containing the CNU stats.
    Returns a dictionary of parsed fields if matched; otherwise None.
    """
    m = line_regex.match(line)
    if not m:
        return None

    # Extract top-level groups
    ignored_identifier = m.group(1)   # (unused, but captured)
    linux_timestamp    = m.group(2)
    trace_level        = m.group(3)
    module             = m.group(4)
    function           = m.group(5)
    source_line        = m.group(6)

    moca_port          = m.group(7)
    moca_port_dev      = m.group(8).strip()
    cnu_id             = m.group(9)
    cnu_mac            = m.group(10).strip()
    source_type        = m.group(11)  # "0" => from Micronode, "1" => from CNU

    rx_good            = m.group(12)
    rx_bad             = m.group(13)
    rx_bad_percent     = m.group(14)
    channel_part       = m.group(15)

    # Parse the per-channel data
    channels = channel_regex.findall(channel_part)
    # channels is a list of tuples, e.g. [(bandIndex, rxBits, rxPower, rxSnr, rxPhyRate, txBits, txPhyRate), ...]

    # Construct a dictionary for final output
    result = {
        "timestamp":      linux_timestamp,
        "trace_level":    trace_level,
        "module":         module,
        "function":       function,
        "source_line":    source_line,
        "moca_port":      moca_port,
        "moca_port_dev":  moca_port_dev,
        "cnu_id":         cnu_id,
        "cnu_mac":        cnu_mac,
        "source_type":    source_type,  # "0" => reported by Micronode, "1" => by CNU
        "rx_good":        rx_good,
        "rx_bad":         rx_bad,
        "rx_bad_percent": rx_bad_percent,
        "channels": []
    }

    # Fill in the channel data
    for ch_tuple in channels:
        bandIndex, rxBits, rxPower, rxSnr, rxPhyRate, txBits, txPhyRate = ch_tuple
        ch_data = {
            "bandIndex":     bandIndex,
            "rxBitsPerSym":  rxBits,
            "rxPower":       rxPower,
            "rxSnr":         rxSnr,
            "rxPhyRate":     rxPhyRate,
            "txBitsPerSym":  txBits,
            "txPhyRate":     txPhyRate
        }
        result["channels"].append(ch_data)

    return result


def main():
    parser = argparse.ArgumentParser(description="Parse CNU stats from log file.")
    parser.add_argument("input_file", help="Input log file.")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable printing of lines that do not match regex at the end.")
    parser.add_argument("-o", "--output", metavar="OUTFILE",
                        help="Write parsed output to OUTFILE (default: stdout)")
    args = parser.parse_args()

    # Decide whether to write to a file or stdout
    if args.output:
        out_f = open(args.output, "w", encoding="utf-8")
    else:
        out_f = sys.stdout

    no_match_lines = []
    with open(args.input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            parsed = parse_cnu_line(line)
            if not parsed:
                # Store no-match lines in a list, then print them later if debug is true
                no_match_lines.append(line)
                continue

            # If matched, print the parsed data
            out_f.write("---------------------------------------------------\n")
            out_f.write(f"Timestamp:  {parsed['timestamp']}\n")
            out_f.write(f"Level:      {parsed['trace_level']}\n")
            out_f.write(f"Module:     {parsed['module']}\n")
            out_f.write(f"Function:   {parsed['function']}\n")
            out_f.write(f"Line:       {parsed['source_line']}\n")
            out_f.write(f"MoCA Port:  {parsed['moca_port']} ({parsed['moca_port_dev']})\n")
            out_f.write(f"CNU ID:     {parsed['cnu_id']}\n")
            out_f.write(f"CNU MAC:    {parsed['cnu_mac']}\n")
            source_str = "Micronode" if parsed['source_type'] == "0" else "CNU"
            out_f.write(f"Source:     {source_str}\n")
            out_f.write(f"Rx Good:    {parsed['rx_good']}\n")
            out_f.write(f"Rx Bad:     {parsed['rx_bad']}\n")
            out_f.write(f"Rx % Bad:   {parsed['rx_bad_percent']}\n")
            out_f.write("Channel Stats:\n")
            for ch in parsed['channels']:
                out_f.write(
                    f"  BandIndex: {ch['bandIndex']} | "
                    f"RX bits/sym: {ch['rxBitsPerSym']} | "
                    f"Power: {ch['rxPower']} dBm? | "
                    f"SNR: {ch['rxSnr']} dB | "
                    f"RX PHY: {ch['rxPhyRate']} Mbps | "
                    f"TX bits/sym: {ch['txBitsPerSym']} | "
                    f"TX PHY: {ch['txPhyRate']} Mbps\n"
                )
            out_f.write("---------------------------------------------------\n")

    # After reading all lines, optionally print no-match lines
    if args.debug and no_match_lines:
        out_f.write("\n=== DEBUG MODE: NO MATCH LINES ===\n")
        for nm in no_match_lines:
            out_f.write(f"NO MATCH: {nm}\n")

    # If an output file was opened, close it
    if args.output:
        out_f.close()


if __name__ == "__main__":
    main()
