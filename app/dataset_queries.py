from typing import Any


DATASET_LIST_FIELD = "TABLELIST"
DATASET_DETAIL_FIELD = "TABLELIST_by_pk"


def build_search_datasets_query() -> str:
    return """
    query SearchDatasets($keyword: String!, $limit: Int!) {
      TABLELIST(
        limit: $limit
        where: {
          _or: [
            { TITLE: { _ilike: $keyword } }
            { STATLIST: { STATNAME: { _ilike: $keyword } } }
            { STATLIST: { GOVLIST: { GOVNAME: { _ilike: $keyword } } } }
            { TABLE_TAGs: { TAG_NAME: { _ilike: $keyword } } }
          ]
        }
        order_by: [{ SURVEY_DATE: desc }]
      ) {
        STATDISPID
        TITLE
        STATCODE
        SURVEY_DATE
        YEAR_S
        YEAR_E
        CYCLE
        STATLIST {
          STATNAME
          GOVLIST {
            GOVCODE
            GOVNAME
          }
        }
      }
    }
    """


def build_get_dataset_query() -> str:
    return """
    query GetDataset($datasetId: String!) {
      TABLELIST_by_pk(STATDISPID: $datasetId) {
        STATDISPID
        TITLE
        STATCODE
        SURVEY_DATE
        YEAR_S
        YEAR_E
        CYCLE
        STATLIST {
          STATCODE
          STATNAME
          GOVCODE
          GOVLIST {
            GOVCODE
            GOVNAME
          }
          STAT_ATTRIBUTE_VALUEs {
            VALUE
            STAT_ATTRIBUTE {
              CODE
              NAME_JA
            }
          }
        }
        TABLE_DIMENSIONs {
          CLASS_NAME
        }
        TABLE_MEASUREs {
          NAME
        }
        TABLE_REGIONs {
          NAME
        }
        TABLE_REGIONTYPEs {
          REGIONTYPE
        }
        TABLE_TAGs {
          TAG_NAME
        }
        TABLE_TIMEs {
          YEAR
          MONTH
          TERM
          PERIOD_TYPE
        }
      }
    }
    """


def normalize_dataset_summary(raw: dict[str, Any]) -> dict[str, Any]:
    statlist = _object(raw.get("STATLIST"))
    govlist = _object(statlist.get("GOVLIST"))

    return {
        "id": raw.get("STATDISPID"),
        "title": raw.get("TITLE"),
        "description": _build_description(raw, statlist),
        "organization": govlist.get("GOVNAME"),
        "metadata": {
            "statcode": raw.get("STATCODE"),
            "statname": statlist.get("STATNAME"),
            "survey_date": raw.get("SURVEY_DATE"),
            "year_start": raw.get("YEAR_S"),
            "year_end": raw.get("YEAR_E"),
            "cycle": raw.get("CYCLE"),
            "govcode": govlist.get("GOVCODE"),
        },
    }


def normalize_dataset(raw: dict[str, Any]) -> dict[str, Any]:
    summary = normalize_dataset_summary(raw)
    statlist = _object(raw.get("STATLIST"))

    return {
        **summary,
        "metadata": {
            **summary["metadata"],
            "attributes": _normalize_attributes(statlist.get("STAT_ATTRIBUTE_VALUEs")),
            "dimensions": _names(raw.get("TABLE_DIMENSIONs"), "CLASS_NAME"),
            "measures": _names(raw.get("TABLE_MEASUREs"), "NAME"),
            "regions": _names(raw.get("TABLE_REGIONs"), "NAME"),
            "region_types": _names(raw.get("TABLE_REGIONTYPEs"), "REGIONTYPE"),
            "tags": _names(raw.get("TABLE_TAGs"), "TAG_NAME"),
            "times": _normalize_times(raw.get("TABLE_TIMEs")),
        },
        "raw": raw,
    }


def _build_description(raw: dict[str, Any], statlist: dict[str, Any]) -> str | None:
    parts = [
        statlist.get("STATNAME"),
        raw.get("SURVEY_DATE"),
        _year_range(raw.get("YEAR_S"), raw.get("YEAR_E")),
        raw.get("CYCLE"),
    ]
    values = [str(part) for part in parts if part not in (None, "")]
    return " / ".join(values) if values else None


def _year_range(start: Any, end: Any) -> str | None:
    if start is None and end is None:
        return None
    if start == end:
        return str(start)
    return f"{start or ''}-{end or ''}"


def _normalize_attributes(raw_values: Any) -> list[dict[str, Any]]:
    attributes = []
    for value in _list(raw_values):
        attribute = _object(value.get("STAT_ATTRIBUTE"))
        attributes.append(
            {
                "code": attribute.get("CODE"),
                "name": attribute.get("NAME_JA"),
                "value": value.get("VALUE"),
            }
        )
    return attributes


def _normalize_times(raw_values: Any) -> list[dict[str, Any]]:
    return [
        {
            "year": value.get("YEAR"),
            "month": value.get("MONTH"),
            "term": value.get("TERM"),
            "period_type": value.get("PERIOD_TYPE"),
        }
        for value in _list(raw_values)
    ]


def _names(raw_values: Any, field: str) -> list[Any]:
    return [value.get(field) for value in _list(raw_values) if value.get(field) is not None]


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
