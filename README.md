# `my_ping.py` and `my_traceroute.py`

## Description
`my_ping.py` is a simple Python script implementing a subset of the functionality of the Unix ping utility.
Similarly, `my_traceroute.py` is a simple Python script implementing a subset of the functionality of the Unix traceroute utility.

## Getting Started:
### Starting the Virtual Environment
When installing dependencies for any Python project, it is good practice to do so from within a virtual environment.
To create a virtual environment for this project, run `python3 -m venv .venv` from a terminal window. 
To start the venv, on a Unix-based system, run `source .venv/bin/activate` from the same directory.

### Installing Dependencies
This project depends on a few required dependencies for building the documentation. To install these,
run the following command from within the venv:
`pip install -r requirements.txt`

### A Note on Administrator Priveleges
Both scripts in this project use raw ICMP sockets for network communication. As such, the scripts must be run with admin
privileges in order to bypass security restrictions. To do this on a Unix-based system, preface each command with
`sudo`.

## Running my_ping
`my_ping` is a Command Line Application. The general command format is given by:
```
my_ping.py [-h] [-c C] [-i I] [-s S] [-t T] dst
```
For a description of each command line argument, run:
`python3 my_ping.py -h`

## Running my_traceroute
Very similarly to `my_ping`, `my_traceroute` is also Command Line Application. The general command format is given by:
```
my_traceroute.py [-h] [-n] [-q Q] [-S] dst
```
Like `my_ping`, a description of each command line argumentfor `my_traceroute` can be found by runing:
`python3 my_traceroute.py -h`

### Usage Examples:
Below are some example commands, with descriptions of the intended result:

 - `python3 my_ping.py google.com`
	 - ping google.com indefinitely until keyboard interrupt.
 - `python3 my_ping.py amazon.com -c 5`
	 - ping amazon.com 5 times.
 - `python3 my_ping.py google.com -s 30`
	 - ping google.com indefinitely until keyboard interrupt, with 30 byte packets.
 - `python3 my_traceroute.py 8.8.8.8`
	 - Trace the packet path to google's open DNS server at IP 8.8.8.8.
 - `python3 my_traceroute.py 8.8.8.8 -n`
	 - Trace the route to 8.8.8.8, printing a summary of packet losses for each hop.
 - `python3 my_traceroute.py 8.8.8.8 -S`
	 - Trace the route to 8.8.8.8, only printing numerical IP addresses for each hop, rather than including hostnames.



