"""Run a command (or a series, joined by ' && ') on the remote host over SSH.

Credentials are read from env vars so they are never written to disk:
  SADOT_SSH_HOST, SADOT_SSH_PORT, SADOT_SSH_USER, SADOT_SSH_PASS

Usage:
  python deploy/remote.py "whoami && uname -a"
"""
import os
import sys

import paramiko

# Force UTF-8 so Docker progress spinners / Hebrew never crash on a Windows console.
for _stream in (sys.stdout, sys.stderr):
    _rc = getattr(_stream, "reconfigure", None)
    if _rc:
        try:
            _rc(encoding="utf-8", errors="replace")
        except Exception:
            pass


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
    # `remote.py -f script.sh` runs a local script file remotely (avoids shell
    # quoting issues); otherwise the single arg is the command string.
    if len(sys.argv) > 2 and sys.argv[1] == "-f":
        with open(sys.argv[2], "r", encoding="utf-8") as fh:
            cmd = "bash -s <<'SADOT_EOF'\n" + fh.read() + "\nSADOT_EOF\n"
    else:
        cmd = sys.argv[1] if len(sys.argv) > 1 else "echo no-command"
    sys.exit(run(cmd))
