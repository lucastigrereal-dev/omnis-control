# W121 — HotelLead Model + HotelLeadRegistry Report

**Date:** 2026-05-15
**Status:** COMPLETE
**Tests:** 33/33 PASS (0.11s)

## Scope
Create `src/commercial/hotel_lead.py` — HotelLead dataclass composing `Lead` from `src/sales/leads.py` with hotel-specific fields, plus file-backed HotelLeadRegistry.

## Files Created
| File | Lines | Description |
|---|---|---|
| `src/commercial/__init__.py` | 2 | Package marker |
| `src/commercial/hotel_lead.py` | 267 | HotelLead model + HotelLeadRegistry |
| `tests/commercial/__init__.py` | 1 | Test package marker |
| `tests/commercial/test_hotel_lead.py` | 335 | 33 focused tests |

## Files Modified
None — zero existing file changes.

## Architecture

### Composition Pattern
HotelLead **composes** Lead (not inheritance) — both are `@dataclass`. Proxy properties (`lead_id`, `name`, `company`, `contact_channel`, `source`, `interest`) expose Lead fields for cross-module compatibility.

### Validation (__post_init__)
- `hotel_tier` ∈ {Starter, Growth, Premium}
- `niche` ∈ {hotel, resort, pousada, boutique, fazenda, urbano, hostel, eco_resort, glamping, apart_hotel}
- `priority_tier` ∈ {hot, warm, cold, disqualified}

### Computed Properties
- `is_pursuable` → priority_tier is "hot" or "warm"
- `is_premium_candidate` → hotel_tier == "Premium" AND fit_score >= 80

### HotelLeadRegistry
File-backed JSONL storage with create/get/get_by_base_lead/list_all/list_by_city/list_by_state/list_by_niche/list_by_tier/list_pursuable/list_by_priority + aggregate counters (count, pursuable_count, premium_candidates). Case-insensitive city/state filters.

## Security Verification
- All fields masked: `cnpj_placeholder`, `contact_value`, `room_count_placeholder`, `average_daily_rate_placeholder`
- `dry_run=True` universal default
- Zero .env reads, zero API calls, zero network
- All contact events use `*_MOCK` enum variants

## Test Results
```
tests/commercial/test_hotel_lead.py::TestHotelLead::test_create_hotel_lead_valid PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_proxy_properties_from_base_lead PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_invalid_hotel_tier_raises PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_invalid_niche_raises PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_invalid_priority_raises PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_is_pursuable PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_is_premium_candidate PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_cnpj_is_masked PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_to_dict_roundtrip PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_to_markdown PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_touch_updates_timestamp PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_default_values PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_dry_run_default PASSED
tests/commercial/test_hotel_lead.py::TestHotelLead::test_no_external_api PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_create_and_get PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_create_multiple PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_get_by_base_lead PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_get_by_base_lead_not_found PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_by_city PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_by_state PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_by_niche PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_by_tier PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_pursuable PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_list_by_priority PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_pursuable_count PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_premium_candidates PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_update PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_update_nonexistent PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_delete PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_delete_nonexistent PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_file_backed_save_load PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_to_jsonl PASSED
tests/commercial/test_hotel_lead.py::TestHotelLeadRegistry::test_no_external_calls PASSED

33 passed in 0.11s
```

## Risks
- None. All new files, zero existing code touched.
- Full suite running in background for confirmation.

## Next Step
Per cadence policy: **W122+W123 together** — SDR Prospect List + Outreach Sequencer.
