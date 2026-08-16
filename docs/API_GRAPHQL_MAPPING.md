# MCP API と Hasura GraphQL 対応表

最終確認日: 2026-08-16

この文書は、`resume-mcp` が提供する MCP Tool と、Hasura GraphQL の `query_root` / 型 / 主なフィールドの対応を整理したものです。`resume-mcp` は read-only の薄いラッパーなので、MCP Tool は Hasura の `query` のみを呼び出し、`mutation` は使用しません。

## 現在の MCP Tool

| MCP Tool | 目的 | 対応する Hasura query_root | 主キー/識別子 | 主な返却フィールド | 実装状況 |
|---|---|---|---|---|---|
| `search_datasets` | キーワードでデータセット候補を検索する | `TABLELIST` | `STATDISPID` | `STATDISPID`, `TITLE`, `STATCODE`, `SURVEY_DATE`, `YEAR_S`, `YEAR_E`, `CYCLE`, `STATLIST.STATNAME` | 実装済み |
| `get_dataset` | データセット ID の詳細を取得する | `TABLELIST_by_pk` | `STATDISPID` | `TABLELIST` 本体、`STATLIST`, dimensions, measures, regions, tags, times | 実装済み |

## 今後追加予定の MCP Tool

| MCP Tool | 目的 | 対応する Hasura query_root | 主キー/識別子 | 主な返却フィールド | 備考 |
|---|---|---|---|---|---|
| `get_metadata` | データセットのメタ情報を取得する | `TABLELIST_by_pk`, `STATLIST_by_pk`, `STAT_ATTRIBUTE_VALUES` | `STATDISPID`, `STATCODE` | 統計名、府省、属性値、タグ、期間、周期 | `TABLELIST.STATLIST` 経由で統計情報を取れる |
| `get_dimension_items` | データセットで利用できる次元と項目を取得する | `TABLE_DIMENSION`, `DIMENSIONLIST`, `DIMENSION_ITEM` | `STATDISPID`, `CLASS_NAME` | `CLASS_NAME`, `DIMENSION_ITEMs.NAME` | `TABLE_DIMENSION` から対象テーブルの次元へ絞る |
| `get_data` | 実データを取得する | 未確認 | 未確認 | 未確認 | 現在の introspection では値データ用テーブルが見えていないため追加確認が必要 |

## Hasura query_root 一覧

今回確認できた主な query_root は以下です。

| query_root | 用途の推定 | by_pk |
|---|---|---|
| `TABLELIST` | データセット/表一覧 | `TABLELIST_by_pk(STATDISPID)` |
| `STATLIST` | 統計一覧 | `STATLIST_by_pk(STATCODE)` |
| `GOVLIST` | 政府/府省一覧 | `GOVLIST_by_pk(GOVCODE)` |
| `STAT_ATTRIBUTE` | 統計属性マスタ | `STAT_ATTRIBUTE_by_pk(ID)` |
| `STAT_ATTRIBUTE_VALUES` | 統計属性値 | `STAT_ATTRIBUTE_VALUES_by_pk(ID)` |
| `DIMENSIONLIST` | 次元マスタ | `DIMENSIONLIST_by_pk(CLASS_NAME)` |
| `DIMENSION_ITEM` | 次元項目 | `DIMENSION_ITEM_by_pk(CLASS_NAME, NAME)` |
| `TABLE_DIMENSION` | 表と次元の対応 | `TABLE_DIMENSION_by_pk(CLASS_NAME, STATDISPID)` |
| `MEASURELIST` | 単位/測度マスタ | `MEASURELIST_by_pk(NAME)` |
| `TABLE_MEASURE` | 表と測度の対応 | `TABLE_MEASURE_by_pk(NAME, STATDISPID)` |
| `REGIONLIST` | 地域マスタ | `REGIONLIST_by_pk(NAME)` |
| `TABLE_REGION` | 表と地域の対応 | `TABLE_REGION_by_pk(NAME, STATDISPID)` |
| `TABLE_REGIONTYPE` | 表と地域種別の対応 | `TABLE_REGIONTYPE_by_pk(REGIONTYPE, STATDISPID)` |
| `TABLE_TIME` | 表と時点の対応 | `TABLE_TIME_by_pk(MONTH, PERIOD_TYPE, STATDISPID, TERM, YEAR)` |
| `TAGLIST` | タグマスタ | `TAGLIST_by_pk(TAG_NAME)` |
| `TABLE_TAG` | 表とタグの対応 | `TABLE_TAG_by_pk(STATDISPID, TAG_NAME)` |

## 主要型とフィールド

### `TABLELIST`

データセット/表の中心テーブルです。MCP の `dataset_id` は `STATDISPID` を使うのが自然です。

| フィールド | 意味の推定 |
|---|---|
| `STATDISPID` | データセット/表 ID |
| `STATCODE` | 統計コード |
| `TITLE` | 表タイトル |
| `SURVEY_DATE` | 調査日 |
| `YEAR_S` | 開始年 |
| `YEAR_E` | 終了年 |
| `CYCLE` | 周期 |
| `STATLIST` | 統計情報へのリレーション |
| `TABLE_DIMENSIONs` | 次元へのリレーション |
| `TABLE_MEASUREs` | 測度へのリレーション |
| `TABLE_REGIONs` | 地域へのリレーション |
| `TABLE_REGIONTYPEs` | 地域種別へのリレーション |
| `TABLE_TAGs` | タグへのリレーション |
| `TABLE_TIMEs` | 時点へのリレーション |

### `STATLIST`

統計そのものの情報です。

| フィールド | 意味の推定 |
|---|---|
| `STATCODE` | 統計コード |
| `STATNAME` | 統計名 |
| `GOVCODE` | 政府/府省コード |
| `GOVLIST` | 政府/府省情報へのリレーション |
| `TABLELISTs` | 対象統計に属する表一覧 |
| `STAT_ATTRIBUTE_VALUEs` | 統計属性値 |

## GraphQL 対応案

### `search_datasets`

`TABLELIST` を検索し、MCP では LLM が扱いやすい `id`, `title`, `description`, `organization` へ整形します。

```graphql
query SearchDatasets($keyword: String!, $limit: Int!) {
  TABLELIST(
    limit: $limit
    where: {
      _or: [
        { TITLE: { _ilike: $keyword } }
        { STATLIST: { STATNAME: { _ilike: $keyword } } }
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
      }
    }
  }
}
```

MCP 返却マッピング案:

| MCP field | GraphQL field |
|---|---|
| `id` | `STATDISPID` |
| `title` | `TITLE` |
| `description` | `STATLIST.STATNAME`, `SURVEY_DATE`, `YEAR_S`, `YEAR_E`, `CYCLE` から生成 |
| `organization` | `STATLIST.GOVLIST` から生成。ただし府省名フィールドは追加確認が必要 |
| `metadata.statcode` | `STATCODE` |

### `get_dataset`

`STATDISPID` で 1 件を取得します。Hasura の `TABLELIST_by_pk` が使えるため、こちらが明快です。

```graphql
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
```

### `get_dimension_items`

対象データセットが使う `CLASS_NAME` を `TABLE_DIMENSION` から取り、その `DIMENSION_ITEMs` を返します。

```graphql
query GetDimensionItems($datasetId: String!) {
  TABLE_DIMENSION(where: { STATDISPID: { _eq: $datasetId } }) {
    CLASS_NAME
    DIMENSIONLIST {
      CLASS_NAME
      DIMENSION_ITEMs {
        NAME
      }
    }
  }
}
```

### `get_metadata`

`get_dataset` の軽量版として `TABLELIST_by_pk` と `STATLIST` 周辺だけを返します。

```graphql
query GetMetadata($datasetId: String!) {
  TABLELIST_by_pk(STATDISPID: $datasetId) {
    STATDISPID
    TITLE
    STATCODE
    SURVEY_DATE
    YEAR_S
    YEAR_E
    CYCLE
    STATLIST {
      STATNAME
      GOVCODE
      STAT_ATTRIBUTE_VALUEs {
        VALUE
        STAT_ATTRIBUTE {
          CODE
          NAME_JA
        }
      }
    }
    TABLE_TAGs {
      TAG_NAME
    }
  }
}
```

## 未確認事項

- `GOVLIST` に府省名/組織名に相当するフィールドが存在するか。
- 実データ本体に相当する query_root が現在の role で公開されているか。
- `search_datasets` の検索対象に `TAG_NAME` や属性値も含めるか。
- `dataset_id` を `STATDISPID` として正式採用してよいか。
