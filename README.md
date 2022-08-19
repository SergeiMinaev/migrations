# migrations
Simplest DB migration manager possible

#### Not production ready at all. Use at your own risk

# How it works?

#### Do not create VCS inside of another VCS

Sometimes it's required to write migrations manually. In this case I hate when it comes to millions of small ups and downs.
In addition "down" migrations are never used. One simple solution is to write only "up" migrations and store them in a single 'migrations.sql' file.
Single file for migrations allows you to see recent changes which leads to better understanding of DB schema.
You don't need to store full list of migrations in this file. Only recent ones are required.
Oldest migrations will always be available via git anyway.

My personal preference is to have some sort of text files with actual scheme description.
I think it's nice to have an opportunity to quickly view the current table schema and refresh your memory for a bit.
Of course you can use psql shell for that but I find it not very ergonomic.
Text files are better for that because of easy access and syntax highlighting.
To solve this, migrations.py script can optionally dump per-table schema and save it to schema/{table}.sql.

#### The logic is simple:
1) mv {example.,}migrations_settings.py and specify DBNAME and other settings.
2) Write some migrations in migrations.sql file. Migrations should be separated by additional line break.
3) Run ./migrations.py . The script will enumerate new migrations and will apply them.
4) Number of last applied migration will be stored in `public.last_migration_n()` function.
Additionally it will appeared in migrations.sql at the first line.
5) Optionally per-table schema will be dumped to schema/{table}.sql files and full DB schema - to schema/schema.sql .
6) When you want to create new migrations, just add it to migrations.sql and run ./migrations.py again.
7) If you need to create an empty DB for tests, use schema/schema.sql . Older versions are available via git.
8) Of course this approach will fit only small projects. 
9) No dependencies. You only need python and psql/pg_dump.

Suggested directory structure:
```
./project/db/migrations/migrations.py
./project/db/migrations.sql
./project/db/scheme/{table}.sql
```
