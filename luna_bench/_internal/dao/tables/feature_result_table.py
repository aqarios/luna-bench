from peewee import AutoField, CharField, ForeignKeyField, IntegerField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus

from .feature_table import FeatureTable
from .model_metadata_table import ModelMetadataTable


class FeatureResultTable(BaseTable):
    id = AutoField(primary_key=True)

    processing_time_ms = IntegerField(null=False)

    status = CharField(max_length=16, choices=[(s.value, s.name) for s in JobStatus])
    error = CharField(max_length=255, null=True)

    result_data = JSONField(  # type: ignore[no-untyped-call]
        json_dumps=lambda x: None if x is None else x.model_dump_json(),
        json_loads=lambda x: None if x is None else ArbitraryDataDomain.model_validate_json(x),
        null=True,
    )

    model_metadata = ForeignKeyField(ModelMetadataTable, backref="feature_results", on_delete="CASCADE")
    feature = ForeignKeyField(FeatureTable, backref="results", on_delete="CASCADE")

    class Meta:
        indexes = ((("model_metadata", "feature"), True),)
