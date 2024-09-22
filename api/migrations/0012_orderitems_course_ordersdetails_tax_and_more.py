# Generated by Django 4.2.7 on 2024-09-18 17:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_cartelements_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitems',
            name='course',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='api.course'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ordersdetails',
            name='tax',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
        migrations.AlterUniqueTogether(
            name='orderitems',
            unique_together={('course', 'order')},
        ),
    ]
