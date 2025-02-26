"""
Caleb Naeger - cmn4315@rit.edu
Foundations of Computer Networks
my_ping.py
python script mimicking the ping utility from UNIX
"""
import argparse
import socket
import struct


def calculate_checksum(data):
    checksum = 0

    # Handle odd-length data
    if len(data) % 2 != 0:
        data += b"\x00"

        # Calculate checksum
    for i in range(0, len(data), 2):
        checksum += (data[i] << 8) + data[i+1]

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += checksum >> 16

    return (~checksum) & 0xffff


def create_packet(packetsize: int = 56):
    """ Create ICMP packet to be used for the ping.
    Packet creation code adapted from https://denizhalil.com/2024/04/06/sending-icmp-packets-with-python-socket-adventure-in-signaling/
    """
    icmp_type = 8  # ICMP echo request
    code = 0
    checksum = 0
    sequence = 1
    payload = b"\x00" * packetsize
    id = 8675309
    
    header = struct.pack("!BBHHH", icmp_type, code, checksum, id, sequence) # ICMP Header
    
    # Calculate checksum
    checksum = calculate_checksum(header + payload)
    # Update ICMP header with correct checksum
    header = struct.pack("!BBHHH", icmp_type, code, socket.htons(checksum), id, sequence)

    return header + payload


def main():
    pass


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='A simple ping utility')
    
    # Add arguments
    parser.add_argument('-c', type=int, required=False, help='The name of the file to read.')
    parser.add_argument('-i', type=int, required=False, help='The number of packets to analyze.')
    parser.add_argument('-s', type=int, required=False, help="Apply a filter to the analyzer, by hostname.")
    parser.add_argument('-t', type=int, required=False, help="Apply a filter to the analyzer, by port number.")

    main()

