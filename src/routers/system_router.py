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
