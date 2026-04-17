# automation
Automation scripts
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
body {
    margin: 0;
    padding: 0;
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 40px;
}

h1 {
    color: #58a6ff;
    font-size: 38px;
    margin-bottom: 10px;
}

h2 {
    color: #58a6ff;
    margin-top: 30px;
    border-bottom: 1px solid #30363d;
    padding-bottom: 6px;
}

h3 {
    color: #79c0ff;
}

p {
    color: #c9d1d9;
}

.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 15px 20px;
    margin: 15px 0;
}

code {
    background: #161b22;
    padding: 4px 8px;
    border-radius: 6px;
    color: #7ee787;
}

pre {
    background: #161b22;
    padding: 15px;
    border-radius: 10px;
    overflow-x: auto;
    border: 1px solid #30363d;
    color: #c9d1d9;
}

.tag {
    display: inline-block;
    background: #238636;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    margin-right: 6px;
    color: white;
}

.warn {
    color: #ff7b72;
}

.ok {
    color: #3fb950;
}

a {
    color: #58a6ff;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border: none;
    border-top: 1px solid #30363d;
    margin: 25px 0;
}

.small {
    font-size: 13px;
    color: #8b949e;
}
</style>

</head>

<body>

<div class="container">

<h1>gitx — Automated Git Workflow CLI</h1>

<p class="small">A fully automated Git CLI tool for Termux & Linux systems.</p>

<hr>

<h2>Overview</h2>

<div class="card">
gitx automates the entire Git workflow from initialization to push.  
It removes repetitive Git setup steps and enforces a clean SSH-first workflow.
</div>

<hr>

<h2>Features</h2>

<div class="card">

<span class="tag">Automation</span>
<span class="tag">SSH First</span>
<span class="tag">Cross Platform</span>

<ul>
<li>Auto Git installation (Termux / Linux)</li>
<li>SSH key detection + generation</li>
<li>Automatic identity configuration</li>
<li>Repository initialization</li>
<li>Branch management</li>
<li>Remote setup (HTTPS + SSH)</li>
<li>Commit + push automation</li>
<li>Global CLI installation</li>
</ul>

</div>

<hr>

<h2>Installation</h2>

<div class="card">

<pre>
chmod +x git.py
python git.py
</pre>

When prompted:
<pre>Install globally? (y/n): y</pre>

This installs the tool as:
<code>gitx</code>

</div>

<hr>

<h2>Usage</h2>

<div class="card">

<pre>
gitx
</pre>

Run inside any project folder.

</div>

<hr>

<h2>Workflow</h2>

<div class="card">

<ol>
<li>Git environment check</li>
<li>User identity setup</li>
<li>SSH verification / generation</li>
<li>Directory selection</li>
<li>Repository initialization</li>
<li>Branch configuration</li>
<li>Remote linking</li>
<li>Commit staging</li>
<li>Push to GitHub</li>
</ol>

</div>

<hr>

<h2>SSH System</h2>

<div class="card">

If SSH is missing:
<ul>
<li>Key is automatically generated</li>
<li>Public key is displayed</li>
<li>User adds it to GitHub</li>
</ul>

Link:
<code>https://github.com/settings/keys</code>

</div>

<hr>

<h2>Remote Options</h2>

<div class="card">

<pre>
1) Existing URL (HTTPS or SSH)
2) Create repo manually
3) Paste repo URL
</pre>

Supports both HTTPS and SSH (SSH recommended).

</div>

<hr>

<h2>Example Output</h2>

<div class="card">

<pre>
[INFO] Starting git automation tool
[OK] Git found
[OK] Identity OK
[OK] SSH ready
[INFO] Repository initialized
[OK] Push complete
</pre>

</div>

<hr>

<h2>Philosophy</h2>

<div class="card">

- Zero friction Git workflow  
- Fail-fast environment setup  
- SSH-first authentication  
- Fully deterministic execution  
- Minimal user interaction  

</div>

<hr>

<h2>Requirements</h2>

<div class="card">

- Python 3.x  
- Git  
- Linux or Termux  

Optional:
- sudo (for system-wide install)

</div>

<hr>

<h2>Notes</h2>

<div class="card">

- Always re-run after SSH setup  
- Prefer SSH URLs for best performance  
- Designed for automation-heavy workflows  

</div>

<hr>

<p class="small">
Built for fast terminal development workflows.
</p>

</div>

</body>
</html>
