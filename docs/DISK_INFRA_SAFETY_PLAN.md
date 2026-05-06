# Disk & Infra Safety Plan

**Date:** 2026-05-04  
**Author:** OMNIS Disk Audit  
**Status:** Plan only — no actions executed  

---

## Current State

| Metric | Value |
|---|---|
| Total | 992.5 GB |
| Used | 919.7 GB (92.7%) |
| Free | **72.8 GB (7.3%)** |
| Risk Level | **CRITICAL** |
| Time to full at current rate | ~2-4 weeks |

---

## Phase 1: Quick Wins (Safe)

Estimated gain: **~72 GB** (bringing disk to ~14-15%)

| Order | Action | Gain | Risk | Why safe |
|---|---|---|---|---|
| 1 | `docker image prune -f` | 54 GB | 🟢 | Only removes dangling/unused images |
| 2 | `docker builder prune -f` | 16 GB | 🟢 | Only removes build cache |
| 3 | `rm -rf ~/.cache/pip/*` | 1-2 GB | 🟢 | Pip cache is auto-rebuilt |
| 4 | `rm -rf ~/daily-prophet-hotels/.next` | 657 MB | 🟢 | Rebuilt on `npm run build` |
| 5 | `find ~ -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null` | ~100 MB | 🟢 | Auto-regenerated |

**Total Phase 1: ~72 GB**

---

## Phase 2: Review Required (Medium)

Estimated gain: **~5-15 GB**

| Order | Action | Gain | Risk | Review needed |
|---|---|---|---|---|
| 6 | Review `~/Downloads/` (8.4 GB) | 2-8 GB | 🟡 | Check for active project files |
| 7 | Review archives in `~/arquivos zip/` | 1-3 GB | 🟡 | Likely old, but manual check |
| 8 | Review `~/Backups/` | 2-5 GB | 🟡 | Backups from Nov 2025 |
| 9 | Review clinical_companion archives | ~2 GB | 🟡 | Old project backup |

---

## Phase 3: Dangerous (Only If Needed)

| Action | Gain | Risk | Warning |
|---|---|---|---|
| `docker system prune -a --volumes` | ~75 GB | 🔴 | Removes ALL unused data including volumes |
| Delete `~/.cache/chroma/` | ~500 MB | 🟡 | May need to re-download ONNX models |
| Delete entire `.venv` | 1-2 GB | 🟡 | Requires `pip install -r requirements.txt` |

---

## Infrastructure Risks Beyond Disk

### Publisher OS (:8000 offline)
- **Impact:** Content production blocked
- **Fix requires:** Enter container or docker-compose restart
- **Blocked by:** D003 (don't modify Docker/Publisher)
- **Status:** Requires separate authorization

### Qdrant (:6333 inaccessible)
- **Impact:** Memory service broken, semantic search offline
- **Known cause:** Embedding dims mismatch (768 vs 1536)
- **Fix:** Update config to `embedding_model_dims: 768`
- **Status:** Requires config change authorization

### 2 Unhealthy Containers
- **Containers:** `crm-tigre-backend`, `jarvis_frontend`
- **Impact:** ~1-2 GB RAM wasted
- **Suggested:** `docker stop crm-tigre-backend jarvis_frontend`
- **Status:** Requires authorization

---

## Monitoring Recommendations

1. Run `python -m src.cli disk` weekly — already exists
2. Set up disk alert at 10% free — manual for now
3. After cleanup, monitor if Docker images grow back (indicates active rebuilds)

---

## Execution Checklist

When authorized:

- [ ] `docker image prune -f`
- [ ] `docker builder prune -f`
- [ ] `rm -rf ~/.cache/pip/*`
- [ ] `rm -rf ~/daily-prophet-hotels/.next`
- [ ] `python -m src.cli disk` — confirm new free space
- [ ] Manual: review Downloads
- [ ] Manual: review archives
- [ ] Manual: docker stop unhealthy containers
