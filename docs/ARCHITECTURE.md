# Architecture

## Components

```text
scheduler/systemd
      |
      v
+---------------------+
| UPDATE ENGINE       |
| precheck            |
| cleanup / APT       |
| Docker transactions |
+----------+----------+
           |
           v
+---------------------+
| VERIFY ENGINE       |
| container health    |
| local app health    |
| public health       |
| dependent services  |
+----------+----------+
           |
           v
+---------------------+
| CLASSIFIER          |
| SUCCESS             |
| RECOVERED           |
| DEGRADED            |
| CRITICAL            |
+----------+----------+
           |
       if eligible
           v
+---------------------+
| DOCTOR              |
| bounded playbooks   |
+----------+----------+
           |
           v
      VERIFY AGAIN
           |
           v
 reboot decision + report + evidence
```

## Separation of concerns

- **Update engine:** performs explicitly allowed mutations.
- **Verifier:** observes the resulting real state independently of command exit codes.
- **Classifier:** converts evidence into an operational state.
- **Doctor:** may execute only policy-approved bounded remediation.
- **Reporter:** summarizes state and points to exact evidence.
- **Reboot policy:** is a final policy decision, not an automatic consequence of APT/Docker commands.

## Trust boundaries

`GitHub -> reviewed release -> controlled installer -> production RPi5`.

Production does not execute arbitrary repository `main`. Configuration and secrets stay on the host or in an approved secret store and are outside repository source.
