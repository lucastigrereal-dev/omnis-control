"""
System Router — missões, ferramentas, métricas, publisher, pipeline, video.

Registra: argos-drafts, creative, publisher, forge, pipeline,
          missions, tools, metrics, oauth, post, video
"""

import typer


def register(app: typer.Typer) -> None:
    from src.cli_commands.argos_drafts_cmd import argos_app
    from src.cli_commands.creative_cmd import creative_app
    from src.cli_commands.publisher_cmd import publisher_app
    from src.cli_commands.forge_cmd import forge_app
    from src.cli_commands.pipeline_cmd import pipeline_app
    from src.cli_commands.missions_cmd import missions_app
    from src.cli_commands.tools_cmd import tools_app
    from src.cli_commands.metrics_cmd import metrics_app
    from src.cli_commands.oauth_cmd import oauth_app
    from src.cli_commands.post_cmd import post_app
    from src.cli_commands.video_production_cmd import video_production_app
    from src.cli_commands.knowledge_cmd import knowledge_app
    from src.cli_commands.mission_builder_cmd import mission_builder_app
    from src.cli_commands.mission_report_cmd import mission_report_app
    from src.cli_commands.mission_orchestrator_cmd import orchestrator_app
    from src.cli_commands.sectors_registry_cmd import sector_registry_app
    from src.cli_commands.skill_matcher_cmd import skill_matcher_app
    from src.cli_commands.capability_gap_cmd import capability_gap_app
    from src.cli_commands.approval_center_cmd import approval_center_app
    from src.cli_commands.capability_forge_lite_cmd import capability_forge_lite_app
    from src.cli_commands.role_registry_cmd import role_registry_app
    from src.cli_commands.squad_composer_cmd import squad_composer_app
    from src.cli_commands.task_decomposer_cmd import task_decomposer_app
    from src.cli_commands.squad_execution_cmd import squad_execution_app

    app.add_typer(argos_app)
    app.add_typer(creative_app)
    app.add_typer(publisher_app)
    app.add_typer(forge_app)
    app.add_typer(pipeline_app)
    app.add_typer(missions_app)
    app.add_typer(tools_app)
    app.add_typer(metrics_app)
    app.add_typer(oauth_app)
    app.add_typer(post_app)
    app.add_typer(video_production_app)
    app.add_typer(knowledge_app)
    app.add_typer(mission_builder_app)
    app.add_typer(mission_report_app)
    app.add_typer(orchestrator_app)
    app.add_typer(sector_registry_app)
    app.add_typer(skill_matcher_app)
    app.add_typer(capability_gap_app)
    app.add_typer(approval_center_app)
    app.add_typer(capability_forge_lite_app)
    app.add_typer(role_registry_app)
    app.add_typer(squad_composer_app)
    app.add_typer(task_decomposer_app)
    app.add_typer(squad_execution_app)
