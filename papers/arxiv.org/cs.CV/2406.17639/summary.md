# Mitigate the Gap: Investigating Approaches for Improving Cross-Modal Alignment in CLIP まとめ

## 概要
CLIP の埋め込み空間に存在する modality gap（画像とテキストの埋め込みが超球面の異なる狭い領域に密集して分布する現象）に対して、エンコーダのパラメータ共有と単一モーダル内分離（Intra-Modality Separation）という2つの改良を提案する AlignCLIP を導入した論文である。CC12M 上でスクラッチ学習した実験により、いずれの改良も modality gap を縮小しつつ下流タスクの性能を向上させ、両者を組み合わせた AlignCLIP が最も高い効果を示すことを実証している。

## 背景
CLIP は対照学習によって画像とテキストの共有表現空間を構築し、ゼロショット分類やマルチモーダル検索で優れた性能を示してきた。しかし近年、埋め込み空間が極度に疎で、画像とテキストの各モーダルが超球面上の異なる狭い部分領域に集中する modality gap の存在が指摘されている [12, 15, 16]。先行研究ではこの gap の原因としてモデルの初期化と対照損失最適化、および画像とテキスト間の情報量のアンバランス（テキストは画像と比べて情報量が少ない）が挙げられている [16]。既存手法 [12, 15, 16] は画像–テキストペアの距離に基づく単純な等長変換で gap を縮小しており、ペアでないサンプルの距離構造を歪めてしまう問題がある。

## 手法
AlignCLIP は2つの主要な要素から構成される。

**(1) SharedCLIP（パラメータ空間の共有）**
ビジョンエンコーダと言語エンコーダの間で transformer encoder および projection layer のパラメータを共有する。テキストは max pooling、画像は [CLS] token pooling で埋め込みを得る。共有により、ビジョンと言語を写像する関数が同じパラメータで最適化され、別々の疎領域への分離が抑えられる。

**(2) Intra-Modality Separation (IMSep)**
画像埋め込み間のコサイン類似度を対照損失の形で分離する。バッチ内の正例は画像–テキストペア $\vec{e}_{v_i} \cdot \vec{e}_{t_i}$、負例はバッチ内の他の画像 $i \neq j$ 同士の $\vec{e}_{v_i} \cdot \vec{e}_{v_j}$ とする vision-to-vision 対照損失を定義する。

$$L_{v \to v} = -\frac{1}{N} \sum_{i=1}^{N} \log \frac{\exp[(\vec{e}_{v_i} \cdot \vec{e}_{t_i}) / \tau]}{\sum_{j=1, j \neq i}^{N} \exp[(\vec{e}_{v_i} \cdot \vec{e}_{v_j}) / \tau]}$$

ただし、意味的に類似した画像同士を過剰に分離しないよう、ペアとなるテキストの意味的類似度を用いてリスケールする。具体的には SBERT all-mpnet-base-v2 でテキストを符号化して意味的類似度行列 $S$ と距離行列 $D = 1 - S$ を計算し、画像–画像類似度行列 $V = E_v E_v^\top$ との要素ごとの積 $V_D = V \odot D$ を負例対数項に反映させる。

最終的な損失は cross-modal separation 損失 $L_{CRsep}$（CLIP 損失そのもの）と IMSep 損失 $L_{IMsep}$ の重み付き和：

$$L = \alpha L_{CRsep} + \beta L_{IMsep}, \quad \alpha = 1, \beta = 12$$

クロスモーダル損失が片方のモーダル（テキスト側）の分離を同時に監督するため、画像側のみに IMSep を課せば十分とされる。

## 結果

**クロスモーダル整列スコア（CC3M / MSCOCO / ImageNet-1K / CIFAR-100 / CIFAR-10）**
- CLIP: 0.38–0.47
- SharedCLIP: 0.54–0.62（最大 +0.17 の改善）
- AlignCLIP: 0.62–0.67

正例ペアの平均角度は約78度（CLIP）から約47度（AlignCLIP）へと縮小した。

**ゼロショット画像分類（Top-1 / Top-5）**
- ImageNet-1K: CLIP 31.4 / 58.7 → AlignCLIP 32.8 / 60.6
- CIFAR-100: CLIP 28.1 / 55.9 → AlignCLIP 36.5 / 66.4
- CIFAR-10: CLIP 61.5 / 95.6 → AlignCLIP 69.3 / 97.8
- Flowers-102, Stanford Cars でも AlignCLIP が最高スコア

**Linear Probing（Top-1）**
ImageNet-1K, CIFAR-100, CIFAR-10, Flowers-102, Stanford Cars の5データセットすべてで AlignCLIP が CLIP・SharedCLIP を上回った。

**自然分布シフトへの頑健性（ゼロショット Top-1）**
- ImageNetV2: 27.1 → 29.1
- ImageNet-R: 39.8 → 41.2
- ImageNet-A: 6.5 → 7.0
- ImageNetSketch: 19.4 → 20.7

**ゼロショット・ファインチューニング双方のマルチモーダル検索（MSCOCO, Flickr30K, R@{1,5,10}）**
ゼロショット・ファインチューニング両設定で SharedCLIP と AlignCLIP は CLIP を一貫して上回り、AlignCLIP が概ね最良となった。

**アブレーション**
リスケール機構を除去すると、分類・検索性能がともに低下し、意味的正則化の有効性が確認された。

**DOSNES 可視化**
CLIP では画像・テキストが超球面の両端に分かれて密集していたが、AlignCLIP では両モーダルが空間全体に広がり、ペア同士が近接する整列された構造が確認された。

## 限界
本文では以下の限界が明記されている。
- ゼロショット分類の評価ベンチマークが ImageNet-1K, CIFAR-10, CIFAR-100, Stanford Cars, Flowers-102 の5つに限定されており、Food-100 や Hateful Memes 等での検証は行われていない。
- 英語のみを対象としており、多言語・言語間転移に関する分析は今後の課題である。
- IMSep のリスケール機構が事前学習済み文エンコーダ（SBERT all-mpnet-base-v2）の選択に依存しており、その影響の体系的ベンチマークは行われていない。

