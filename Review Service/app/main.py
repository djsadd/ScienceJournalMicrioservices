from fastapi import FastAPI
from sqlalchemy import inspect, text
from app.reviews_router import router as reviews_router
from app.database import Base, engine

app = FastAPI(title="Review Service")

# создаем таблицы
Base.metadata.create_all(bind=engine)


def _ensure_schema():
	"""Lightweight migration to ensure required columns exist."""
	inspector = inspect(engine)
	try:
		columns = {col["name"] for col in inspector.get_columns("reviews")}
	except Exception:
		columns = set()

	alters: list[str] = []
	expected = {
		"deadline": "TIMESTAMPTZ NULL",
		"importance_applicability": "TEXT NULL",
		"novelty_application": "TEXT NULL",
		"originality": "TEXT NULL",
		"innovation_product": "TEXT NULL",
		"results_significance": "TEXT NULL",
		"coherence": "TEXT NULL",
		"style_quality": "TEXT NULL",
		"editorial_compliance": "TEXT NULL",
	}

	for name, ddl in expected.items():
		if name not in columns:
			alters.append(f"ADD COLUMN IF NOT EXISTS {name} {ddl}")

	if alters:
		with engine.connect() as conn:
			conn.execute(text("ALTER TABLE reviews " + ", ".join(alters)))
			conn.commit()

	# Ensure enum value 'resubmission' exists in PostgreSQL type reviewstatus
	try:
		with engine.connect() as conn:
			existing = conn.execute(text("""
				SELECT e.enumlabel
				FROM pg_type t
				JOIN pg_enum e ON t.oid = e.enumtypid
				WHERE t.typname = 'reviewstatus'
			""")).fetchall()
			labels = {row[0] for row in existing}
			if 'resubmission' not in labels:
				conn.execute(text("ALTER TYPE reviewstatus ADD VALUE IF NOT EXISTS 'resubmission'"))
				conn.commit()
	except Exception:
		# Silent ignore; if fails, service will still run but endpoint will error until manual migration
		pass


_ensure_schema()

app.include_router(reviews_router)
