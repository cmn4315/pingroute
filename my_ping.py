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


def create_packet(packetsize: int = 56):
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


def ping(packet: bytes, ip: str = "8.8.8.8"):
    """Send a ping to a given IP, timing the response time. Returns a Tuple(bool, float) representing whether the
    response was lost and the total time in seconds for the ping. On loss, response time will be -1.
    :param packet: the packet to send.
    :param ip: the IP address to which to send the packet.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        sock.settimeout(10)
        resp_time = time.time()
        sock.sendto(packet, (ip, 1))
        try:
            # Receive the response
            response, addr = sock.recvfrom(1024) # receive up to 1024 bytes from the socket
            resp_time = time.time() - resp_time
            
            # Extract ICMP response, skipping IP header
            icmp_header = response[20:28]
            recv_type, recv_code, recv_checksum, recv_id, recv_seq = struct.unpack("!BBHHH", icmp_header)

            if recv_type == 0 and recv_id == os.getpid() & 0xFFFF:  # Echo reply, with id specified in create_packet()
                print(f"{len(response[20:])} bytes from {ip}: icmp_seq={recv_seq}, ttl={int.from_bytes(response[8:9])} time={(resp_time*1000):.3f} ms")
                return False, resp_time*1000
            else:
                print("Unexpected ICMP Packet received")
                return True, -1
        except socket.timeout:
            print("Request timed out")
            return True, -1


def main(ip: str, timeout: int, packetsize: int, count: int, wait: int):
    """The main function for my_ping.py, controlling the sending of pings, aggregation and output of results, and
    timeouts/end conditions.
    :param ip: the dst provided by the user.
    :param timeout: total time in seconds for which the program should run.
    :param packetsize: the number of data bytes to add to the ping packet.
    :param count: the total number of pings to send.
    :param wait: time in seconds to wait between each ping.
    """
    real_ip = ip
    real_ip = socket.gethostbyname(ip)
    print(f"PING {ip} ({real_ip}): {packetsize} data bytes")
    i = 0
    losses = 0
    runtimes = []
    start_time = time.time()
    try:
        while (timeout < 0 or time.time() - start_time < timeout) and (count < 0 or i < count):
            packet = create_packet(packetsize)
            loss, runtime = ping(packet, real_ip)
            if (runtime > 0):
                runtimes.append(runtime)
            if loss:
                losses += 1
            i += 1
            time.sleep(wait)
    except KeyboardInterrupt:
        pass
    print()
    print(f"--- {ip} ping statistics ---")
    print(f"{i} packets transmitted, {i-losses} packets received, {(losses/i)*100}% packet loss")
    print(f"round-trip min/avg/max/stddev = {min(runtimes):.3f}/{(sum(runtimes)/len(runtimes)):.3f}/{max(runtimes):.3f}/{statistics.stdev(runtimes):.3f}ms")


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='A simple ping utility')
    
    # Add arguments
    parser.add_argument('dst', type=str, help='The destination hostname or IP address to ping')
    parser.add_argument('-c', type=int, required=False, default=-1, help='The number of ping packets to send. Will send indefinitely if not provided')
    parser.add_argument('-i', type=int, required=False, default=1, help='The interval to wait between each packet, defaults to 1s')
    parser.add_argument('-s', type=int, required=False, default=56, help="The payload size in bytes, defaults to 56 bytes.")
    parser.add_argument('-t', type=int, required=False, default=-1, help="Timeout duration for a run. Will run until interrupt if not provided")

    args = parser.parse_args()
    main(args.dst, args.t, args.s, args.c, args.i)

