## 目的と優先順位

- **最優先: 正しさの担保とAPI互換**
  - ベースURLの二重付与や同期/非同期の取り扱い不整合などの致命的不具合を是正
  - 既存パブリックAPI(クラス名/メソッド名)の後方互換を維持しつつ内部実装を置き換え
- **次点: 設計の単純化と型安全性の向上**
  - HTTP層の一元化、例外・ロギング方針の統一、モデルの明確化
- **その後: 性能・品質の継続改善**
  - セッション再利用、レート制御、リトライ、CI/テスト整備、ドキュメント整備

---

## 現状の主な問題点(要修正リスト)

- **URL組み立ての不整合**
  - `ApiClientBase.get/post` が `self.base_url + url` を行うのに、各メソッド側で `f"{self.base_url}/..."` を渡しており、結果としてベースURLが二重付与される。
- **同期/非同期のAPI設計不整合**
  - `make_request` が `self.is_async` を見てコルーチンを返す設計のため、同期クライアントからも await すべき値が返りうる。
  - `manager.py` 側で `self.client.set_async`(メソッド) を真偽値として誤用している箇所多数。
- **レスポンス処理の不整合**
  - `get_schedules_by_change_date` で `self.get(...)` の戻り値(すでにJSON/dict)に対してさらに `response.json()` を呼んでいる。
  - `make_request_async` で `response_json['Errors']` を前提にしており、キー非存在時に `KeyError` の可能性。
- **シリアライズの欠落**
  - `AddPersonRequest` などのリクエストオブジェクトを `requests` の `json=` に直接渡しており、JSONシリアライズ不能(クラス→dict変換がない)。
  - `SetSchedulesForPersonOptions` で `options.datePeriod.startDate` のように dict をオブジェクト属性として参照している等、モデル仕様不一致。
- **依存関係とインポート設計**
  - `__init__.py` で `PeopleManager` などをトップレベル公開しており、`pandas/tqdm` 未インストール環境でも import だけで失敗しうる。
- **ロギング/例外方針の曖昧さ**
  - 例外を `logger.error` して `None` を返すなど、呼び出し側でのエラーハンドリングが困難。
- **データ処理の堅牢性**
  - `PeopleManager`/`ScheduleManager` の DataFrame マージ前提の列存在チェックが弱い。空DataFrameやキー欠落時のエラー可能性。
- **レート/リトライ**
  - 一部で指数バックオフがあるが、HTTP429/5xx等の扱いが統一されていない。`aiohttp` セッションも使い捨て。

---

## あるべき設計(概要)

- **モジュール分割**
  - `calabrio_py/http/`:
    - `base.py`: 共通HTTPクライアント(タイムアウト/リトライ/セッション/ヘッダ/URL組立)
    - `sync.py`: 同期用実装
    - `async.py`: 非同期用実装
  - `calabrio_py/models/`:
    - `requests.py`/`responses.py`/`types.py`: dataclassベースのモデルと `to_payload()` 変換
    - CamelCase 変換ユーティリティ/日付変換ユーティリティ
  - `calabrio_py/endpoints/`:
    - `command.py`/`query.py`: エンドポイント群を責務単位で整理
  - `calabrio_py/managers/`:
    - `people.py`/`accounts.py`/`schedule.py`: Manager群(依存: `pandas` を extras 扱い)
  - 既存の `ApiClient`/`AsyncApiClient` は後方互換レイヤーとして残し、内部で新実装に委譲

- **URLとHTTP層**
  - `HttpClientBase` に `base_url`, `default_headers`, `timeout`, `retry_policy` を集約
  - エンドポイント実装からは常に「相対パス」を渡す(例: `POST("/command/AddPerson", payload)`)。`HttpClient` 側で `urljoin` により組み立て
  - 同期/非同期で明確にクラスを分ける(戻り値も `dict` を直接返す)。同期がコルーチンを返すことはない
  - `aiohttp` は `ClientSession` を使い回す(コンテキスト管理 or 明示クローズ API)

- **シリアライズ/デシリアライズ**
  - dataclass モデルで API の CamelCase キーに合わせたエクスポートを提供
  - 例: `AddPersonRequest.to_payload()` が `Dict[str, Any]` を返す。`datetime` は ISO8601 文字列に統一
  - 受信レスポンスは基本 `dict` とし、必要に応じて軽量モデル化

- **例外/ロギング方針**
  - 既定: HTTPエラー時は `CalabrioApiError`(status, body, headers含む) を送出
  - APIボディに `Errors` があれば `CalabrioApiError` を送出(オプトアウト可能な `raise_on_api_errors`)
  - ログは `calabrio_py` 名前空間で統一、APIキーは伏字

- **Manager層**
  - すべて `async` メソッドを基本とし、同期ラッパー(必要なもののみ)を提供
  - 依存の `pandas`/`tqdm` を extras に移動し、トップレベル import で依存しない設計
  - DataFrame マージ時に列存在チェック/空チェックを徹底
  - 並列取得はセマフォで制御し、`asyncio.gather(..., return_exceptions=True)` を活用

- **互換性**
  - 既存の `ApiClient`, `AsyncApiClient` のパブリックメソッド名/引数は維持
  - 内部で相対URLに置換し、`to_payload()` を使ってシリアライズ
  - 旧挙動(エラーでも `None` を返す)は非推奨とし、`suppress_errors=True` オプションでのみ許容

---

## 具体的なリファクタリング計画(段階的)

### Phase 0: ガードレール(小修正・バグ修正のみ)

- `ApiClientBase.get/post` のURL仕様を明確化
  - 暫定対応として、各エンドポイントで渡すURLを相対パスに統一(`/command/...`, `/query/...`)
- `get_schedules_by_change_date` の `response.json()` を削除し、`dict` を直接返す
- `make_request_async` の `Errors` 参照を `response_json.get("Errors", [])` に
- `AddPersonRequest` 等のリクエストオブジェクトを一時的に `dict` で受ける(呼出側で `dict` を渡す) or 簡易 `to_payload()` を実装
- `manager.py` の `self.client.set_async` 判定を `getattr(self.client, "is_async", False)` に修正
- ログにAPIキーを出さない

### Phase 1: HTTP層の抽象化

- `http/base.py`, `http/sync.py`, `http/async.py` を追加
  - タイムアウト、ヘッダ、セッション再利用、リトライ(429/5xx)を統一実装
- 既存 `ApiClientBase` は新HTTP層へ委譲

### Phase 2: モデルの整備とシリアライズ

- `models/requests.py` に主要リクエスト(dataclass)を整備
  - `AddPersonRequest`, `ExternalMeeting`, `SetSchedulesForPersonOptions` など
  - `to_payload()` 実装、CamelCaseキー変換ユーティリティ
- エンドポイントは `to_payload()` を通じて送信

### Phase 3: エンドポイント再編成

- `endpoints/command.py`/`endpoints/query.py` に整理(責務別)
- `ApiClient`/`AsyncApiClient` は後方互換の薄いFacadeに変更

### Phase 4: Manager層の堅牢化/依存の分離

- `managers/people.py`/`accounts.py`/`schedule.py` に分割
- すべて `async` ベースへ寄せ、必要時のみ同期ラッパーを提供
- 列存在チェック・空集合時の分岐・例外伝播/抑止方針の統一
- セマフォ/バックオフ/並列数のデフォルト最適化

### Phase 5: 依存関係/パッケージング

- `pyproject.toml` への移行、`setuptools`/`wheel`/`build`
- extras: `calabrio_py[pandas]` で `pandas`, `tqdm`
- `__init__.py` で重依存をトップレベル公開しない(遅延インポート)

### Phase 6: ロギング/エラー/設定

- 例外階層: `CalabrioError`/`CalabrioHttpError`/`CalabrioApiError`
- 可観測性: リクエストID/X-RateLimit系ヘッダのログ出力
- 設定オブジェクト: タイムアウト/リトライ/レートリミット/raise_on_api_errors

### Phase 7: 品質(型/CI/テスト/Docs)

- 型付け強化と `mypy --strict` 通過
- `ruff`/`black`/`isort` 導入、`pre-commit`
- ユニットテスト: `httpx`/`aiohttp` mocking、簡易VCR
- ドキュメント: READMEの整備、APIリファレンス自動生成

---

## 修正対象の代表例(抜粋)

- URL二重付与の是正:
  - 例) `get_all_commands` を `return self.get("/command")` にする
- `get_schedules_by_change_date`:
  - `response = self.get(url, params=params)` → そのまま `dict` を返す
- `AddPersonRequest`:
  - dataclass化 + `to_payload()` 実装、`client.add_person(add_person_request.to_payload())`
- `SetSchedulesForPersonOptions`:
  - dict/属性の不整合を解消。`datePeriod` は dict なら `datePeriod["StartDate"]`、モデル化するなら `options.date_period.start_date`
- `manager.py`:
  - `if self.client.set_async:` を `if getattr(self.client, "is_async", False):` に
  - DataFrame マージの堅牢化(列存在チェック、`empty` 分岐)

---

## 互換性ポリシー

- Minor バージョン内では既存メソッドシグネチャを維持
- 例外送出への変更点はデフォルト抑止(`suppress_errors=True`)で互換提供
- Deprecated 警告を段階導入し、メジャーリリースでクリーンアップ

---

## マイルストーン/タスク一覧

- [ ] Phase 0: クリティカルバグ修正(PR: hotfix)
  - [ ] 相対URLへ統一(全メソッド)
  - [ ] `get_schedules_by_change_date` の戻り値修正
  - [ ] `Errors` 安全参照
  - [ ] `manager.py` の async 判定修正
  - [ ] APIキーのログマスキング
- [ ] Phase 1: HTTP層抽象化
- [ ] Phase 2: モデル整備/シリアライズ
- [ ] Phase 3: エンドポイント再編
- [ ] Phase 4: Manager堅牢化/依存分離
- [ ] Phase 5: パッケージング/Extras
- [ ] Phase 6: ログ/例外/設定
- [ ] Phase 7: 型/CI/テスト/Docs

---

## TDD方針とテスト計画

- テストフレームワーク: `pytest` + `pytest-asyncio`
- モック戦略:
  - 同期HTTPは `requests.request` を monkeypatch してURL/ヘッダ/ペイロードを検証
  - 非同期HTTPは `aiohttp.ClientSession` をモックして `json()` 戻り値や `raise_for_status()` の動きを検証
- 最初に落ちるべきテスト(Phase 0 対応範囲):
  - `ApiClient` が Authorization ヘッダと正しいURL(ベースURL + 相対パス)で呼び出す
  - 渡されたURLが絶対パスの場合でもベースURLの二重付与を行わない
  - `get_schedules_by_change_date` が `dict` を返し `.json()` を二重に呼ばない
  - 非同期の `make_request_async` が `Errors` キー非存在でも例外にならない
  - `add_person` に `dict` を渡すとそのまま `json` ペイロードとして送信される

- 追加テスト(後続Phase):
  - dataclass リクエストモデルの `to_payload()` シリアライズ
  - 例外ポリシー(HTTPエラー/ボディErrors)の送出と抑止フラグ
  - Manager層の堅牢な結合テスト(モッククライアントでのDataFrameマージの列存在/空ケース)

---

## 参考: 推奨インターフェース例(抜粋)

```python
# 同期
client = ApiClient(base_url, api_key, timeout=30, retry_policy=RetryPolicy())
client.get_all_business_units()

# 非同期
async with AsyncApiClient(base_url, api_key, timeout=30) as client:
    await client.get_all_business_units()

# リクエストモデル
person = AddPersonRequest(
    time_zone_id="UTC",
    business_unit_id="...",
    first_name="Taro",
    last_name="Yamada",
    start_date=date(2025,1,1),
    email="taro@example.com",
    employment_number="E0001",
    application_logon="taro",
    identity="...",
    team_id="...",
    contract_id="...",
    contract_schedule_id="...",
    part_time_percentage_id="...",
    role_ids=["..."]
)
await client.add_person(person.to_payload())
```

---

## 期待効果

- ベースURL/非同期取り扱いの不具合解消による実用性の回復
- 例外/ログの標準化による運用容易性向上
- モデル/型導入による改修容易性・保守性の大幅改善
- Manager層の堅牢化と依存分離による軽量利用/高度利用の両立
