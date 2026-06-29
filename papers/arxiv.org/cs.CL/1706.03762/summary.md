# Attention Is All You Need まとめ

## 概要
本論文は、再帰と畳み込みを完全に排除し、Attention 機構のみに基づく新しいネットワークアーキテクチャ「Transformer」を提案する。WMT 2014 の英語→ドイツ語・英語→フランス語翻訳タスクにおいて、既存的最良手法（アンサンブル含む）を BLEU で 2 以上上回りつつ、訓練コストを大幅に削減した。さらに、Transformer が英文構文解析にも有効に汎化することを示した。

## 背景
従来の支配的な系列変換モデルは、RNN や LSTM [13]、Gated RNN [7] を用いた encoder-decoder 構造に基づき、必要に応じて Attention を組み合わせるものであった [35, 2, 5]。再帰モデルは位置 $t$ の隠れ状態を $h_{t-1}$ と $t$ 番目の入力から逐次計算するため、本質的に逐次的であり、訓練例内の並列化が困難で、長い系列ではメモリ制約からバッチ化にも限界があった。Attention 機構自体は距離に依らない依存関係モデリングを可能とするが、ほとんどは再帰ネットワークと併用されていた。畳み込み系（Extended Neural GPU [16]、ByteNet [18]、ConvS2S [9]）では二位置間の演算回数が系列長に対し $O(n)$（ConvS2S）または $O(\log_k(n))$（ByteNet）必要であり、遠隔依存の学習が困難であった [12]。

## 手法
全体構造は encoder-decoder で、encoder は入力系列 $(x_1, \dots, x_n)$ を連続表現 $\mathbf{z} = (z_1, \dots, z_n)$ へ写像し、decoder は $\mathbf{z}$ から出力系列 $(y_1, \dots, y_m)$ を自己回帰的に生成する。

**Encoder/Decoder Stacks**
- Encoder は $N=6$ 個の同一層スタックで、各層は (1) multi-head self-attention サブ層と (2) position-wise 全結合 feed-forward サブ層からなり、双方に residual connection と layer normalization を適用する。出力は $\mathrm{LayerNorm}(x + \mathrm{Sublayer}(x))$。
- Decoder も $N=6$ 層で、各層に encoder 出力に対する multi-head attention サブ層を追加する。Decoder の self-attention では後続位置を参照しないようマスクし、自己回帰性を保つ。
- 全サブ層と埋め込み層の出力次元は $d_{\text{model}} = 512$。

**Scaled Dot-Product Attention**
query $\times$ key の内積を $\sqrt{d_k}$ で割ってから softmax を取る形式で、
$$\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$
大きな $d_k$ で内積が大きくなり softmax の勾配が極端に小さくなるのを防ぐためのスケーリングである。

**Multi-Head Attention**
$d_{\text{model}}$ 次元の query/key/value を $h$ 個の異なる学習済み線形射影で $d_k$、$d_v$ 次元に射影し、並列に attention を計算した後 concat して再び射影する。本論文では $h=8$、$d_k = d_v = d_{\text{model}}/h = 64$ を用いる。
$$\mathrm{MultiHead}(Q,K,V) = \mathrm{Concat}(\mathrm{head}_1,\dots,\mathrm{head}_h)W^O,\quad \mathrm{head}_i = \mathrm{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

**Attention の 3 用途**
- encoder-decoder attention: query が前 decoder 層、key/value が encoder 出力
- encoder self-attention: 全層で全位置間の依存を計算
- decoder self-attention: 上向き（左方向）の情報流を禁止

**Position-wise Feed-Forward Networks**
$$\mathrm{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$
各位置に同一に適用されるが層ごとに異なるパラメータを持ち、$d_{\text{model}} = 512$、内層次元 $d_{ff} = 2048$。

**Embeddings と Softmax**
埋め込み層と pre-softmax 線形変換で重み行列を共有し、埋め込み層の重みには $\sqrt{d_{\text{model}}}$ を掛ける。

**Positional Encoding**
再帰も畳み込みも無いため系列順情報を与える必要があり、入力埋め込みに加算する $\mathrm{sin}$/$\mathrm{cos}$ 関数による固定 positional encoding を用いる：
$$PE_{(pos,2i)} = \sin(pos / 10000^{2i/d_{\text{model}}})$$
$$PE_{(pos,2i+1)} = \cos(pos / 10000^{2i/d_{\text{model}}})$$
任意の固定オフセット $k$ に対し $PE_{pos+k}$ が $PE_{pos}$ の線形関数として表せ、相対位置の学習が容易になると仮説を立てた。学習済み positional embedding でもほぼ同等の結果が得られた（Table 3 行 (E)）。

**訓練設定**
- データ: WMT 2014 English-German（~4.5M 文対、共有 ~37k BPE）、English-French（36M 文、32k word-piece）
- 最適化: Adam、$\beta_1=0.9$、$\beta_2=0.98$、$\epsilon=10^{-9}$
- 学習率スケジュール: $\mathrm{lrate} = d_{\text{model}}^{-0.5} \cdot \min(\mathrm{step\_num}^{-0.5},\ \mathrm{step\_num}\cdot\mathrm{warmup\_steps}^{-1.5})$、$\mathrm{warmup\_steps}=4000$
- 正則化: sub-layer 出力と埋め込み+positional encoding の和に dropout（基本 $P_{\text{drop}}=0.1$）、label smoothing $\epsilon_{ls}=0.1$
- ハードウェア: 8 基の NVIDIA P100 GPU、base モデル約 0.4 秒/ステップで 100,000 ステップ（12 時間）、big モデル 1.0 秒/ステップで 300,000 ステップ（3.5 日）

## 結果
**機械翻訳（Table 2）**
- WMT 2014 English-to-German: Transformer (big) が 28.4 BLEU を達成し、既存最良（アンサンブル含む）を 2.0 BLEU 以上上回る新 SoTA。
- WMT 2014 English-to-French: Transformer (big) が 41.8 BLEU、単一モデルとして新 SoTA。
- 比較対象: ByteNet [18]、Deep-Att + PosUnk [39]、GNMT + RL [38]、ConvS2S [9]、MoE [32]、およびそれぞれのアンサンブル。
- FLOPs に基づく訓練コストは他モデルの 1/10 から 1/100 程度。
- 推論時はベースモデルは最後の 5 チェックポイント、big モデルは最後の 20 チェックポイントを平均化、beam size 4、length penalty $\alpha=0.6$。

**モデル構成の ablations（Table 3, English-to-German dev, newstest2013）**
- (A) head 数と key/value 次元の組合せ: 単一 head は最良設定より 0.9 BLEU 低下。多すぎても品質低下。
- (B) key 次元 $d_k$ を小さくすると品質低下（compatibility 計算の困難さを示唆）。
- (C) (D) モデルが大きいほど良く、dropout が過学習抑制に有効。
- (E) sinusoid の代りに学習済み positional embedding でもほぼ同等の結果。

**英文構文解析（Table 4, WSJ Section 23）**
- WSJ のみ (~40K 文) で訓練した 4 層 Transformer（$d_{\text{model}}=1024$）が F1 = 91.3。
- semi-supervised 設定（~17M 文）では F1 = 92.1 を達成し、Recurrent Neural Network Grammar [8] を除く全報告モデルより高い結果。

**Self-Attention の理論的利点（Table 1）**
- per-layer 計算量: self-attention $O(n^2 \cdot d)$
- 逐次演算: $O(1)$（recurrent の $O(n)$ と比較）
- 最大経路長: $O(1)$（recurrent $O(n)$、conv $O(\log_k(n))$ と比較）

## 限界
- 長系列への対処として local, restricted attention（近傍サイズ $r$）は計画中の将来的検討事項であり、restricted self-attention では最大経路長が $O(n/r)$ に増大する。本文からは本番モデルでの採用は確認できない。
- 生成の逐次性の解消は今後の研究目標として挙げられている。
- テキスト以外の modality（画像・音声・動画等）への拡張は今後の課題として記述されているのみ。
- その他、本文からは不明。
