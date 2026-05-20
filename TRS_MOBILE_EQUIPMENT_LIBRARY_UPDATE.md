# TRS Mobile Mode + Equipment Library Update

## Added
- Mobile Mode for phones:
  - Hamburger sidebar menu
  - Responsive cards/forms/tables
  - Mobile equipment cards
  - No changes to the Excel Live Sheet editor

- Equipment library bundled into the project:
  - `sample_data/equipment/HPU/` with 40 Excel history cards
  - `sample_data/equipment/Power Tong/` with 58 Excel history cards

- Automatic equipment seeding on startup:
  - Each Excel file becomes an equipment record
  - Folder name becomes the category
  - File name becomes the equipment serial number
  - Source Excel file is copied to uploads and linked to the equipment record

## Equipment structure
```text
Equipment
├── HPU
│   ├── 111467.xlsx
│   ├── 111468.xlsx
│   └── ...
└── Power Tong
    ├── 110093.xlsx
    ├── 111520.xlsx
    └── ...
```

## Notes
- The Excel Live Sheet editor was intentionally not changed.
- On first run, the system imports the bundled equipment library automatically.
