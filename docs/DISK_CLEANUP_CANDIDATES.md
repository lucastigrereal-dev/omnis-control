# Disk Cleanup Candidates — Read-Only Survey

**Date:** 2026-05-04  
**Disk:** 72.8 GB free (7.3% of 992.5 GB)  
**Note:** This is a catalog only. No cleanup was executed.

---

## 1. Docker (Reclaimable: ~70 GB — Highest Impact)

| Candidate | Est. Reclaim | Risk | Command |
|---|---|---|---|
| Unused images | ~54 GB | 🟢 Safe | `docker image prune -f` |
| Build cache | ~16 GB | 🟢 Safe | `docker builder prune -f` |
| Unused volumes | ~7.8 GB | 🔴 Dangerous | `docker system prune -a --volumes` |
| **Total safe** | **~70 GB** | 🟢 | |

**Impact:** Would free ~70 GB, bringing disk to ~15% — still low but no longer critical.

---

## 2. Cache Directories (Reclaimable: ~10+ GB)

| Path | Est. Size | Risk | Notes |
|---|---|---|---|
| `~/.cache/` | ~9.9 GB | 🟢 Safe | Chroma ONNX models, pip/http cache, CUDA |
| `~/.cache/pip/` | ~1-2 GB | 🟢 Safe | Old pip cache, safe to clear |
| `~/.cache/chroma/` | ~500 MB | 🟢 Safe | ONNX embedding model cache |

**Commands (not executed):**
```bash
rm -rf ~/.cache/pip/*
rm -rf ~/.cache/chroma/onnx_models
```

---

## 3. Archives & Backups (Reclaimable: varies)

| Path | Est. Size | Risk | Notes |
|---|---|---|---|
| `~/arquivos zip/` | 500 MB+ | 🟡 Review | Old zip files with long hashed names |
| `~/Backups/` | unknown | 🟡 Review | Server backups from Nov 2025 |
| `~/_BACKUP_PROJETOS_RIMA_2026-02-08.tar.gz` | unknown | 🟡 Review | Project backup |
| `~/clinical_companion_*.tar.gz` | ~2 GB | 🟡 Review | Old project backup |

**Risk:** Review before deleting — may contain needed project data.

---

## 4. Build Artifacts (Reclaimable: ~1.5 GB)

| Path | Size | Risk | Notes |
|---|---|---|---|
| `~/daily-prophet-hotels/.next/` | 657 MB | 🟢 Safe | Next.js build cache, rebuilds on `next build` |
| `~/publisher-os/services/publish-worker/node_modules/` | 120 MB | 🟢 Safe | Reinstallable via npm |

**Commands (not executed):**
```bash
rm -rf ~/daily-prophet-hotels/.next
```

---

## 5. Python Caches (Reclaimable: ~500 MB)

| Pattern | Risk | Notes |
|---|---|---|
| `__pycache__` dirs | 🟢 Safe | Auto-regenerated on import |
| `.venv/Lib/site-packages/` | 🟡 Review | Only if rebuilding venv |
| `~/.cache/pip/` | 🟢 Safe | Downloaded wheels |

---

## 6. Downloads (Reclaimable: 8.4 GB)

| Path | Size | Risk | Notes |
|---|---|---|---|
| `~/Downloads/` | 8.4 GB | 🟡 Review | Contains current project files too |

**Review needed** before bulk cleanup — may contain active project files.

---

## 7. Priority Matrix

| Priority | Candidate | Est. GB | Risk | Effort |
|---|---|---|---|---|
| **P0** | Docker image prune | 54 GB | 🟢 | 1 cmd |
| **P1** | Docker builder prune | 16 GB | 🟢 | 1 cmd |
| **P2** | Clear pip cache | 1-2 GB | 🟢 | 1 cmd |
| **P3** | Remove .next build cache | 657 MB | 🟢 | 1 cmd |
| **P4** | Review archives/backups | 2-5 GB | 🟡 | Manual review |
| **P5** | Review Downloads | 8.4 GB | 🟡 | Manual review |
| **P6** | Dangerous: full docker prune | 75 GB | 🔴 | Only if needed |

**Recommended first action:**
```bash
docker image prune -f          # +54 GB, safe
docker builder prune -f        # +16 GB, safe
```
These two alone would bring disk from 7.3% to ~14-15%.
