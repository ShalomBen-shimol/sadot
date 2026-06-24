"""Run a command (or a series, joined by ' && ') on the remote host over SSH.

Credentials are read from env vars so they are never written to disk:
  SADOT_SSH_HOST, SADOT_SSH_PORT, SADOT_SSH_USER, SADOT_SSH_PASS

Usage:
  python deploy/remote.py "whoami && uname -a"
"""
import os
import sys

import paramiko


def run(command: str) -> int:
    host = os.environ["SADOT_SSH_HOST"]
    port = int(os.environ.get("SADOT_SSH_PORT", "22"))
    user = os.environ["SADOT_SSH_USER"]
    password = os.environ["SADOT_SSH_PASS"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password, timeout=20)

    # Request a shell that loads the login environment (docker path, etc.).
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    client.close()

    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return code


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "echo no-command"
    sys.exit(run(cmd))
