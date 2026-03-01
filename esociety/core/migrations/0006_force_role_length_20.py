from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_user_mobile_number'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_user ALTER COLUMN role TYPE varchar(20);",
            reverse_sql="ALTER TABLE core_user ALTER COLUMN role TYPE varchar(10);",
        ),
    ]
