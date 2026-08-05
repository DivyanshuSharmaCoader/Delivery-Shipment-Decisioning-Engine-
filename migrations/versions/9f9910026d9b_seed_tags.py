from alembic import op
import sqlalchemy as sa

revision = "YOUR_NEW_REVISION_ID"
down_revision = "f52dda889cc5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("""
        INSERT INTO tag (id, name, instructions) VALUES
        (gen_random_uuid(), 'EXPRESS', 'Handle with priority - deliver within 24 hours'),
        (gen_random_uuid(), 'STANDARD', 'Regular delivery within 3-5 business days'),
        (gen_random_uuid(), 'FRAGILE', 'Handle with care - contains breakable items'),
        (gen_random_uuid(), 'HEAVY', 'Weight exceeds 20kg - use appropriate equipment'),
        (gen_random_uuid(), 'INTERNATIONAL', 'Package requires customs clearance'),
        (gen_random_uuid(), 'DOMESTIC', 'For delivery within country borders only'),
        (gen_random_uuid(), 'TEMPERATURE_CONTROLLED', 'Keep between 2-8°C at all times'),
        (gen_random_uuid(), 'GIFT', 'Contains gift items - handle discreetly'),
        (gen_random_uuid(), 'RETURN', 'Package is being returned to sender'),
        (gen_random_uuid(), 'DOCUMENTS', 'Contains important documents - keep dry');
    """))


def downgrade():
    op.execute(sa.text("DELETE FROM tag;"))