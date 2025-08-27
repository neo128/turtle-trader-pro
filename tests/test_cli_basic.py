import subprocess, sys

def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "turtletrader.cli", "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Turtle Trading CLI" in r.stdout
