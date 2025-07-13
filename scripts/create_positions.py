from flask.cli import with_appcontext
import click
from app import create_app, db
from app.models import Position

# Create the Flask app instance
app = create_app()

# List of predefined positions
POSITIONS = [
    "President",
    "Governor",
    "Senator",
    "Women Representative",
    "Member Of Parliament",
    "Member Of County Assembly"
]

@click.command("create-positions")
@with_appcontext
def create_positions():
    """Create standard election positions."""
    for title in POSITIONS:
        if not Position.query.filter_by(title=title).first():
            position = Position(title=title)
            db.session.add(position)
    db.session.commit()
    click.echo("✅ Positions created successfully.")

# Register the CLI command
app.cli.add_command(create_positions)
