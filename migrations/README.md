# Database Migrations

This project uses Flask-Migrate (Alembic) for database migrations.

## Migration Commands

Initialize migrations (first time only):

```
flask db init
```

Create a new migration after model changes:

```
flask db migrate -m "Description of changes"
```

Apply migrations to the database:

```
flask db upgrade
```

Downgrade to a previous migration:

```
flask db downgrade
```

View migration history:

```
flask db history
```

Show current migration version:

```
flask db current
```

## Manual Migrations

If auto-detection doesn't capture your schema changes, you can create a manual migration:

1. Create a blank revision:

   ```
   flask db revision -m "Description of changes"
   ```

2. Edit the generated file in the migrations/versions folder to add the schema changes:

   - Define changes in the `upgrade()` function
   - Define how to revert changes in the `downgrade()` function

3. Apply the changes:
   ```
   flask db upgrade
   ```

## Notes

- Always commit migration files to version control
- Review auto-generated migrations before applying them
- For SQLite databases, some operations require special handling using the `render_as_batch=True` option (already configured)
