"""Creative Production Planner — deterministic, dry-run, stdlib-only.

NEVER generates real images.
NEVER renders real HTML.
NEVER calls Canva/Figma/external APIs.
ONLY produces specs, briefings, task plans, and deterministic packages.
"""

from __future__ import annotations

import textwrap
from typing import Optional

from .models import (
    AssetSpec,
    AssetType,
    CreativeBriefV2,
    CreativeFormat,
    CreativePackage,
    CreativeRequest,
    CreativeReviewPlan,
    CreativeStatus,
    CreativeTask,
    PackageStatus,
    ProductionAssetPlan,
    ProductionBatch,
    ReviewCheckpoint,
    ReviewVerdict,
    TaskStatus,
    _now,
    _short_id,
)

# ── Format defaults ───────────────────────────────────────────────────────────

FORMAT_CONFIG = {
    CreativeFormat.CAROUSEL: {
        "asset_types": [AssetType.IMAGE, AssetType.IMAGE, AssetType.TEXT_OVERLAY],
        "tools": ["canva", "canva", "canva"],
        "dimensions": "1080x1080",
    },
    CreativeFormat.REEL: {
        "asset_types": [AssetType.VIDEO, AssetType.AUDIO, AssetType.TEXT_OVERLAY],
        "tools": ["capcut", "capcut", "capcut"],
        "dimensions": "1080x1920",
    },
    CreativeFormat.PHOTO: {
        "asset_types": [AssetType.IMAGE],
        "tools": ["canva"],
        "dimensions": "1080x1350",
    },
    CreativeFormat.VIDEO: {
        "asset_types": [AssetType.VIDEO, AssetType.THUMBNAIL],
        "tools": ["capcut", "canva"],
        "dimensions": "1920x1080",
    },
    CreativeFormat.STORY: {
        "asset_types": [AssetType.IMAGE, AssetType.TEXT_OVERLAY],
        "tools": ["canva", "canva"],
        "dimensions": "1080x1920",
    },
    CreativeFormat.MULTI_COPY: {
        "asset_types": [AssetType.TEXT_OVERLAY],
        "tools": ["manual"],
        "dimensions": "1080x1080",
    },
}

DEFAULT_HOOK_VARIANTS = 3
DEFAULT_CHECKPOINTS = [
    ("Hook Review", ["Is the hook attention-grabbing?", "Is it under 3 seconds?"]),
    ("Visual Consistency", ["Matches brand colors?", "Fonts consistent?", "Style coherent?"]),
    ("Message Clarity", ["Key message readable?", "Caption supports visuals?"]),
    ("Brand Safety", ["No controversial content?", "Tone matches brand voice?"]),
    ("CTA Check", ["Clear call-to-action?", "CTA matches objective?"]),
]


class CreativeProductionPlanner:
    """Deterministic planner for creative production workflows.

    All methods are pure: same input → same output.
    No I/O, no network, no randomness beyond ID generation.
    """

    # ── Step 1: Build creative brief ──────────────────────────────────────────

    def build_creative_brief(self, request: CreativeRequest) -> CreativeBriefV2:
        """Build a CreativeBriefV2 from a CreativeRequest.

        Deterministic transformation with validation warnings.
        """
        warnings: list[str] = []

        if not request.account_handle:
            warnings.append("MISSING_ACCOUNT_HANDLE")
        if not request.topic:
            warnings.append("MISSING_TOPIC")
        if not request.objective:
            warnings.append("MISSING_OBJECTIVE")

        fmt = request.format
        cfg = FORMAT_CONFIG.get(fmt, FORMAT_CONFIG[CreativeFormat.CAROUSEL])

        hook_variants = self._generate_hooks(request.topic, request.tone, request.key_message)

        shot_list = self._generate_shot_list(fmt, request.asset_count)
        design_notes = self._generate_design_notes(request.visual_style, cfg["dimensions"])
        editing_notes = self._generate_editing_notes(fmt)

        brief = CreativeBriefV2(
            request_id=request.request_id,
            account_handle=request.account_handle,
            format=fmt,
            topic=request.topic,
            objective=request.objective,
            tone=request.tone,
            target_audience=request.target_audience,
            key_message=request.key_message,
            visual_direction=request.visual_style,
            hook_variants=hook_variants,
            caption_framework="hook → problem → solution → proof → CTA",
            shot_list=shot_list,
            design_notes=design_notes,
            editing_notes=editing_notes,
            music_mood=self._music_mood(request.tone),
            color_palette=self._color_palette(request.visual_style),
            font_suggestions=["Inter", "Plus Jakarta Sans"],
            asset_count_target=request.asset_count,
            tool_suggestions=cfg["tools"],
            status=CreativeStatus.PLANNED,
            warnings=warnings,
        )
        return brief

    # ── Step 2: Plan production assets ────────────────────────────────────────

    def plan_production_assets(self, brief: CreativeBriefV2) -> ProductionAssetPlan:
        """Create a ProductionAssetPlan from a CreativeBriefV2.

        Generates AssetSpec entries for each required asset.
        """
        cfg = FORMAT_CONFIG.get(brief.format, FORMAT_CONFIG[CreativeFormat.CAROUSEL])
        asset_types = cfg["asset_types"]
        tools = cfg["tools"]
        dims = cfg["dimensions"]

        assets: list[AssetSpec] = []
        tool_assignments: dict[str, str] = {}
        template_refs: dict[str, str] = {}

        for i in range(brief.asset_count_target):
            a_type = asset_types[i % len(asset_types)] if asset_types else AssetType.IMAGE
            tool = tools[i % len(tools)] if tools else "manual"
            label = a_type.value

            asset = AssetSpec(
                asset_index=i,
                asset_type=a_type,
                description=f"{label.title()} #{i+1} for '{brief.topic}'",
                dimensions=dims,
                duration_seconds=5.0 if a_type == AssetType.VIDEO else 0.0,
                text_content=brief.key_message if a_type == AssetType.TEXT_OVERLAY else "",
                source_hint=f"template://{brief.format.value}/slide_{i+1}",
                fallback_description=f"Generic {label} placeholder",
            )
            assets.append(asset)
            tool_assignments[f"asset_{i}"] = tool
            template_refs[f"slide_{i+1}"] = f"template://{brief.format.value}/v2/slide_{i+1}"

        total_minutes = len(assets) * 15

        return ProductionAssetPlan(
            brief_id=brief.brief_id,
            assets=assets,
            total_estimated_minutes=total_minutes,
            tool_assignments=tool_assignments,
            template_references=template_refs,
            notes=f"Asset plan for {brief.format.value} — {len(assets)} assets, ~{total_minutes}min estimated",
        )

    # ── Step 3: Build production batch ────────────────────────────────────────

    def build_production_batch(
        self, plan: ProductionAssetPlan, brief: CreativeBriefV2
    ) -> ProductionBatch:
        """Build a ProductionBatch from an asset plan and brief.

        Creates CreativeTask entries with dependency analysis.
        """
        tasks: list[CreativeTask] = []
        batch_id = _short_id()

        for asset in plan.assets:
            deps: list[str] = []
            # Asset 0 has no deps; subsequent assets depend on prior
            if asset.asset_index > 0:
                deps.append(f"task_{asset.asset_index - 1}")

            task = CreativeTask(
                batch_id=batch_id,
                brief_id=brief.brief_id,
                asset_index=asset.asset_index,
                asset_type=asset.asset_type,
                description=asset.description,
                tool_target=plan.tool_assignments.get(f"asset_{asset.asset_index}", "manual"),
                estimated_minutes=15,
                dependencies=deps,
                output_filename=f"{brief.format.value}_{asset.asset_type.value}_{asset.asset_index + 1}.png",
            )
            tasks.append(task)

        parallelizable = sum(1 for t in tasks if not t.dependencies)
        sequential = len(tasks) - parallelizable

        return ProductionBatch(
            batch_id=batch_id,
            brief_id=brief.brief_id,
            plan_id=plan.plan_id,
            tasks=tasks,
            estimated_total_minutes=sum(t.estimated_minutes for t in tasks),
            parallelizable_count=parallelizable,
            sequential_count=sequential,
            status=CreativeStatus.PLANNED,
        )

    # ── Step 4: Plan creative review ──────────────────────────────────────────

    def plan_creative_review(self, brief: CreativeBriefV2) -> CreativeReviewPlan:
        """Create a CreativeReviewPlan with standard checkpoints."""
        checkpoints: list[ReviewCheckpoint] = []
        for idx, (label, criteria) in enumerate(DEFAULT_CHECKPOINTS):
            checkpoints.append(
                ReviewCheckpoint(
                    checkpoint_index=idx,
                    label=label,
                    criteria=list(criteria),
                    required=True,
                    auto_pass=False,
                )
            )

        return CreativeReviewPlan(
            brief_id=brief.brief_id,
            checkpoints=checkpoints,
            reviewer="operator",
            verdict=ReviewVerdict.PENDING,
        )

    # ── Step 5: Validate creative package ─────────────────────────────────────

    def validate_creative_package(self, package: CreativePackage) -> CreativePackage:
        """Validate a CreativePackage, populating errors and warnings.

        Returns the same package with validation fields populated.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if package.brief is None:
            errors.append("MISSING_BRIEF: CreativeBriefV2 is required")
        else:
            if not package.brief.topic:
                errors.append("BRIEF_MISSING_TOPIC")
            if not package.brief.objective:
                errors.append("BRIEF_MISSING_OBJECTIVE")
            if package.brief.format not in FORMAT_CONFIG:
                errors.append(f"UNSUPPORTED_FORMAT: {package.brief.format}")

        if package.asset_plan is None:
            errors.append("MISSING_ASSET_PLAN: ProductionAssetPlan is required")
        elif not package.asset_plan.assets:
            warnings.append("ASSET_PLAN_EMPTY: No assets defined")

        if package.batch is None:
            errors.append("MISSING_BATCH: ProductionBatch is required")
        elif not package.batch.tasks:
            warnings.append("BATCH_EMPTY: No tasks defined")

        if package.review_plan is None:
            warnings.append("MISSING_REVIEW_PLAN: CreativeReviewPlan not provided")

        status = PackageStatus.VALIDATED if not errors else PackageStatus.DRAFT
        if warnings:
            status = PackageStatus.VALIDATED  # warnings don't block

        package.validation_errors = errors
        package.validation_warnings = warnings
        package.status = status
        package.updated_at = _now()
        return package

    # ── Step 6: Export creative package as markdown ───────────────────────────

    def export_creative_package_markdown(self, package: CreativePackage) -> str:
        """Export a CreativePackage as a deterministic markdown string.

        NEVER writes to disk. NEVER calls external services.
        Returns a markdown string suitable for saving or further processing.
        """
        lines: list[str] = []
        lines.append(f"# Creative Package: {package.package_id}")
        lines.append(f"**Status:** {package.status.value}")
        lines.append(f"**Created:** {package.created_at}")
        lines.append(f"**Updated:** {package.updated_at}")
        lines.append("")

        # ── Brief section ──
        if package.brief:
            b = package.brief
            lines.append("## Creative Brief V2")
            lines.append(f"- **Brief ID:** {b.brief_id}")
            lines.append(f"- **Account:** {b.account_handle}")
            lines.append(f"- **Format:** {b.format.value}")
            lines.append(f"- **Topic:** {b.topic}")
            lines.append(f"- **Objective:** {b.objective}")
            lines.append(f"- **Tone:** {b.tone}")
            lines.append(f"- **Target Audience:** {b.target_audience}")
            lines.append(f"- **Key Message:** {b.key_message}")
            lines.append(f"- **Visual Direction:** {b.visual_direction}")
            lines.append(f"- **Music Mood:** {b.music_mood}")
            lines.append("")
            if b.color_palette:
                lines.append(f"- **Color Palette:** {', '.join(b.color_palette)}")
            if b.font_suggestions:
                lines.append(f"- **Font Suggestions:** {', '.join(b.font_suggestions)}")
            lines.append("")
            if b.hook_variants:
                lines.append("### Hook Variants")
                for h in b.hook_variants:
                    lines.append(f"- {h}")
                lines.append("")
            if b.shot_list:
                lines.append("### Shot List")
                for s in b.shot_list:
                    lines.append(f"- {s}")
                lines.append("")
            lines.append(f"### Design Notes\n\n{b.design_notes}\n")
            lines.append(f"### Editing Notes\n\n{b.editing_notes}\n")
            if b.warnings:
                lines.append(f"### Warnings: {', '.join(b.warnings)}\n")

        # ── Asset Plan section ──
        if package.asset_plan:
            ap = package.asset_plan
            lines.append("## Production Asset Plan")
            lines.append(f"- **Plan ID:** {ap.plan_id}")
            lines.append(f"- **Estimated Total:** ~{ap.total_estimated_minutes}min")
            lines.append("")
            lines.append("| # | Type | Description | Dimensions | Tool |")
            lines.append("|---|---|---|---|---|")
            for a in ap.assets:
                tool = ap.tool_assignments.get(f"asset_{a.asset_index}", "manual")
                lines.append(
                    f"| {a.asset_index + 1} | {a.asset_type.value} | {a.description} | {a.dimensions} | {tool} |"
                )
            lines.append("")

        # ── Batch section ──
        if package.batch:
            bt = package.batch
            lines.append("## Production Batch")
            lines.append(f"- **Batch ID:** {bt.batch_id}")
            lines.append(f"- **Total Tasks:** {len(bt.tasks)}")
            lines.append(f"- **Estimated:** ~{bt.estimated_total_minutes}min")
            lines.append(f"- **Parallelizable:** {bt.parallelizable_count}")
            lines.append(f"- **Sequential:** {bt.sequential_count}")
            lines.append("")
            lines.append("| Task | Type | Tool | Est. | Deps |")
            lines.append("|---|---|---|---|---|")
            for t in bt.tasks:
                deps_str = ", ".join(t.dependencies) if t.dependencies else "none"
                lines.append(
                    f"| {t.task_id} | {t.asset_type.value} | {t.tool_target} | {t.estimated_minutes}min | {deps_str} |"
                )
            lines.append("")

        # ── Review section ──
        if package.review_plan:
            rp = package.review_plan
            lines.append("## Creative Review Plan")
            lines.append(f"- **Review ID:** {rp.review_id}")
            lines.append(f"- **Reviewer:** {rp.reviewer}")
            lines.append(f"- **Verdict:** {rp.verdict.value}")
            lines.append("")
            for cp in rp.checkpoints:
                lines.append(f"### {cp.checkpoint_index + 1}. {cp.label} {'(required)' if cp.required else '(optional)'}")
                for c in cp.criteria:
                    lines.append(f"- [ ] {c}")
                lines.append("")

        # ── Validation section ──
        lines.append("## Validation")
        if package.validation_errors:
            lines.append("### Errors")
            for e in package.validation_errors:
                lines.append(f"- ❌ {e}")
            lines.append("")
        if package.validation_warnings:
            lines.append("### Warnings")
            for w in package.validation_warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")
        if not package.validation_errors and not package.validation_warnings:
            lines.append("✅ No validation issues.\n")

        lines.append("---")
        lines.append(f"*Generated by CreativeProductionPlanner v2 — {package.created_at}*")
        lines.append("*Dry-run only. No assets generated. No external APIs called.*")

        return "\n".join(lines)

    # ── Pipeline: request → package in one call ───────────────────────────────

    def plan_from_request(self, request: CreativeRequest) -> CreativePackage:
        """Full pipeline: CreativeRequest → CreativePackage in one shot."""
        brief = self.build_creative_brief(request)
        asset_plan = self.plan_production_assets(brief)
        batch = self.build_production_batch(asset_plan, brief)
        review_plan = self.plan_creative_review(brief)

        package = CreativePackage(
            brief=brief,
            asset_plan=asset_plan,
            batch=batch,
            review_plan=review_plan,
        )
        return self.validate_creative_package(package)

    # ── Helpers (deterministic) ───────────────────────────────────────────────

    @staticmethod
    def _generate_hooks(topic: str, tone: str, key_message: str) -> list[str]:
        if not topic:
            return ["[Hook placeholder — no topic provided]"]
        tone_tag = f"[{tone}] " if tone else ""
        return [
            f"{tone_tag}Você sabia que {topic} pode transformar seus resultados?",
            f"{tone_tag}O segredo de {topic} que ninguém te contou.",
            f"{tone_tag}3 erros fatais sobre {topic} (e como evitar).",
        ]

    @staticmethod
    def _generate_shot_list(fmt: CreativeFormat, count: int) -> list[str]:
        base: list[str] = []
        for i in range(count):
            base.append(f"Slide {i+1}: [{fmt.value}] — visual placeholder, no real render")
        return base

    @staticmethod
    def _generate_design_notes(visual_style: str, dimensions: str) -> str:
        style = visual_style or "clean-modern"
        return textwrap.dedent(f"""\
            Style: {style}
            Dimensions: {dimensions}
            Brand Kit: use project brand_kit/ (logos, colors, fonts)
            Placeholder Mode: shapes + text only — no real stock photos
            Note: dry-run — no actual pixels rendered.""")

    @staticmethod
    def _generate_editing_notes(fmt: CreativeFormat) -> str:
        notes = {
            CreativeFormat.REEL: "Keep cuts under 2s. Sync beats to transitions. End with CTA frame.",
            CreativeFormat.CAROUSEL: "Slide 1 = hook. Last slide = CTA. Consistent spacing.",
            CreativeFormat.PHOTO: "Single frame. Focus on composition and lighting. Overlay CTA text if needed.",
            CreativeFormat.VIDEO: "Intro 3s, body 30-60s, outro 5s with CTA. Subtitles required.",
            CreativeFormat.STORY: "Vertical 9:16. Quick cuts. Poll/sticker for engagement. Link sticker CTA.",
            CreativeFormat.MULTI_COPY: "Text-only format. Focus on copy hierarchy and readability.",
        }
        return notes.get(fmt, "Standard editing flow. Review before final render.")

    @staticmethod
    def _music_mood(tone: str) -> str:
        mapping = {
            "inspirador": "uplifting-cinematic",
            "divertido": "fun-upbeat-pop",
            "emocionante": "emotional-piano-strings",
            "urgente": "fast-drive-beat",
            "calmo": "ambient-chill-lofi",
            "luxo": "sophisticated-jazz-lounge",
            "aventura": "epic-orchestral-adventure",
        }
        return mapping.get(tone.lower(), "neutral-corporate")

    @staticmethod
    def _color_palette(visual_style: str) -> list[str]:
        palettes = {
            "clean": ["#FFFFFF", "#1A1A1A", "#0066CC"],
            "warm": ["#FFF8F0", "#E07A5F", "#3D405B"],
            "bold": ["#FF3366", "#FFD700", "#121212"],
            "nature": ["#2D6A4F", "#D4EDDA", "#F8F9FA"],
            "luxo": ["#1A1A1A", "#C9A96E", "#F5F5F0"],
            "praia": ["#00B4D8", "#FFE066", "#023E8A"],
            "gastronomia": ["#E63946", "#FFF3E0", "#2B2B2B"],
        }
        key = visual_style.lower() if visual_style else "clean"
        for k, v in palettes.items():
            if k in key:
                return v
        return palettes["clean"]
