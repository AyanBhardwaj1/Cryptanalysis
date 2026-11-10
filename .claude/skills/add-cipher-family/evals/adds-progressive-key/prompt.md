---
tags: [add-cipher-family]
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

add a progressive key cipher to the lab: periodic key where every full cycle the whole key gets shifted up by some step d (mod 29). the orchestrator should be able to propose it
