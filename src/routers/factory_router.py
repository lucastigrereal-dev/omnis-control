"""
Factory Router — pipeline de produção offline.

Registra: assets, offline, render, quality, campaign, manual-publish, delivery, dashboard, asset-inbox
"""

import typer


def register(app: typer.Typer) -> None:
    from src.cli_commands.assets_cmd import assets_app
    from src.cli_commands.offline_factory_cmd import offline_app
    from src.cli_commands.render_cmd import render_app
    from src.cli_commands.quality_cmd import quality_app
    from src.cli_commands.campaign_cmd import campaign_app
    from src.cli_commands.manual_publish_cmd import manual_publish_app
    from src.cli_commands.delivery_cmd import delivery_app
    from src.cli_commands.dashboard_cmd import dashboard_app
    from src.cli_commands.asset_inbox_cmd import asset_inbox_app

    app.add_typer(assets_app)
    app.add_typer(offline_app)
    app.add_typer(render_app)
    app.add_typer(quality_app)
    app.add_typer(campaign_app)
    app.add_typer(manual_publish_app)
    app.add_typer(delivery_app)
    app.add_typer(dashboard_app)
    app.add_typer(asset_inbox_app)
