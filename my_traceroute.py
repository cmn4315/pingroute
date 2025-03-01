"""
my_traceroute.py
A simple implementation of a subset of the Unix traceroute functionality

Caleb Naeger - cmn4315@rit.edu
Foundations of Computer Networks

Usage: my_traceroute.py [-h] [-n] [-q Q] [-S] dst

positional arguments:
  dst         The destination hostname or IP address to trace
              the route for

options:
  -h, --help  show this help message and exit
  -n          Print hop addresses numerically rather than symbolically and numerically
  -q Q        Set the number of probes to send per TTL
  -S          Print a summary of unanswered probes per hop
"""
import argparse
import socket
import struct
import time
import os


def calculate_checksum(data):
    """Calculate the ICMP checksum for a given piece of data and return the calculated checksum.
    :param data: the data for which to calculate the checksum
    """
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
    """ Create ICMP packet to be used and return the created packet.
    Packet creation code adapted from https://denizhalil.com/2024/04/06/sending-icmp-packets-with-python-socket-adventure-in-signaling/
    :param packetsize: the number of data bytes to put in the packet
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
    """Send one traceroute probe to the destination address and return a Tuple(bool, float, str) representing whether
    a response was received, the total elapsed time to send and receive a response, and the source IP of the response
    packet respectively. On a failure, response time will be -1 and the response source IP will be "".
    :param packet: the packet to send for the probe
    :param ttl: the Time To Live to be associated with the packet
    :param ip: the IP address to which to send the packet.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        # Set the TTL option for the socket
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        sock.settimeout(2)
        resp_time = time.time()
        sock.sendto(packet, (ip, 1))
        try:
            # Receive the response
            response, _ = sock.recvfrom(1024) # receive up to 1024 bytes from the socket
            resp_time = time.time() - resp_time
            
            # Extract ICMP response, skipping IP header
            icmp_header = response[20:28]
            recv_type, _, _, _, _ = struct.unpack("!BBHHH", icmp_header)

            if recv_type == 11 or recv_type == 0:  # Echo reply, with id specified in create_packet()
                return False, resp_time, socket.inet_ntoa(response[12:16])
            else:
                return True, -1, ""
        except socket.timeout:
            return True, -1, ""


def get_hostname(ip):
    """Attempt to resolve the hostname for a given ip address, returning the ip address on failure and the hostname on
    success.
    :param ip: the IP address for which to resolve the hostname
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return ip


def main(ip: str, probes: int, n: bool, s: bool, hops: int = 64):
    """Main function for traceroute. This function handles the control flow of the program to send each probe with
    increasing TTL and print the results as they are received.
    :param ip: the dst provided by the user to the program.
    :param probes: the number of probes to send per hop.
    :param n: flag determining whether hostnames will be shown (where possible) for each hop IP.
    :param s: flag denoting whether to show loss summaries for each hop.
    :param hops: maximum number of hops to attempt before prematurely ending the program.
    """
    real_ip = ip
    real_ip = socket.gethostbyname(ip)
    losses = 0
    i = 1
    runtimes = {}
    hop_ips = []
    print(f"traceroute to {ip} ({real_ip}), {hops} hops max, 40 byte packets")
    try:
        while i < hops + 1 and (real_ip not in hop_ips):
            losses = 0
            for p in range(probes):
                packet = create_packet()
                loss, runtime, hop_ip = probe(packet, i, real_ip)
                if p == 0:
                    print(f" {i} ", end="")
                if not loss and hop_ip != "" and hop_ip not in hop_ips:
                    hop_ips.append(hop_ip)
                    domain = get_hostname(hop_ip)
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
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='A simple python traceroute utility')
    
    # Add arguments
    parser.add_argument('dst', type=str, help='The destination hostname or IP address to trace the route for')
    parser.add_argument('-n', action="store_true", required=False, help='Print hop addresses numerically rather than symbolically and numerically')
    parser.add_argument('-q', type=int, required=False, default=3, help='Set the number of probes to send per TTL')
    parser.add_argument('-S', action="store_true", required=False, help="Print a summary of unanswered probes per hop")

    args = parser.parse_args()
    main(args.dst, args.q, args.n, args.S)

