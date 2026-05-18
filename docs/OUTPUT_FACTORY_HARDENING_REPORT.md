# Output Factory Hardening Report

Generated: 2026-05-18

## Status: DONE

## Module: `src/output_factory/`

| File | Role |
|---|---|
| `__init__.py` | Exports `OutputFactory` |
| `manifest.py` | `ManifestGenerator.generate()` — `outputs_manifest.json` |
| `indexer.py` | `FileIndexer.generate_index()` — `files_index.md` |
| `checksums.py` | `ChecksumGenerator.generate()` — `checksums.json` (SHA-256) |
| `zipper.py` | `PackageZipper.zip()` — `final_package.zip` |
| `validator.py` | `PackageValidator.validate()` — checks required files |
| `factory.py` | `OutputFactory.run()` — orchestrates all + `package_report.md` |

## Tests: `tests/output_factory/test_factory.py`

7/7 PASS

- `test_manifest_generates_correct_file_list`
- `test_checksums_are_valid_sha256`
- `test_zip_created_and_extractable`
- `test_files_index_contains_file_names`
- `test_validator_detects_missing_files`
- `test_factory_run_produces_all_outputs`
- `test_factory_dry_run_writes_nothing`

## Retroactive application

| Mission | Valid |
|---|---|
| MIS-20260518-002 | True |
| MIS-20260518-003 | True |
| MIS-20260518-004 | True |
| MIS-20260518-005 | True |
| MIS-20260518-006 | True |

Each mission `06_exports/` now contains:
- `outputs_manifest.json`
- `files_index.md`
- `checksums.json`
- `package_report.md`
- `final_package.zip`

Note: pre-existing `package_manifest.json` was NOT overwritten.

## CLI commands added to `src/cli_local.py`

- `omnis local output-index --mission <name>` — generates index + manifest
- `omnis local package --mission <name>` — full Output Factory run
