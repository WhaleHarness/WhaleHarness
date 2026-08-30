import json, urllib.request, re, urllib.error, sys
issues = []
try:
    d = json.loads(urllib.request.urlopen(urllib.request.Request("https://whaleharness.com/bundles.json", headers={"User-Agent":"WhaleHarness-agent-qa"}), timeout=15).read().decode())
except Exception as e:
    print("BUNDLES-JSON-FETCH-FAIL", e); sys.exit(1)
for b in d["bundles"]:
    bid = b.get("id", "?")
    prof = b.get("profile_url", "")
    one = b.get("one_liner", "")
    if not prof:
        issues.append(f"{bid}: NO profile_url (not bundled)")
    else:
        try:
            with urllib.request.urlopen(urllib.request.Request(prof, headers={"User-Agent":"WhaleHarness-agent-qa"}), timeout=12) as r:
                if r.status != 200:
                    issues.append(f"{bid}: profile {r.status}")
        except Exception as e:
            issues.append(f"{bid}: profile ERR {e}")
    if one:
        for u in re.findall(r"https://[^\s&\"']+", one):
            u2 = u.split("?")[0]
            try:
                with urllib.request.urlopen(urllib.request.Request(u2, headers={"User-Agent":"WhaleHarness-agent-qa"}), timeout=10) as r:
                    code = r.status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception:
                code = "ERR"
            if code != 200:
                issues.append(f"{bid}: cmd-url {code} {u2}")
if issues:
    print("BUNDLE-QA-FAIL:")
    for i in issues: print(" ", i)
    sys.exit(1)
else:
    print("BUNDLE-QA-OK: all bundles bundled & buttons reachable")
