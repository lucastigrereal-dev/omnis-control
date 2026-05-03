"""OMNIS CLI command groups.

Future home for extracted CLI command modules.
Each module exports a Typer app registered in cli.py.

Current groups planned:
    diagnostics      status, skills, doctor, report
    video_assets_cmd video-status, video-assets
    content_queue_cmd queue, accounts
    caption_approval_cmd captions, approvals, templates
    publisher_cmd    publisher-health
    docker_cmd       docker-status
    memory_cmd       memory-status
    obsidian_cmd     obsidian-status
    argos_drafts_cmd argos-drafts (Fase 2E)
    integrations_cmd integrations (Fase 3A+)
"""
