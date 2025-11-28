"""add_full_article_snapshot_to_versions

Revision ID: f02b17fc7620
Revises: 20251126_02
Create Date: 2025-11-27 12:41:42.385191

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f02b17fc7620'
down_revision = '20251126_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новые колонки в article_versions для полного снимка статьи
    op.add_column('article_versions', sa.Column('title_kz', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('title_en', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('title_ru', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('abstract_kz', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('abstract_en', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('abstract_ru', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('doi', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('article_type', sa.Enum('original', 'review', name='articletype'), nullable=True))
    op.add_column('article_versions', sa.Column('manuscript_file_url', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('antiplagiarism_file_url', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('author_info_file_url', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('cover_letter_file_url', sa.String(), nullable=True))
    op.add_column('article_versions', sa.Column('not_published_elsewhere', sa.Boolean(), nullable=True))
    op.add_column('article_versions', sa.Column('plagiarism_free', sa.Boolean(), nullable=True))
    op.add_column('article_versions', sa.Column('authors_agree', sa.Boolean(), nullable=True))
    op.add_column('article_versions', sa.Column('generative_ai_info', sa.String(), nullable=True))
    
    # Создаем таблицы связей для версий с авторами и ключевыми словами
    op.create_table('article_version_authors',
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['article_versions.id'], ),
        sa.PrimaryKeyConstraint('version_id', 'author_id')
    )
    
    op.create_table('article_version_keywords',
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['article_versions.id'], ),
        sa.PrimaryKeyConstraint('version_id', 'keyword_id')
    )
    
    # Миграция существующих данных: копируем file_url в manuscript_file_url
    op.execute("""
        UPDATE article_versions 
        SET manuscript_file_url = file_url 
        WHERE file_url IS NOT NULL
    """)
    
    # Обновляем существующие версии - копируем данные из статей
    op.execute("""
        UPDATE article_versions av
        SET 
            title_kz = a.title_kz,
            title_en = a.title_en,
            title_ru = a.title_ru,
            abstract_kz = a.abstract_kz,
            abstract_en = a.abstract_en,
            abstract_ru = a.abstract_ru,
            doi = a.doi,
            article_type = a.article_type,
            antiplagiarism_file_url = a.antiplagiarism_file_url,
            author_info_file_url = a.author_info_file_url,
            cover_letter_file_url = a.cover_letter_file_url,
            not_published_elsewhere = a.not_published_elsewhere,
            plagiarism_free = a.plagiarism_free,
            authors_agree = a.authors_agree,
            generative_ai_info = a.generative_ai_info
        FROM articles a
        WHERE av.article_id = a.id
    """)
    
    # Копируем авторов для существующих версий
    op.execute("""
        INSERT INTO article_version_authors (version_id, author_id)
        SELECT av.id, aa.author_id
        FROM article_versions av
        JOIN article_authors aa ON av.article_id = aa.article_id
    """)
    
    # Копируем ключевые слова для существующих версий
    op.execute("""
        INSERT INTO article_version_keywords (version_id, keyword_id)
        SELECT av.id, ak.keyword_id
        FROM article_versions av
        JOIN article_keywords ak ON av.article_id = ak.article_id
    """)
    
    # Делаем обязательными поля после миграции данных
    op.alter_column('article_versions', 'title_kz', nullable=False)
    op.alter_column('article_versions', 'title_en', nullable=False)
    op.alter_column('article_versions', 'title_ru', nullable=False)
    op.alter_column('article_versions', 'article_type', nullable=False)
    op.alter_column('article_versions', 'not_published_elsewhere', nullable=False, server_default='false')
    op.alter_column('article_versions', 'plagiarism_free', nullable=False, server_default='false')
    op.alter_column('article_versions', 'authors_agree', nullable=False, server_default='false')


def downgrade() -> None:
    # Удаляем таблицы связей
    op.drop_table('article_version_keywords')
    op.drop_table('article_version_authors')
    
    # Удаляем добавленные колонки
    op.drop_column('article_versions', 'generative_ai_info')
    op.drop_column('article_versions', 'authors_agree')
    op.drop_column('article_versions', 'plagiarism_free')
    op.drop_column('article_versions', 'not_published_elsewhere')
    op.drop_column('article_versions', 'cover_letter_file_url')
    op.drop_column('article_versions', 'author_info_file_url')
    op.drop_column('article_versions', 'antiplagiarism_file_url')
    op.drop_column('article_versions', 'manuscript_file_url')
    op.drop_column('article_versions', 'article_type')
    op.drop_column('article_versions', 'doi')
    op.drop_column('article_versions', 'abstract_ru')
    op.drop_column('article_versions', 'abstract_en')
    op.drop_column('article_versions', 'abstract_kz')
    op.drop_column('article_versions', 'title_ru')
    op.drop_column('article_versions', 'title_en')
    op.drop_column('article_versions', 'title_kz')
