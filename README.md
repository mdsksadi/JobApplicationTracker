# Job Application Tracker

A polished desktop app for tracking job applications, with a weekly target, a
colour-coded motivation background, an offline license for the "Sadi App"
watermark, and **export-on-demand** — your application records are never saved
to disk automatically.

## Install

```bash
pip install job-application-tracker
```

Requires Python 3.10+. Works on Windows, Linux and macOS.

Run it with either command:

```bash
job-application-tracker
jat
```

Or as a module: `python -m job_application_tracker`

For Excel (`.xlsx`) export support, install the optional extra:

```bash
pip install "job-application-tracker[excel]"
```

## Using the app

- **Row 1 is always an input row.** Fill in the fields and press the green
  `+` button (or the **Add** button in the toolbar). The new application is
  inserted at the top of the saved list and row 1 is cleared for the next one.
- **20 applications per page** by default. Use **< Previous** / **Next >** to
  browse older applications. Change the page size in **Settings**.
- Columns: Number, Company Name, Position, Requirements, Link, Status,
  Credential, Application date, Important notes.
  - **Requirements** is a button: click it to open a compact window where you
    can add or remove requirements without widening the grid.
  - **Status** is a dropdown: Pending, Submitted, Rejected, 1st Interview,
    2nd Interview, Offer, Accepted, Withdrawn, plus any custom status you add
    via `+ Add custom status...` (e.g. `3rd Interview`).
  - **Link** has an `open` button that opens the URL in your browser.
  - **Application date** has a `today` shortcut; dates use `YYYY-MM-DD`.
  - **Notes** has a `...` button for longer multi-line notes.
- Saved rows can be edited directly. Click the red `x` in the Number column to
  delete one (with confirmation).

## Weekly target & background colour

Open **Settings** and set **Applications per week**. The window background
reflects how many applications you dated in the current Monday–Sunday week:

| Applications this week | Background |
|---|---|
| 0 | strong red |
| approaching target | progressively lighter red |
| exactly target | white |
| above target | progressively green |

The header shows `This week: 3 / 5 - 2 to go`.

## No automatic data files

Application records and the activity log live **only in memory** while the app
is open. Nothing is written when you close the app. To keep your data:

1. Click **Export**, choose JSON, CSV, TXT, Markdown, or XLSX, pick a path, and
   confirm. Only then is a file written.
2. Use **Import** to load a previously exported JSON or CSV file back into
   memory in a later session.

If you quit with unsaved applications, the app asks whether to export first.

The only automatic file is a tiny `config.json` in your user config directory
(`%APPDATA%\JobApplicationTracker\config.json` on Windows,
`~/.config/JobApplicationTracker/config.json` on Linux). It stores your weekly
target, custom statuses, theme, page size and license activation — never your
application records.

**TXT export** contains both a readable dump of every application and the full
activity timeline, so you can inspect it with any text editor or `cat`.

## License / watermark

The app displays a subtle **Sadi App** watermark by default. To remove it,
enter a signed license code via the **Activate** button. Codes are Ed25519
signed and verified offline — no internet connection or account required.

If you are the developer and want to issue codes:

```bash
# once: creates keys/private_key.pem (secret) and the bundled public key
python tools/generate_keys.py

# issue a code
python tools/issue_license.py "Customer Name"
python tools/issue_license.py "Customer Name" --expires 2027-12-31
```

Keep `keys/private_key.pem` private and back it up — it is gitignored and is
the only way to issue valid codes. The app ships only the public key.

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   Linux/macOS: source .venv/bin/activate
pip install -e .
pip install pytest
pytest
```

### Publishing to PyPI (maintainer)

```bash
python -m pip install build twine
python -m build
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

Uploading requires your own PyPI account/API token. The package name
`job-application-tracker` was available at the time of writing.

## License

Apache-2.0. See [LICENSE](LICENSE).
