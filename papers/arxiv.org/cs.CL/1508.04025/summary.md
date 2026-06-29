# Effective Approaches to Attention-based Neural Machine Translation まとめ

## 概要
本論文は、Neural Machine Translation (NMT) におけるアテンション機構を体系的に検討し、ソース文の全単語を参照する global attention と、一部の単語のみを参照する local attention という2つの単純な手法を提案している。WMT の英独・独英翻訳タスクで評価し、local attention により dropout を組み込んだ非アテンションシステム比で最大 +5.0 BLEU の大幅な改善を達成し、WMT'15 英独タスクで 25.9 BLEU の新たな state-of-the-art を記録した。

## 背景
NMT は大規模翻訳タスクで state-of-the-art を達成していたが、Bahdanau et al. (2015) によるアテンション機構の適用以降、アーキテクチャ設計の探索は限定的であった。具体的には、global 型のソフトアテンションは長い系列で計算コストが高く、hard attention は微分不可能で学習が困難というトレードオフが存在していた。本論文はこのトレードオフに対し、単純かつ効果的なアーキテクチャを設計することを動機とする。

## 手法
エンコーダ・デコーダは stacking LSTM (4層、各1000セル) を用いる。デコーダの各時刻 $t$ における上位隠れ状態 $h_t$ から、ソース側文脈ベクトル $c_t$ を導出し、$h̃_t = \tanh(W_c [c_t; h_t])$ を介して $p(y_t|y_{<t}, x) = \mathrm{softmax}(W_s h̃_t)$ により予測分布を得る。

**Global attention**: 全てのソース隠れ状態 $\bar{h}_s$ を参照し、alignment ベクトル $a_t$ を
$$a_t(s) = \frac{\exp(\mathrm{score}(h_t, \bar{h}_s))}{\sum_{s'} \exp(\mathrm{score}(h_t, \bar{h}_{s'}))}$$
に基づき計算する。$c_t$ は $\bar{h}_s$ の重み付き平均。

**Local attention**: まず aligned position $p_t$ を予測し、ウィンドウ $[p_t - D, p_t + D]$ (本論文では $D=10$) 内のソース隠れ状態のみを参照して $c_t$ を計算する。2 種類の変種を提案:
- local-m (monotonic): $p_t = t$ と仮定
- local-p (predictive): $p_t = S \cdot \mathrm{sigmoid}(v_p^\top \tanh(W_p h_t))$ で $p_t \in [0, S]$ を動的に予測し、中心 $p_t$ の Gaussian 分布で alignment 重みを重み付けする

**Alignment 関数**: $\mathrm{score}(h_t, \bar{h}_s)$ として dot ($h_t^\top \bar{h}_s$)、general ($h_t^\top W_a \bar{h}_s$)、concat ($v_a^\top \tanh(W_a[h_t; \bar{h}_s])$)、location ($a_t = \mathrm{softmax}(W_a h_t)$) の4種類を検討。

**Input-feeding approach**: 過去の alignment 情報を反映するため、$h̃_t$ を次時刻の入力に連結してフィードする。これにより水平・垂直方向に深いネットワークを構築し、coverage 効果を狙う。

Bahdanau et al. (2015) との相違点として、top LSTM 層の隠れ状態を直接用いる点、計算経路が $h_t \to a_t \to c_t \to h̃_t$ と単純な点、複数の alignment 関数を比較した点を挙げている。

## 結果
WMT'14 の 4.5M 文対 (英独両方) で学習し、newstest2013 でハイパーパラメータ選択、newstest2014/2015 で BLEU 評価。

**WMT'14 英独 (Table 1, tokenized BLEU on newstest2014)**:
- Base + reverse + dropout: 14.0 BLEU
- + global attention (location): 16.8 BLEU (+2.8)
- + feed input: 18.1 BLEU (+1.3)
- + local-p attention (general) + feed input: 19.0 BLEU (+0.9)
- + unk replace: 20.9 BLEU (+1.9)
- Ensemble 8 models: **23.0 BLEU** (Jean et al. (2015) の 21.6 を +1.4 上回り、当時の SOTA)

**WMT'15 英独 (Table 2, NIST BLEU on newstest2015)**:
- Ensemble 8 models + unk replace: **25.9 BLEU** (既存最高システムを +1.0 BLEU 上回り新 SOTA)

**WMT'15 独英 (Table 3)**: SOTA には届かなかったものの、global (dot) + drop + feed + unk で 24.9 BLEU を達成し、非アテンション比で合計 +8.0 BLEU の累積的改善を確認。

**Attention アーキテクチャ比較 (Table 4)**: local-p (general) が ppl 5.9、unk 置換後 BLEU 20.9 で最良。location 関数はアラインメント品質が劣り、concat は ppl が高かった。dot は global に、general は local に適していた。

**アラインメント品質 (Table 6)**: RWTH の 508 文対で AER を評価。local-m (general) と ensemble で 0.34、Berkeley Aligner の 0.32 と比較可能なレベルを達成。

**長文翻訳 (Figure 6)**: アテンションモデルは文長が伸びても品質が劣化せず、非アテンションを大きく上回った。

**定性評価 (Table 5)**: アテンションモデルが固有名詞 (例: "Miranda Kerr") や二重否定 ("not incompatible") の翻訳で優位性を示した。

## 限界
- 独英方向では phrase-based SOTA (Edinburgh, 29.2 BLEU) に及ばなかった。
- 計算コストの観点で global attention は長い系列で依然高コストであり、実用上は段落や文書長での翻訳に課題が残る。
- AER と翻訳スコアの相関は低く [Fraser and Marcu 2007]、アラインメント品質の翻訳への寄与は限定的である可能性が示唆される。
- 学習には単一 GPU (Tesla K40) で 7〜10 日を要し、リソース消費が大きい。
- 本文からは不明: 本論文以降に直接的に議論された残課題 (例: ビームサーチの詳細、未知語処理の限界、多言語への汎化) については明記されていない。
