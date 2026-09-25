"""HTTP server inside the sandbox image that runs one piece of code per request. Stub, Lane D.

Purpose
Execute untrusted R and Python safely. This file runs inside the sandbox container only and uses the
standard library only, so the image stays small.

What to build
POST /run with language, code and optional base64 data. Write them to a fresh temporary folder,
run Rscript or python in a child process with resource limits for CPU seconds, memory and open
files, a wall clock timeout and an empty environment. Return stdout, the JSON values printed on the
last line, the duration and an error when the process fails or times out. Delete the folder after.
GET /health answers ok.

How to test
Run this file with plain python and send a request that loops forever, it must come back as a
timeout within the limit.
"""

raise SystemExit("the sandbox runner is not written yet")
