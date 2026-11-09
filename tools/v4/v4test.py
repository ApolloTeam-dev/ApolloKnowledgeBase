#!/usr/bin/env python3
"""Build AKB tests with ApolloCrossDev, run them on a V4, collect the results.

  v4test.py run [--rounds N] [--shot] [--record] [--power-cycle] TEST...
  v4test.py build [TEST...]        build only (all tests when none given; CI)
  v4test.py alive
  v4test.py shot FILE.png
  v4test.py record FILE.mp4 SECONDS
  v4test.py power-cycle

A TEST is a folder under tools/v4/tests/ (or a path to one) with a test.c
and optional .s files. The protocol a test prints is described in
tools/v4/tests/akbtest.h; v4test.py fails a test that prints a FAIL line, does
not print AKB-DONE, or does not finish within its timeout.

Markers in test.c:
  v4:variant NAME FLAGS   build and run the test once per variant, with these
                          GCC flags; -l flags go after the objects (default:
                          one variant, "default", with the ApolloCrossDev
                          template flags)
  v4:timeout SECONDS      time limit for one run (default 60)

The variants run alternately, ROUNDS times (guides/benchmark-method.md).
Results go to build/v4/<UTC time>/: per run the program's output, the serial
log and result.json, and summary.json for the whole session, with the core
number from `ApolloControl CO`.

The machine is set with environment variables:
  AKB_V4_HOST     V4 address (ApolloExplorerSrv must run on it)   required
  AKB_V4_PLUG     Tasmota plug that powers the V4, for power-cycle optional
  AKB_V4_SERIAL   serial port of the V4 debug output, or "none"   default: first /dev/cu.usbserial*
  AKB_V4_CAPTURE  ffmpeg avfoundation video device of the HDMI capture  default: "USB Video"
  PREFIX          ApolloCrossDev compiler folder   default: from skills/apollo-build/scripts/find-acd.sh
Needs ash and acp (ApolloExplorer), and ffmpeg for shot and record.
"""
import argparse
import datetime
import glob
import json
import os
import re
import select
import subprocess
import sys
import termios
import threading
import time
import urllib.request

KB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS = os.path.join(KB, "tools", "v4", "tests")
DEFAULT_OPTS = "-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer"
AOPTS = "-m68080 -m68881 -opt-speed"
REMOTE_DIR = "RAM:akb"
ENV = dict(os.environ, LC_ALL="en_US.UTF-8")


def host():
    h = os.environ.get("AKB_V4_HOST")
    if not h:
        sys.exit("set AKB_V4_HOST to the V4's address")
    return h


# --- the V4 over the network ------------------------------------------------

def ash(cmd, timeout=15):
    """Run an AmigaDOS command with ash. Returns (output, finished)."""
    try:
        p = subprocess.run(["ash", host(), cmd], stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=ENV, timeout=timeout)
        out, done = p.stdout, True
    except subprocess.TimeoutExpired as e:
        out, done = e.stdout or b"", False
    lines = out.decode("latin-1").replace("\r", "").split("\n")
    lines = [l for l in lines
             if not l.startswith("Connecting to ") and l != "Connected."]
    return "\n".join(lines).strip("\n"), done


def alive():
    out, done = ash("C:Echo up", timeout=10)
    return done and out.strip() == "up"


def upload(path, remote_dir):
    h = host()
    vol, _, rest = remote_dir.partition(":")
    dest = "%s:%s/%s/" % (h, vol, rest) if rest else "%s:%s/" % (h, vol)
    p = subprocess.run(["acp", path, dest], stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=ENV, timeout=60)
    if p.returncode != 0:
        sys.exit("acp failed: %s" % p.stdout.decode("latin-1"))


def power_cycle():
    plug = os.environ.get("AKB_V4_PLUG")
    if not plug:
        print("AKB_V4_PLUG is not set: cannot power-cycle")
        return False
    for cmd in ("Power%20Off", "Power%20On"):
        urllib.request.urlopen("http://%s/cm?cmnd=%s" % (plug, cmd), timeout=5).read()
        if cmd.endswith("Off"):
            time.sleep(10)
    for i in range(24):
        time.sleep(5)
        if alive():
            print("V4 up after %d s" % ((i + 1) * 5))
            return True
    print("V4 not answering 120 s after power-on")
    return False


# --- serial log and video ----------------------------------------------------

class SerialLog(threading.Thread):
    """Log the V4's serial output (115200 8N1, no flow control) while a test runs."""

    def __init__(self, path):
        super().__init__(daemon=True)
        port = os.environ.get("AKB_V4_SERIAL")
        if port is None:
            port = (sorted(glob.glob("/dev/cu.usbserial*")) or ["none"])[0]
        self.port, self.path, self.stop = port, path, threading.Event()

    def run(self):
        if self.port == "none":
            return
        fd = os.open(self.port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        cc = termios.tcgetattr(fd)[6]
        cc[termios.VMIN] = cc[termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW,
                          [0, 0, termios.CS8 | termios.CREAD | termios.CLOCAL, 0,
                           termios.B115200, termios.B115200, cc])
        termios.tcflush(fd, termios.TCIFLUSH)
        with open(self.path, "wb") as out:
            while not self.stop.is_set():
                if select.select([fd], [], [], 0.2)[0]:
                    data = os.read(fd, 4096)
                    if data:
                        out.write(data)
                        out.flush()
        os.close(fd)


def ffmpeg_input():
    dev = os.environ.get("AKB_V4_CAPTURE", "USB Video")
    return ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "avfoundation", "-pixel_format", "uyvy422", "-framerate", "30",
            "-i", dev + ":none"]


def shot(path):
    subprocess.run(ffmpeg_input() + ["-frames:v", "1", path],
                   stdin=subprocess.DEVNULL, timeout=20, check=True)


def start_recording(path, seconds):
    return subprocess.Popen(ffmpeg_input() + ["-t", str(seconds), "-c:v", "libx264",
                                              "-preset", "veryfast", "-pix_fmt", "yuv420p", path],
                            stdin=subprocess.PIPE)


def stop_recording(p):
    try:
        p.communicate(b"q", timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()


# --- building ----------------------------------------------------------------

def acd_prefix():
    if os.environ.get("PREFIX"):
        return os.environ["PREFIX"]
    out = subprocess.run(["sh", os.path.join(KB, "skills/apollo-build/scripts/find-acd.sh"),
                          "--offline"], stdout=subprocess.PIPE, text=True).stdout
    m = re.search(r"^PREFIX=(.+)$", out, re.M)
    if not m:
        sys.exit("ApolloCrossDev not found: set PREFIX\n" + out)
    return m.group(1)


def markers(src):
    text = open(src).read()
    variants = re.findall(r"v4:variant[ \t]+(\S+)[ \t]+(.+?)[ \t]*$", text, re.M)
    t = re.search(r"v4:timeout[ \t]+(\d+)", text)
    return variants or [("default", DEFAULT_OPTS)], int(t.group(1)) if t else 60


def build(test_dir, name, variant, opts, out_dir):
    prefix = acd_prefix()
    tgt = os.path.join(prefix, "m68k-amigaos")
    incl = ["-I" + os.path.join(tgt, d) for d in
            ("libnix/include", "sys-include", "ndk32-include/Include_H")]
    objs = []
    for s in sorted(glob.glob(os.path.join(test_dir, "*.s"))):
        o = os.path.join(out_dir, os.path.basename(s)[:-2] + ".o")
        subprocess.run([os.path.join(prefix, "bin/vasmm68k_mot"), "-quiet"] + AOPTS.split()
                       + ["-I" + os.path.join(tgt, "DevPac/Include"), "-Fhunk", "-o", o, s],
                       check=True)
        objs.append(o)
    exe = os.path.join(out_dir, "akb-%s-%s" % (name, variant))
    flags = [f for f in opts.split() if not f.startswith("-l")]
    libs = [f for f in opts.split() if f.startswith("-l")]  # after the objects
    subprocess.run([os.path.join(prefix, "bin/m68k-amigaos-gcc"), "-noixemul"] + flags
                   + ["-Wall", "-Werror"] + incl
                   + [os.path.join(test_dir, "test.c")] + objs + libs + ["-o", exe], check=True)
    return exe


# --- running -------------------------------------------------------------------

def parse(output):
    lines = output.split("\n")
    fails = [l for l in lines if l.startswith("FAIL ")]
    values = {}
    for l in lines:
        m = re.match(r"VALUE (\S+) (\d+) (.*)$", l)
        if m:
            values[m.group(1)] = [int(m.group(2)), m.group(3)]
    done = "AKB-DONE" in lines
    return {"passed": sum(l.startswith("PASS ") for l in lines),
            "failed": fails, "values": values, "done": done,
            "ok": done and not fails}


def run_one(exe, timeout, run_dir, opts, args):
    os.makedirs(run_dir, exist_ok=True)
    serial = SerialLog(os.path.join(run_dir, "serial.log"))
    serial.start()
    rec = None
    if args.record:
        rec = start_recording(os.path.join(run_dir, "video.mp4"), timeout + 5)
        time.sleep(2)                               # ffmpeg needs time to start
    started = time.time()
    output, finished = ash("%s/%s" % (REMOTE_DIR, os.path.basename(exe)), timeout)
    seconds = round(time.time() - started, 1)
    if rec:
        stop_recording(rec)
    if args.shot:
        try:
            shot(os.path.join(run_dir, "screen.png"))
        except Exception as e:                      # a missing picture is not a test failure
            print("  screenshot failed: %s" % e)
    time.sleep(0.5)
    serial.stop.set()
    serial.join(2)
    open(os.path.join(run_dir, "output.txt"), "w").write(output + "\n")
    res = parse(output)
    res.update(finished=finished, seconds=seconds, opts=opts, serial_port=serial.port)
    if not finished:
        res["ok"] = False
        res["failed"].append("FAIL timeout no answer within %d s" % timeout)
        res["alive_after"] = alive()
        if not res["alive_after"] and args.power_cycle:
            res["power_cycled"] = power_cycle()
    json.dump(res, open(os.path.join(run_dir, "result.json"), "w"), indent=2)
    return res


def test_dir(t):
    d = t if os.path.isdir(t) else os.path.join(TESTS, t)
    if not os.path.isfile(os.path.join(d, "test.c")):
        sys.exit("no test.c in %s" % d)
    return d, os.path.basename(os.path.normpath(d))


def cmd_build(args):
    tests = args.tests or sorted(n for n in os.listdir(TESTS)
                                 if os.path.isfile(os.path.join(TESTS, n, "test.c")))
    for t in tests:
        d, name = test_dir(t)
        for v, opts in markers(os.path.join(d, "test.c"))[0]:
            out_dir = os.path.join(KB, "build", "v4", "build", name, v)
            os.makedirs(out_dir, exist_ok=True)
            print("built " + os.path.relpath(build(d, name, v, opts, out_dir), KB))
    return 0


def cmd_run(args):
    if not alive():
        sys.exit("V4 at %s does not answer (is ApolloExplorerSrv running?)" % host())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    session = os.path.join(KB, "build", "v4", stamp)
    version, _ = ash("C:Version")
    core, _ = ash("ApolloControl CO")               # core number, e.g. 12556
    core = core.strip() if core.strip().isdigit() else None
    print("V4 at %s: core %s, %s" % (host(), core or "unknown", version))
    summary = {"time": stamp, "core": core, "host_version": version, "runs": []}
    ash("C:MakeDir %s" % REMOTE_DIR)                # fails harmlessly when it exists

    plan = []
    for t in args.tests:
        d, name = test_dir(t)
        variants, timeout = markers(os.path.join(d, "test.c"))
        exes = {}
        for v, opts in variants:
            out_dir = os.path.join(session, "build", name, v)
            os.makedirs(out_dir, exist_ok=True)
            exes[v] = (build(d, name, v, opts, out_dir), opts)
            upload(exes[v][0], REMOTE_DIR)
        plan.append((name, variants, exes, timeout))

    all_ok = True
    for name, variants, exes, timeout in plan:
        for r in range(args.rounds):
            for v, _ in variants:
                exe, opts = exes[v]
                run_dir = os.path.join(session, "%s-%s-%d" % (name, v, r + 1))
                res = run_one(exe, timeout, run_dir, opts, args)
                all_ok &= res["ok"]
                summary["runs"].append(dict(test=name, variant=v, round=r + 1, **res))
                vals = " ".join("%s=%d" % (k, x[0]) for k, x in res["values"].items())
                print("%-4s %s/%s round %d: %d passed, %d failed  %s" %
                      ("ok" if res["ok"] else "FAIL", name, v, r + 1,
                       res["passed"], len(res["failed"]), vals))
                for f in res["failed"][:5]:
                    print("     " + f)
                if not res["finished"] and not res.get("alive_after") \
                        and not res.get("power_cycled"):
                    json.dump(summary, open(os.path.join(session, "summary.json"), "w"), indent=2)
                    sys.exit("V4 hung; results so far in %s" % session)
    json.dump(summary, open(os.path.join(session, "summary.json"), "w"), indent=2)
    print("results: %s" % session)
    return 0 if all_ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("tests", nargs="+")
    r.add_argument("--rounds", type=int, default=1)
    r.add_argument("--shot", action="store_true", help="screenshot after each run")
    r.add_argument("--record", action="store_true", help="record video of each run")
    r.add_argument("--power-cycle", action="store_true", help="power-cycle a hung V4")
    b = sub.add_parser("build")
    b.add_argument("tests", nargs="*")
    sub.add_parser("alive")
    s = sub.add_parser("shot")
    s.add_argument("file")
    v = sub.add_parser("record")
    v.add_argument("file")
    v.add_argument("seconds", type=int)
    sub.add_parser("power-cycle")
    a = ap.parse_args()

    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "build":
        return cmd_build(a)
    if a.cmd == "alive":
        ok = alive()
        print("V4 at %s %s" % (host(), "answers" if ok else "does not answer"))
        return 0 if ok else 1
    if a.cmd == "shot":
        shot(a.file)
        return 0
    if a.cmd == "record":
        p = start_recording(a.file, a.seconds)
        p.stdin.close()
        return p.wait()
    if a.cmd == "power-cycle":
        return 0 if power_cycle() else 1


if __name__ == "__main__":
    sys.exit(main())
