# TRS Job Files update — Connection-level filing

Implemented change requested by Cláudio:

## New file structure

```text
Company / Year / Rig / Connection Type / Files
```

Example:

```text
AGIBA / 2026 / EDC 47 / VAM TOP
AGIBA / 2026 / EDC 47 / PH-6
```

## What changed

- Removed `Well` from the folder path level.
- `Well` is still extracted from PDF as metadata only, so it can be searched and shown in file detail.
- Smart PDF detection now suggests paths like:
  - `AGIBA / 2026 / EDC 47 / VAM TOP`
- Job Files UI now has separated browser columns:
  1. Company
  2. Year
  3. Rig
  4. Connection Type
- Upload modal only asks for Company / Year / Rig / Connection Type.
- Create Path modal creates a connection folder only.
- Folder delete now works on connection-level folders.

## Demo PDF expected result

For `Job# 4-AGIBA _ EDC 47- LOTUS.W.3_Report.PDF`, the system should classify as:

```text
AGIBA / 2026 / EDC 47 / VAM TOP
```

`LOTUS.W.3` is retained as detected well metadata, not a folder.
