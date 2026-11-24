# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | Yes |
| Earlier | No code was released |

## Reporting a vulnerability

Please do not put vulnerability details in a public issue. GitHub private vulnerability reporting is not currently enabled for this repository, so open a minimal issue asking for a private contact channel and leave out the technical details.

Include the affected version, the impact and the steps needed to reproduce the problem. This is a personal project, so responses are best effort and no response time is guaranteed.

## Scope

The tool runs locally and processes command-line input. Relevant reports include code execution through formula input, resource exhaustion that bypasses the documented limits, SQL injection in the run store and compromise of the build or CI configuration.
