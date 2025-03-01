"""
Caleb Naeger - cmn4315@rit.edu
Foundations of Computer Networks
my_ping.py
python script mimicking the ping utility from UNIX
"""
import argparse
import socket
import struct
import time
import statistics
import os


def calculate_checksum(data):
    checksum = 0

    # Handle odd-length data
    if len(data) % 2 != 0:
        data += b"\x00"

    # Calculate checksum
    for i in range(0, len(data), 2):
        checksum += (data[i] << 8) + data[i+1] # sum the bits
        checksum = (checksum >> 16) + (checksum & 0xffff) # handle overflow


    return (~checksum) & 0xffff # 1s complement


def create_packet(packetsize: int = 40):
    """ Create ICMP packet to be used.
    Packet creation code adapted from https://denizhalil.com/2024/04/06/sending-icmp-packets-with-python-socket-adventure-in-signaling/
    """
    icmp_type = 8  # ICMP echo request
    code = 0
    checksum = 0
    sequence = 1
    payload = b"\x00" * packetsize
    id = os.getpid() & 0xFFFF
    
    header = struct.pack("!BBHHH", icmp_type, code, checksum, id, sequence) # ICMP Header
    
    # Calculate checksum
    checksum = calculate_checksum(header + payload)
    # Update ICMP header with correct checksum
    header = struct.pack("!BBHHH", icmp_type, code, checksum, id, sequence)

    return header + payload


def probe(packet: bytes, ttl: int, ip: str = "8.8.8.8"):
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        # Set the TTL option for the socket
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        sock.settimeout(2)
        resp_time = time.time()
        sock.sendto(packet, (ip, 1))
        try:
            # Receive the response
            response, addr = sock.recvfrom(1024) # receive up to 1024 bytes from the socket
            resp_time = time.time() - resp_time
            
            # Extract ICMP response, skipping IP header
            icmp_header = response[20:28]
            recv_type, recv_code, recv_checksum, recv_id, recv_seq = struct.unpack("!BBHHH", icmp_header)

            if recv_type == 11 or recv_type == 0:  # Echo reply, with id specified in create_packet()
                return False, resp_time, socket.inet_ntoa(response[12:16])
            else:
                return True, -1, ""
        except socket.timeout:
            return True, -1, ""


def main(ip: str, probes: int, n: bool, s: bool, hops: int = 64):
    real_ip = ip
    real_ip = socket.gethostbyname(ip)
    print(real_ip)
    losses = 0
    i = 1
    runtimes = {}
    hop_ips = []
    while i < hops + 1 and (real_ip not in hop_ips):
        losses = 0
        for p in range(probes):
            packet = create_packet()
            loss, runtime, hop_ip = probe(packet, i, real_ip)
            if p == 0:
                print(f" {i} ", end="")
            if not loss and hop_ip != "" and hop_ip not in hop_ips:
                hop_ips.append(hop_ip)
                domain = hop_ip
                try:
                    domain = socket.gethostbyaddr(hop_ip)[0]
                except socket.herror:
                    pass
                print(f" {domain if not n else hop_ip} {f'({hop_ip})' if not n else ''}", end=" ")
            if runtime > 0:
                runtimes[hop_ip] = [runtime]
                print(f" {(runtime*1000):.3f} ms", end="")
            elif loss:
                losses += 1
                print(" *", end="")
        if s:
            print(f" ({int((losses/probes)*100)}% loss)", end="")
        print()
        i += 1

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='A simple ping utility')
    
    # Add arguments
    parser.add_argument('dst', type=str, help='The destination hostname or IP address to ping')
    parser.add_argument('-n', action="store_true", required=False, help='Print hop addresses numerically rather than symbolically and numerically')
    parser.add_argument('-q', type=int, required=False, default=3, help='Number of probes to send per TTL')
    parser.add_argument('-S', action="store_true", required=False, help="Print a summary of unanswered probes per hop")

    args = parser.parse_args()
    main(args.dst, args.q, args.n, args.S)

