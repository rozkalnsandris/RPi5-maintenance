# APT policy

## Ownership

There must be one package-mutation owner during the maintenance window. Avoid competing unattended/manual update writers.

## Required behavior

- acquire the shared maintenance lock;
- run bounded preflight and package metadata refresh according to policy;
- distinguish simulation/check results from packages actually applied;
- capture package changes and exact exit status;
- treat interrupted/inconsistent package state as critical until repaired by an explicit recovery procedure;
- determine reboot requirement from supported host signals/policy rather than package-name guesses alone where possible;
- never run autonomous package downgrade/removal as doctor remediation.

Debian's `unattended-upgrades` is a supported package automation mechanism, but adopting it is an architecture choice. The critical invariant is that two independent package mutation engines do not compete.
