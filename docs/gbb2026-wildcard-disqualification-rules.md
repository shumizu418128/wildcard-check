# GBB 2026 Wildcard 失格になりうるルール

出典: [GBB 2026 Wildcard Competition](https://swissbeatbox.com/newsfeed/gbb-2026-wildcard-competition/)

取得日: 2026-09-29

このファイルは、上記記事だけを根拠に、申請が不受理になる条件と、失格（または失格に至りうる警告）になる条件を書き出したもの。後続の要件定義でルールIDを参照する。

## 範囲

対象カテゴリは、この記事が扱う World League Wildcard のみ。

- Solo
- Loopstation
- Tag Team
- Crew
- Producer Showcase

次は別記事のため、ここには含めない。

- Showcase Wildcard（Solo / Loopstation）。記事内で「別記事で公開する」とされている
- Studio Wildcard Competition。[別記事](https://swissbeatbox.com/newsfeed/gbb-2026-studio-competition-wildcard-rules/)がある
- チケット規約や会場規則（[gbb.swissbeatbox.com/en/rules](https://gbb.swissbeatbox.com/en/rules)）
- 補欠繰り上げ、Second League、Challenger Series、Comeback Wildcard の選出手順。動画の合否ではなく、順位確定後の枠の扱いである

## 結果の区分

記事は「失格」以外にも、不受理・警告・順位ペナルティを使い分けている。ツール化では混ぜない。

| 区分 | 意味 | 記事上の帰結 |
| --- | --- | --- |
| `reject` | 申請そのものを受け付けない、または権利を放棄する | 審査対象にならない |
| `dq` | 失格。調査のあと確定するものを含む | 次点に回る、または大会から外れる |
| `red` | 即レッドカード。即失格と同じ | 即失格。最小で GBB から1年 |
| `warn` | 警告。単体では失格ではない | 警告2回でイエロー。イエロー保持中の追加警告はレッド＝失格 |
| `penalty` | 順位を下げる。失格ではない | 超過・不足した秒数ぶん最終順位が下がる |
| `admin` | 動画内容ではなく、合格後の手続きや年齢で失格になる | 次の有資格者に交代 |

ゼロトレランスの宣言は、形式・長さ・音声仕様・命名・情報不足などの技術要件を満たさない提出を、例外なく自動失格しうると書いている。個別ルールが「警告」や「順位ペナルティ」と書いている項目とは衝突する。衝突箇所は各ルールの「注記」に残す。

## 総則

### GEN-ZERO ゼロトレランス

区分: `dq`（自動失格になりうる）

GBB26 では厳格なゼロトレランスを適用する。形式、長さ、音声仕様、命名、不足情報、その他の技術要件を満たさない提出は、自動的に失格になりうる。例外、再提出、不服申立てはない。

原文: "Any submission that fails to meet the stated criteria, whether related to format, duration, audio specifications, naming conventions, missing information, or other technical requirements, may be disqualified automatically. There are no exceptions, no second attempts, and no appeals."

注記: 長さについては `TIME-PENALTY` が「秒数ぶん順位を下げる」と書いており、この総則と文言が食い違う。どちらを優先するかは未確定。

### GEN-YOUTUBE 通常動画として公開する

区分: `reject` / ゼロトレランス上は `dq` になりうる

参加するには、Wildcard を YouTube の通常動画としてアップロードし（Shorts は不可）、Swissbeatbox の提出フォームにリンクを載せる。

原文: "participants must upload their wildcards to YouTube as a normal video (no shorts are allowed)"

## 全カテゴリ共通（動画・提出物）

### SUB-ONCE 提出は1回だけ

区分: `reject`

- Wildcard の登録は1回だけ。
- 登録期間中に後から新しい動画を上げても、審査されるのは最初のアップロードだけ。
- 最初のアップロードを削除して差し替えると、Wildcard の権利を放棄し、大会に受け付けられない。
- 後からの編集・再アップロードはできない。上げる時点で最終版である必要がある。

### SUB-RAW 生ファイルの提出

区分: `reject`（提出時に無い場合）。調査で正当性を確認できない場合は `dq`

提出時に、次をコピーで出す。

- 生の音声（未加工の原音）
- 生の動画（カメラ音声を含む）

Loopstation、Tag Team、Crew は、収録している様子の画面キャプチャも追加で必要。Solo の箇条書きには画面キャプチャは含まれない。

生の音声、画面キャプチャ、生の動画のいずれかが提出時に無いと、申請は受け付けられない。

リンクの条件:

- 開いたリンクであること
- アクセス申請が不要であること
- 有効期限で閉じないこと
- 2026-09-24 までアクセスできること。それ以降は参加者が無効化してよい

調査時に正当性が確認できない例として、不正な加工とリップシンクが挙がっている。その場合は失格。手元に残すもの:

- 生音声
- 生カメラ
- ミックスしたプロジェクトファイル（自分でミックスしていない場合、エンジニアがコピーを保持する）
- 収録の画面キャプチャ

カテゴリ別の本文でも、音声セッションファイルを調査のために消さないよう繰り返し書かれている。勝者に加え、順位の次点も音声を検査する（Solo / Loopstation / Tag Team に明記）。

### INTRO-REQUIRED 冒頭の自己紹介

区分: 自己紹介が無い場合は `warn`。別撮りは `dq`

動画の冒頭で、次の要素を話す。

> My name is [ARTIST NAME], and this is my [CATEGORY] wildcard for the GBB2026 World League.

必須要素は NAME、`GBB2026 World League`、カテゴリ。これ以外の言葉を足してよいが、必須要素は省けない。例示カテゴリは Solo、Loop など。

自己紹介が動画の冒頭に無い場合は、追加調査の対象になり、ルール違反として警告を受ける。この段落は即失格とは書いていない。

### INTRO-SAME-TAKE 自己紹介は本編と同じ収録

区分: `dq`（調査後）

自己紹介は、Wildcard 本編と同一の環境・同一のタイミングで収録する。別撮りのイントロは動画に統合されていないものとして扱われ、調査のあと Wildcard は失格になる。

原文: "The introduction MUST BE RECORDED in the SAME SETTING ENVIRONMENT and at the SAME TIME when the wildcard is being recorded. A separate intro recording will be treated as NON INTEGRATED part of the video and your wildcard will be disqualified after further investigation."

### TITLE-FORMAT 動画タイトル

区分: ゼロトレランスの naming conventions により `dq` になりうる。タイトル節自体は「must」とだけ書き、単独の失格文はない

次のいずれか。

- `[ARTIST NAME] – GBB26: World League [CATEGORY] Wildcard`
- `Grand Beatbox Battle 2026: World League [CATEGORY] Wildcard`

例: `Pepouni – GBB26: World League Solo Wildcard`

### VIS-FACE 顔が常に判別できる

区分: 禁止。即失格とは書かれていない。ゼロトレランスの技術要件、および後述のレッドカード文の射程に入りうる（`CARD-SCOPE`）

Solo と Tag Team は、スマホから別マイクのプロ機材まで収録方法は自由。そのうえで次を満たす。

- カメラに明確かつ全身ではなく、人物がはっきり全体として映る（"clearly and fully visible"）
- マスク等で顔の一部でも隠さない
- 顔を完全に認識できる照明にする
- 暗すぎる、または白飛びした環境は不可
- 参加者は、顔が映った生動画を送る
- 完成動画にエフェクトやビジュアルを使ってよい。ただし顔は見える状態を保ち、エフェクト無しの生データを送る。整合性は検査される
- 生データと編集後の両方で、本人が映り、生の音が聞こえる状態を、公式の検査が終わるまで保持する責任は参加者にある

Tag Team は、各メンバーが常時映っていること（他カテゴリと同様）。

Crew は、各メンバーが常時映っていること。

### SYNC-LIVE 映像と音声は同時収録。リップシンク禁止

区分: `dq`（正当性が確認できない場合）。禁止事項としての明記あり

リップシンク、その他の映像テクニックは禁止。全カテゴリで、映像と音声は同時に収録する。

正当性が確認できない例にリップシンクが含まれる。確認できない場合は失格。

Crew はこれより厳しい。`CREW-SIMUL` を参照。

### AUDIO-PROCESS 許可される音声加工と即レッドカード

区分: `red`（即失格）。検出された無許可加工は `dq`

加工はポストプロダクションでのみ。収録そのものは生である。

許可されるのは、録音全体に一様にかける次のものだけ。

- 基本的なダイナミクス（コンプレッション）
- EQ
- リバーブ

禁止:

- キックとスネアで EQ やコンプレッションを変えるような、自動・部分ごとの処理
- ディストーション
- ディレイ
- その他のタイムベース、または周波数を歪ませるエフェクト

原文: "You may process your audio recording with basic dynamic (compression), EQ plugins, and reverb – this must be done in post; the recording itself must be raw. Automated processing, such as EQing and compressing the kick and snare differently, is not allowed; the entire recording must be processed uniformly. Also, distortion, delay, or any other time-based or frequency distortion effects are strictly forbidden"

この規則に違反すると即レッドカード。無許可の加工は検出され、Wildcard 大会から失格になる、と続く。

原文: "Breaching these rules result in an immediate red card!"

原文: "if you attempt to use any unauthorised processing methods without our prior knowledge, we will detect it, and you will be disqualified from the wildcard competition."

注記: Producer Showcase は "Mix/Mastering restrictions: no restrictions" と書いてあり、この音声加工制限の対象外に読める。`PROD-MIX` を参照。

### CARD-SCOPE レッドカード文がどの箇条までを指すか

区分: 未確定

"Breaching these rules result in an immediate red card!" は、音声加工の箇条の直後にある。直後の文は無許可の音声加工に限定して失格と書いている。一方 "these rules" は、同じ「Allowed Recording Setup and Raw Files」節の可視性・同時収録・Crew 収録・Loopstation のステレオ制限まで含む読みもできる。記事は射程を定義していない。

## カテゴリ別

### Solo

#### SOLO-TIME 演奏時間

区分: `penalty`（`TIME-PENALTY`）

ビートボックス時間は 2:00、許容は ±10秒。つまり 1:50 以上 2:10 以下。イントロとアウトロは含めない。

#### SOLO-RAW 提出物

区分: `reject` / 検査不能なら `dq`（`SUB-RAW`）

未加工の生音声と、カメラ音声付きのメインカメラ生データを提出する。セッションファイルは消さない。勝者および次点の音声を検査する。

### Loopstation

#### LOOP-TIME 演奏時間

区分: `penalty` と読める。文言は崩れており、即時ペナルティ発動とも取れる。失格とは書かれていない

演奏時間は 3:00 以上 3:30 以下。このカテゴリに ±10秒は無い。範囲の外は、一般ペナルティ規則が直ちに発動する、という趣旨の文がある。

原文: "Beatbox time: 3 minutes – 3 minutes and 30 seconds. (no +/- in this category allowed, being over or under the allowed time leads directly to immediate triggers of or general penalty rule)."

共通ルール側も、範囲が指定される例として Loopstation の 3:00–3:30 を挙げ、±10秒の例から外している。範囲外の秒数ペナルティは `TIME-PENALTY`。

#### LOOP-DEVICE 使用機材

区分: 禁止。明示の失格文は無い。ゼロトレランスと整合性検査の対象になりうる

- メインの Loopstation は1台
- 許可機材は BOSS RC-505 MKI と BOSS RC-505 MKII のみ
- それ以外の機材は不可。MIDI 機材を含む
- 機材内部の追加配線（出力を入力へ戻す等）は可。ケーブルは機材に数えない

#### LOOP-SOUND 音源

区分: 禁止。メトロノームの観客への可聴は "STRICTLY FORBIDDEN"

- 音はすべて、マイクで拾った人の声または身体から、その場で生成する
- プリレコーデッドのサンプルは禁止
- メトロノームを観客に聞こえる状態で使うことは厳禁
- 接続するマイクは1本
- 出力は1組のステレオに限る。複数の出力信号は不可
- マルチチャンネル録音は不可。録音できるのはステレオの L/R 出力のみ（共通の収録セットアップ節）

#### LOOP-CAMERA 画角と提出物

区分: `reject` / 検査不能なら `dq`

- セットアップ全体が画角に入ること。特に Loopstation の背面が入り、セットアップと収録過程を確認できること
- 生の未加工音声、カメラ音声付きのメインカメラ生データ、収録中の画面キャプチャ
- セッションファイルは消さない
- 勝者および次点の音声を検査する

### Tag Team

#### TAG-TIME 演奏時間

区分: `penalty`

2:00、許容 ±10秒。1:50 以上 2:10 以下。

#### TAG-VIS メンバーの可視

区分: `VIS-FACE` と同じ

各メンバーが常時映っている。

#### TAG-RAW 提出物

区分: `reject` / 検査不能なら `dq`

- 未加工の生音声。複数マイクなら両チャンネル
- カメラ音声付きのメインカメラ生データ
- 画面キャプチャ（共通ルールで Tag Team は必須）
- セッションファイルは消さない
- 勝者および次点の音声を検査する

注記: この記事は Tag Team の人数を規定していない。

### Crew

#### CREW-TIME 演奏時間

区分: `penalty`

3:00、許容 ±10秒。2:50 以上 3:10 以下。

#### CREW-SIZE 人数

区分: 規定違反。失格文は無い。ゼロトレランスの missing / technical に入りうる

3人以上5人以下。

#### CREW-SIMUL 全員が同時に、各自のマイクで収録

区分: 禁止。同時収録違反は `SYNC-LIVE` により `dq` になりうる

- 各メンバーが自分のマイクで収録する。カメラ音声を各メンバーのトラック代わりにしてはならない
- 全員が同じ部屋で、同時に、ライブで収録する。別収録は不可
- 各マイクトラックを別々に提出する。全員が同時にリアルタイム収録したことを監視するため
- カメラ音声付きの映像も提出する
- 映像では各メンバーが常時映っている
- 生の未加工音声、カメラ音声付きメインカメラ、画面キャプチャ（共通ルール）
- セッションファイルは消さない

### Producer Showcase

Loop Mayhem がホストし、選考の裁量は Loop Mayhem にある。判定は最終。これは芸術的選考であり、技術的失格条項とは別。

#### PROD-TIME 演奏時間

区分: 範囲外の扱いが記事内で明示されていない。共通の `TIME-PENALTY` が適用される可能性がある。ゼロトレランスは duration を自動失格事由に挙げている

3:30 以上 5:00 以下。

#### PROD-SOLO ソロ公演

区分: 規定違反。失格文は無い

ソロのパフォーマンスである。

#### PROD-SOURCE 収録ソース

区分: 許可の範囲。違反時の帰結は書かれていない

Wildcard 用に撮ったライブでも、過去のライブ映像から必要時間に切ったものでもよい。

#### PROD-MIX ミックス制限なし

区分: 共通の `AUDIO-PROCESS` を上書きする記載

Mix / Mastering に制限はない。機材制限もない。選ばれた場合、機材の持込と輸送費は参加者負担。

#### PROD-DJ DJ Wildcard の禁止

区分: `reject` に最も近い。明示の単語は "No DJ wildcards"

DJ の Wildcard は不可。

#### PROD-TRACK 完成済みトラックの再生禁止

区分: 禁止。明示の失格文は無い

事前に録音され、完全にマスタリングされたトラックは不可。

原文: "No prerecorded, fully mastered tracks"

ライブ要素が主であること（ライブのビートボックス、歌、楽器演奏など）。サンプルはある程度まで可。程度の線引きは記事に無い。

#### PROD-COVER カバーは1:1禁止

区分: 禁止。明示の失格文は無い

曲のカバーは可。1:1 の再現は不可で、自分のスタイルを入れる。

#### PROD-SET 合格後のセット

区分: 合格後の義務。不履行時に失格とは書かれていない

2人の勝者は、GBB26 アフターパーティ用に 45–60 分のセットを一緒に用意する。

## 時間の計測と順位ペナルティ

### TIME-MEASURE 計測の開始

公式の長さはビートボックス時間だけ。イントロとアウトロは含めない。

開始は、Wildcard のルーティンを始めた瞬間。ボーカル、ラップ、歌、ビートボックスの音を含む。

### TIME-PENALTY 超過・不足は順位を下げる

区分: `penalty`。失格ではない

許容時間より短い、または長い場合、はみ出した満秒ごとに最終順位が1つ下がる。審判の採点中には引かれず、最終順位の確定後に適用する。

長さを検査するのは、審判順位の上位だけ。それ以外の Wildcard には時間検査をしない。

原文: "For every full second under or over the time limit, you will lose one placement in the final ranking."

原文: "Only the top-ranked wildcards by the judges will be controlled by the SBX team on the length of the wildcard (time control won’t happen for other wildcards!)."

注記: `GEN-ZERO` は duration 未達を自動失格事由に含めている。この節は順位ペナルティと書き、検査対象も上位だけに限定している。要件では両方を残し、優先順位は未決とする。

カテゴリごとの許容範囲:

| カテゴリ | 許容されるビートボックス時間 | ±10秒 |
| --- | --- | --- |
| Solo | 1:50–2:10 | あり（基準 2:00） |
| Tag Team | 1:50–2:10 | あり（基準 2:00） |
| Crew | 2:50–3:10 | あり（基準 3:00） |
| Loopstation | 3:00–3:30 | なし。範囲外は一般ペナルティ |
| Producer Showcase | 3:30–5:00 | 記事は範囲のみ。±10秒とは書いていない |

## イエローカード / レッドカード

既存の法的合意書にある不正行為条項を置き換えない。判定は最終で、交渉できない。可能なら直ちに、かつ公開で通知する。

### CARD-WARN 警告

区分: `warn`

ルールまたは行為が、許容範囲のすぐ外側、または軽微にはみ出した場合の正式通知。

### CARD-YELLOW イエロー

区分: 単体では失格ではない。保持中の追加違反は `red`

次のいずれかでイエロー。

- 警告が2回
- 失格には至らない、より重い単発の違反

### CARD-RED レッド

区分: `red`（即失格）

次のいずれかでレッド。即失格。

- ルールまたは行動規範の、明白で重大な違反
- イエロー受け取り後の、軽微なものも含む追加の不適切行為
- イエロー保持中に追加の警告を受けた場合。追加警告はレッドになり失格

カードは GBB 1サイクル持ち越す。例として、GBB26 Wildcard シーズンのイエローは GBB26 と GBB27 を通して有効、と書かれている。次の GBB に予選通過しても出場できない、という文と、処分期間は重大性により主催者が決め、最短で GBB 大会から1年、という文が並んでいる。期間の決定権は主催者にある。

行動規範の中身はこの記事に無く、参加者が署名する法的合意を参照している。動画チェッカーの判定根拠にはできない。

`AUDIO-PROCESS` の違反は、この制度の即レッドカードに明示的に接続されている。

## 合格後・参加資格（動画の中身ではない）

動画チェッカーの対象外。失格になりうるので要件の境界として残す。

### ADMIN-AGE 年齢

区分: `admin`（保護者を用意できない場合は `dq`）

- GBB26 時点で16歳以上
- 18歳未満の Wildcard 勝者がいる場合、保護者の同伴が必要
- 保護者の査証・渡航・宿泊・食事の追加費用は主催者負担ではない
- 18歳未満で保護者なしの参加は禁止
- 法的保護者を用意できない場合、その参加者は失格し、次の有資格者が選ばれる

### ADMIN-CALL オンボーディング通話

区分: `dq`

Wildcard 勝者は、確認メールで指定された期間内の公式ビデオ通話に出る。音声エンジニアと作業した場合、そのエンジニアも出席する。

通話日時が確定したあと、次は即失格。例外はない。

- 少なくとも24時間前に連絡せず欠席する
- 10分を超えて遅刻する

主催者が提示した枠のどれにも出られない場合、緊急時に限り、メールで合意した枠から外れた別の1時間で referee / commissioner と個別に会える。

当初設定した日から10営業日以内に会えず、または協力できない場合、次の Wildcard が選ばれ、本人は失格。

出席者:

- Tag Team と Crew は、申請メンバーのうち少なくとも1人
- それ以外は Wildcard 本人
- マネージャー、友人、家族、その他の代理人は不可

次点も、脱落に備えた検査の通話を数週間後に受ける。資格を保つため、生音声とセッションファイルは 2026-09-24 まで消さない。

## 記事内で失格と明記されているもの

動画チェックに直結する明記だけを再掲する。

| ID | 明記された帰結 |
| --- | --- |
| INTRO-SAME-TAKE | 別撮りのイントロは、調査後に失格 |
| AUDIO-PROCESS | 違反は即レッドカード。無許可加工は失格 |
| SYNC-LIVE | リップシンク等で正当性を確認できない場合は失格 |
| SUB-RAW | 生ファイルが提出時に無いと不受理。調査で確認できないと失格 |
| SUB-ONCE | 削除して差し替えると不受理（権利放棄） |
| CARD-RED | レッドカードは即失格 |
| ADMIN-AGE | 18歳未満で保護者を用意できないと失格 |
| ADMIN-CALL | 無断欠席、10分超の遅刻、10営業日以内に会えない、非協力は失格 |
| GEN-ZERO | 技術要件未達は自動失格になりうる。個別ルールと衝突する箇所あり |
| PROD-DJ | "No DJ wildcards"（不受理に最も近い） |

## 未確定（要件で決めるまでツールの合否にしない）

1. `GEN-ZERO` の自動失格と、`TIME-PENALTY` の順位ペナルティのどちらが長さ違反の帰結か。
2. `CARD-SCOPE`。即レッドカードが音声加工だけか、収録セットアップ節全体か。
3. `LOOP-TIME` の "immediate triggers of or general penalty rule" が、秒数ペナルティ以外の即時処分を含むか。
4. タイトル不一致、顔が隠れている、暗所、Crew の人数外、Loopstation の禁止機材が、警告・不受理・失格のどれか。記事は must / not allowed と書き、帰結の単語を置いていない。
5. Producer の「サンプルはある程度まで」「ライブ要素が主」の線引き。
6. Producer に `SUB-RAW` と冒頭自己紹介がどこまで適用されるか。共通節は全参加者向けに読め、Producer 節はミックス無制限と過去ライブ映像を許可している。
7. 行動規範の具体例。この記事には無い。
8. Showcase / Studio のルール。この URL の範囲外。
