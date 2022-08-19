#LAST_APPLIED: 2

# 1
select 'I am already applied';

# 2
select 'I am already applied too';

select 'This migration is not applied yet.'
select 'because the last applied migration number is set to 2';

select 'This migration is not applied too.'
select 'Migrations are separated by empty line.';
select 'So this three lines will be treated as a single migration.';
