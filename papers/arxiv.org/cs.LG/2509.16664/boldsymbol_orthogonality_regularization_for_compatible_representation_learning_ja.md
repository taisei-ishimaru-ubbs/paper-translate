---
title: "$\boldsymbolλ$-Orthogonality Regularization for Compatible Representation Learning（日本語訳）"
tags: [paper-translation]
---

[[boldsymbol_orthogonality_regularization_for_compatible_representation_learning|← 論文ノート]]

# Introduction 

検索タスクは、顔認識 [[#^ref-1|1]][[#^ref-2|2]][[#^ref-3|3]]、画像ローカライゼーション [[#^ref-4|4]][[#^ref-5|5]][[#^ref-6|6]]、および物体同定 [[#^ref-7|7]][[#^ref-8|8]][[#^ref-9|9]] といった実世界アプリケーションにおいてますます重要になっている。画像検索では、ラベル付き画像からなるギャラリーとクエリ画像を対応付け、関連する画像、理想的には同一クラスの画像を同定する。高次元の画像そのものではなく、検索では埋め込みモデルによって得られる低次元の特徴ベクトルを用いる。検索性能の向上には、より表現力の高いネットワークアーキテクチャ [[#^ref-12|12]]、新たな学習手法（例：損失関数）や学習パラダイム [[#^ref-13|13]][[#^ref-14|14]][[#^ref-15|15]] を活用するために、埋め込みモデル [[#^ref-10|10]][[#^ref-11|11]] を更新することがしばしば含まれる。しかし、ニューラルネットワークは、同一データに対し同一の手法とアーキテクチャで学習された場合であっても、互換性のある特徴をほとんど生成しない [[#^ref-16|16]]。その結果、新規クエリの特徴と旧来のギャラリーの特徴を対応付ける際に、不整合により検索性能が低下しうる [[#^ref-15|15]]。これに対処するためには、旧モデルによって生成されたギャラリー特徴を新モデルが生成したものに置き換える必要があるが、このバックフィリングと呼ばれる処理は計算コストが高い。基盤モデルを更新しつつ後方互換性を確保し、バックフィリングを回避する課題は広く研究されてきた [[#^ref-17|17]][[#^ref-15|15]][[#^ref-18|18]][[#^ref-19|19]][[#^ref-20|20]][[#^ref-21|21]]。さらに、ギャラリー更新の最適戦略、すなわち partial backfilling も近年注目を集め始めている [[#^ref-22|22]]。

互換性を確保するためのアーキテクチャ変更や追加損失は、更新後モデルの性能を低下させうる [[#^ref-23|23]][[#^ref-24|24]]。この問題に対処するため、研究は、パラメータ効率の高いアダプタ [[#^ref-22|22]][[#^ref-25|25]] を用いて、基盤モデルの表現を独立に学習された改良モデルの表現に整合させることに焦点を当ててきた。一方、manifold hypothesis [[#^ref-26|26]][[#^ref-27|27]] は、ニューラルネットワークが通常、同一データ分布の潜在空間表現を生成し、その差異は主として変換によって記述できることを示唆する。したがって、機能的に等価なモデルは同一の潜在多様体を近似するため、ある表現を別の表現へ写像するのに必要なパラメータはごく少数で済む [[#^ref-28|28]][[#^ref-29|29]][[#^ref-27|27]]。ゆえに、新しい表現空間を以前の表現空間に整合させる単純な変換によって、更新後モデルの後方互換性を実現できる。

![](assets/fig01.png)

検索システム更新時に表現互換性を実現するための提案手法の概要。新たに独立学習されたモデルは、幾何構造を保持する直交変換 $B_{\perp}$ により旧表現空間へ整合される。順方向変換 $F$ は、旧表現を新モデルの後方整合済み空間へ写像する。学習時に最適化されるのは変換パラメータのみであり、モデルパラメータは固定されたままである。

近年の研究では、基盤モデルの潜在空間（source space）を別のモデルの潜在空間（target space）へ適応させるために、特定のデータ点を参照として affine mapping および orthogonal mapping が検討されてきた [[#^ref-30|30]][[#^ref-28|28]][[#^ref-31|31]]。plasticity-stability paradigm [[#^ref-32|32]] において、affine mapping は高い適応性（plasticity）を提供する一方で、source space の配置を変化させる可能性がある [[#^ref-33|33]][[#^ref-34|34]]。逆に、orthogonal mapping は source space の幾何構造を維持する（stability）ものの、異なる分布への適応性は持たない。source space の幾何構造、特にそれが target space よりも情報量に富む場合 [[#^ref-28|28]][[#^ref-35|35]] を保持しつつ適応性も実現するために、本研究では新たな正則化項を提案する。先行研究 [[#^ref-36|36]] と異なり、本項は、ハイパーパラメータ $\lambda$ により制御される所定の近傍に変換を制約し、直交条件の近傍に留まるようにする。

本論文では、Fig. [\[fig:compatible_adapters\]](#fig:compatible_adapters) に示すように、異なる表現空間間で変換を学習することにより、独立学習されたモデル間の互換性を確保する課題に取り組む。貢献は以下のとおりである。

- $\lambda$-Orthogonality regularization を提案する。これは、元の表現空間の大域構造を保持しつつ、下流タスクに対する局所的な微調整を可能にする緩和直交制約である。

- supervised contrastive loss を用いて表現互換性を向上させる。これにより、クラス内クラスタリングとモデル間の特徴表現整合を促進しつつ、モデルアーキテクチャに依存しない枠組みを実現する。

- 多様なアーキテクチャとデータセットにわたる広範な実験を行い、本手法がモデル間の互換性を確保するだけでなく、基盤モデルの潜在空間幾何の保持も促進し、下流タスクの精度向上につながることを示す。

- 検索性能を改善しつつギャラリー更新プロセスを最適化する、新しいアーキテクチャ非依存の backfilling 戦略を提案する。

# Related Works

[[#^ref-16|16]] によれば、同一データで学習された場合であっても、2つのモデルから得られる特徴表現は一般には一致せず、検索システムにおいて高コストなバックフィリングを生じさせる。これを回避するために、[[#^ref-15|15]] は Backward Compatible Training (BCT) を導入し、旧分類器を参照として固定することで、新しい埋め込みが従来のクラスプロトタイプに整合するようにした。さらに、同研究はモデル表現間の互換性の形式的定義を与えた。その後の研究はこの基盤を拡張し、新しい表現を従来のものによりよく整合させるための追加正則化手法 [[#^ref-21|21]][[#^ref-37|37]][[#^ref-20|20]][[#^ref-38|38]][[#^ref-39|39]] や、特定のアーキテクチャ設計 [[#^ref-18|18]][[#^ref-13|13]][[#^ref-40|40]] を導入してきた。しかし、更新された backward-compatible model の性能は、しばしば独立に学習されたモデルの性能に届かない [[#^ref-23|23]]。これは、互換性を達成するために課される正則化の帰結である。これを避けるために、[[#^ref-23|23]] と [[#^ref-24|24]] は、古いクラスの表現整合を更新中に維持しつつ、新しいクラスを含めるよう表現空間を拡張することを提案した。独立に学習されたモデル間の互換性を確保するために、mapping-based strategy も開発されている [[#^ref-41|41]][[#^ref-42|42]][[#^ref-43|43]]。[[#^ref-25|25]] で詳述される Forward Compatible Training (FCT) は、旧モデルの埋め込みを新モデル空間の埋め込みへ整合させる関数を導入し、各データ点に対する追加の補助情報を組み込む。[[#^ref-25|25]] が指摘するように、これらの変換に伴う計算オーバーヘッドは、埋め込みモデルを通じて画像を処理する負荷と比べればごく小さい。FastFill [[#^ref-22|22]] は、新モデル分類器を用いることで順方向変換学習を改善し、新モデルを活用してギャラリーバックフィリング過程を最適化する Bayesian strategy を提案する。これに対し本研究では、モデル更新時に forward compatibility だけでなく backward compatibility も確保するための一連の変換関数を提案し、特に backward mapping における orthogonality property に焦点を当てる。さらに、クラス内クラスタリングと相互モダリティ整合を促進する supervised contrastive loss を提案し、適応を強化する。最後に、事前抽出されたギャラリー表現に対して直接動作する距離尺度に基づく新しいギャラリーバックフィリング戦略を提案し、基盤アーキテクチャに依存しないものとする。

# Method 

独立に学習されたモデル間で互換的な表現を実現するために、我々は複数の変換から構成される理論的基盤を有するパイプラインを導入する。まず、Sec. 3.1 では [[#^ref-15|15]] により導入された互換性の定義を述べる。Sec. 3.2 および 3.3 では、新しい backward-ompatibility 手法を導入する。これは、厳密な直交変換、あるいは下流タスクへ適応する際には我々が提案する $\lambda$-Orthogonality 制約で正則化された変換のいずれかを用いて、新モデルの表現を以前のモデルの表現へ整合させるものである。次に、Sec. 3.4 では forward trasformation learning を示す。これは、前モデルの表現を、更新・適応後の新モデルの表現へ affine またはより複雑な変換により整合させ、ギャラリー集合の有効な更新を可能にする。さらに、変換学習の際に supervised contrastive loss（Sec. 3.5）を適用し、モデル表現間の整合を改善するとともに、クラス内クラスタのコンパクト性を高め、Def. 1 で定義された互換性基準を満たすようにする。最後に、Sec. 3.6 では、改善された表現を最適化された順序でギャラリーに backfilling するための新しい順序付け戦略を提案する。本手法全体を通じて、すべてのモデルはパラメータを固定した特徴抽出器として機能し、学習されるのは変換層のみである。

![](assets/fig02.png)

![](assets/fig03.png)

![](assets/fig04.png)

異なる $\lambda$ における Eq. [\[eq:orth_smooth\]](#eq:orth_smooth) の値。

## Backward-Compatible Representations Definition 

[[#^ref-15|15]] により導入された表現間の Backward-Compatibility の定式化は、異なるモデル間の潜在空間通信の概念と密接に関係している [[#^ref-30|30]]。Backward-compatible representations の形式的定義は以下のとおりである。

**Definition 1** (***Backward-Compatibility***). ステップ $k$ で学習されたモデルの表現が、後続ステップ $t$ で学習された異なるモデルの表現と互換的であるとは、$k < t$ のとき、次の条件が満たされる場合をいう。$$\forall\,i,j:\;\bigl(y_i=y_j\implies d(\mathbf h_i^t,\mathbf h_j^k)\le d(\mathbf h_i^k,\mathbf h_j^k)\bigr)\;\wedge\;\bigl(y_i\neq y_j\implies d(\mathbf h_i^t,\mathbf h_j^k)\ge d(\mathbf h_i^k,\mathbf h_j^k)\bigr)$$ ここで $d(\cdot, \cdot)$ は距離関数であり、$y_i$ と $y_j$ は、それぞれ抽出された表現ベクトル $\mathbf{h}_{i}$ と $\mathbf{h}_{j}$ に対応するクラスラベルである。Def. 1 の不等式は、新モデルの表現が旧表現と比較したとき、同一クラス画像のクラスタリングおよび異なるクラス画像の分離において、少なくとも従来モデルと同等以上に機能すべきであることを示している。

## Backward Transformation 

relative encoding [[#^ref-30|30]] の貢献の一つは、実際には、表現空間は同じあるいは類似したデータセマンティクスを共有する場合、しばしば角度保存変換によってのみ異なるという観察である。さらに [[#^ref-28|28]] は、学習されたセマンティクスに差異がある場合、角度と距離の双方を保存する変換――Procrustes analysis [[#^ref-44|44]] により学習される――が、角度保存のみの写像よりも、クロスアーキテクチャおよびクロスモダリティの分類タスクで優れた性能を与えることを示している。変換 $T$ は、空間内の任意の2点 $a$ と $b$ の間の角度と距離を保存するなら等長写像（isometry）と定義される。形式的には、写像 $T: \mathbb{R}^n \to \mathbb{R}^n$ が等長写像であるとは、次の条件が成り立つ場合である：$\| T(a) - T(b) \|_2 = \| a - b \|_2, \quad \forall a, b \in \mathbb{R}^n$。ここで $\| \cdot \|_2$ はユークリッドノルムを表し、他の空間では同値な一般距離尺度を意味する。我々はこの性質を利用して、直交変換により更新後モデルの空間を基盤モデルの空間に整合させ、後方互換表現を実現する。これにより、更新をまたいで統一された表現空間が維持され、変換の等長性により更新後モデルの幾何学的性質と性能が保持される。

与えられたベースモデル $\phi^k$ とその更新版 $\phi^t$（ただし $k < t$）、およびそれぞれに対応する表現ベクトル $\mathbf{h}^k \in \mathbb{R}^d$ と $\mathbf{h}^t \in \mathbb{R}^n$ に対し、更新モデルの埋め込み空間をベースモデルの空間へ写像する直交変換 $B_{\perp}: \mathbb{R}^n \rightarrow \mathbb{R}^n$ を学習する。厳密な直交性を課すため、一般的な変換 $B$ は歪対称行列 $P$ の行列指数としてパラメータ化され、$B = e^P$ とする。このとき、$P$ の上三角成分を学習可能パラメータとする [[#^ref-45|45]]。更新モデルとベースモデルの表現空間間の整合を強制するため、$\mathbf{h}^k$ と変換後の $\mathbf{h}^t$ の間の平均二乗誤差損失を最小化することにより、変換 $B_{\perp}$ を最適化する： $$\mathcal{L}_{B} = ||B_{\perp}(\mathbf{h}^t) - \mathbf{h}^k||_2^2$$ 変換 $B_{\perp}$ は正方行列であるため、二つの表現空間の次元が異なる場合には、高次元側の特徴ベクトルを切り詰めて、より小さい表現空間の次元に合わせる。

## $\boldsymbol{\lambda}$-Orthogonality Regularization 

変換 $B$ に対する厳密な直交制約（高い安定性）は、アダプタが訓練された分布と実際の分布が異なる場合には必ずしも理想的ではない。すなわち、抽出済み埋め込みのみをユーザに提供する private models の場合である。このような制約を課すと、下流タスクに必要な新たな関連情報の統合が制限され得る。これに対して、幾何学的正則化を伴わないアフィン変換（高い可塑性）は、更新モデルの表現を攪乱し得る [[#^ref-46|46]][[#^ref-47|47]]。[[#^ref-36|36]] で述べられているように、重み行列 $W \in \mathbb{R}^{n \times n}$ とバイアス項 $b \in  \mathbb{R}^n$ からなる変換 $B: \mathbb{R}^n \rightarrow \mathbb{R}^n$ に対して、ソフトな直交制約を適用できる。先行研究 [[#^ref-48|48]][[#^ref-49|49]][[#^ref-50|50]] は、次のように定義される損失関数を最小化することで、重み行列の Gram 行列が単位行列に近くなるよう制約することを提案している： $$\mathcal{L}_{orth} = ||W^T W - I||_F$$ ここで $||\cdot||_F$ は Frobenius ノルムを表し、$W$ は変換 $B$ の重みである。これは、パラメータ集合を Stiefel manifold [[#^ref-50|50]] の近傍に制限する重み減衰項として解釈できる。しかし、このアプローチでは、変換に対して具体的にどの程度の直交性を課すかを制御できない。

そこで本研究では、重み行列の Gram 行列が単位行列にどの程度近いかを指定する閾値 $\lambda$ を導入する。素朴な解決策としては、損失が Gram 行列に直接影響することから、重み行列の Gram 行列が閾値 $\lambda$ に到達した時点で $\mathcal{L}_{orth}$ の最適化を停止する方法が考えられる： $$\min_{W} \; ||W^T W - I||_F \quad \text{s.t.} \quad ||W^T W - I||_F \geq \lambda$$ この目的は、パラメータ $\lambda$ によってシフトされた Heaviside step function [[#^ref-51|51]][[#^ref-52|52]] を用いることで直接実現できる：$H(x-\lambda)=\mathbf{1}_{\{x\ge\lambda\}}$ この関数 $H$ は、最小化過程における直交性の程度を制御する効率的な機構を提供し、Frobenius ノルムが閾値 $\lambda$ を超えると、式 [\[eq:ortho\]](#eq:ortho) の正則化項を実質的に無効化する： $$\mathcal{L}_{\lambda} = H ( \| WW^T - I \|_F - \lambda) \cdot \| WW^T - I \|_F.$$ しかし、このアプローチは [[#^ref-53|53]] で指摘されているように、損失関数に不連続性を導入する。特に同研究では、これらの sigmoid 関数が Heaviside step function にどれほど近いかの評価に焦点を当て、Hausdorff 距離に対する厳密な上界および下界を与えている。これらの理論的・実証的分析を踏まえ、本研究では、制約の効果が徐々に調整され、$\lambda$ からの距離に応じて罰則の強さが増減するような滑らかなモジュレーション関数を提案する。具体的には、次の損失関数を最適化することで、新規の $\lambda$-Orthogonality Regularization 項を定式化する： $$\mathcal{L}_{\lambda} = \sigma \left( \alpha \left( \| WW^T - I \|_F - \lambda \right) \right) \cdot \| WW^T - I \|_F$$ ここで $\sigma(\cdot)$ は sigmoid 関数であり、$\alpha$ はスケーリング係数である。

![](assets/fig05.png)

![](assets/fig06.png)

![](assets/fig07.png)

![](assets/fig08.png)

![](assets/fig09.png)

Source space

sigmoid 関数は、図 [\[fig:lambda\]](#fig:lambda) に示すように、$\lambda$ の値付近で正則化項を徐々にオン・オフする連続的なスイッチとして機能する。一方、スケーリング係数 $\alpha$ は sigmoid 関数の急峻さを制御し、それにより $\| WW^T - I \|_F$ の値が閾値 $\lambda$ に近づく際に正則化がどの程度急激に有効化・無効化されるかが決まる。図 [\[fig:alpha\]](#fig:alpha) では、正則化損失に適用した異なる急峻さのレベルを示す。$\alpha$ が増加するにつれて、その挙動は Heaviside step function により近く収束する。

$\lambda$-orthogonality regularization の挙動をさらに解析するため、ランダム初期化された重み行列 $W$ をもつ変換 $B$ に Eq. [\[eq:orth_smooth\]](#eq:orth_smooth) を適用して最適化する。図 [\[fig:angle\]](#fig:angle) に示すように、これらの角度の kernel density estimation (KDE) は、正則化に用いる $\lambda$ の値に応じて変化する。$\lambda$ の値が小さいほど、列ベクトルはより強く直交化される。特に $\lambda=0$ のとき、本正則化は Eq.[\[eq:ortho\]](#eq:ortho) と等価である。図 [\[fig:mnist\]](#fig:mnist) は、full MNIST dataset で学習された source representation space（図 [\[fig:source\]](#fig:source)）と、MNIST の最初の 5 クラスで学習された target representation space（図 [\[fig:target\]](#fig:target)）を整合させるために学習した、アフィン変換（図 [\[fig:affine\]](#fig:affine)）、厳密直交変換（図 [\[fig:sorth\]](#fig:sorth)）、および $\lambda$-orthogonality regularized 変換（図 [\[fig:near_orth_mnist\]](#fig:near_orth_mnist)）の効果を示している。この toy experiment は、$\lambda$-orthogonal 制約が、厳密直交性を緩和しつつ source feature space の構造保持を促進することで整合を改善することを示しており、これは無制約変換とは対照的である。

## Forward Transformation 

新しいモデルの表現を以前のモデルの表現へ写像する backward transformation に加え、forward transformation $F: \mathbb{R}^d \rightarrow \mathbb{R}^n$ を定式化することも可能である。この変換は、以前のモデルの表現ベクトル $\mathbf{h}^k \in \mathbb{R}^d$ を、新しいモデルの表現 $\mathbf{h}^t \in \mathbb{R}^n$ へ写像する。新しいモデルの表現は以前のモデルのそれより優れているため、変換 $F$ は、改善された表現により適切に適応できるよう、アフィン（高い可塑性）であるか、あるいは複数の射影層から構成されるべきである。変換 $F$ は、[[#^ref-25|25]] で述べられたアプローチに従い、二つの表現間の Mean Squared Error を $|| F(\mathbf{h}^k) - \mathbf{h}^t ||_2^2$ として最小化することによって学習される。この概念は latent space communication [[#^ref-30|30]][[#^ref-31|31]] と密接に関連しており、そこでは $\mathcal{T}$ を一般的な変換とすると、$d \big(\mathbf{h}^k_{i}, \mathbf{h}^k_{j} \big) = d \big(\mathcal{T}\ \mathbf{h}^t_{i}, \mathcal{T}\ \mathbf{h}^t_{j} \big)$ が成り立つ。先行手法 [[#^ref-25|25]][[#^ref-22|22]] では、古い表現 $\mathbf{h}^k$ を変換 $F$ を通じて新しい $\mathbf{h}^t$ に直接整合させているが、$\mathbf{h}^k$ と $F(\mathbf{h}^k)$ の間に非整合が生じる。Sec. 3.2 で述べたように、backward orthogonal transformation $B_{\perp}$ は新しい表現を古いものに再整合させる。古い特徴を新しい表現 $\mathbf{h}^t$ に直接適応させる代わりに、$B_{\perp}(\mathbf{h}^t)$ に適応させることで、モデル更新全体を通じて統一的な整合を保証する。さらに、変換 $F$ と $B_{\perp}$ は同一の訓練データを利用するため、同時に学習可能である。したがって、我々の方法論における forward alignment loss は次のように定義される：

$$\mathcal{L}_F = || F(\mathbf{h}^k) - B_{\perp}(\mathbf{h}^t) ||_2^2$$

抽出された表現が、Sec. 3.3 で議論したように、二つのモデルの訓練集合とは異なるデータセットに由来する場合には、厳密直交な $B_{\perp}$ の代わりに、$\lambda$-orthogonal regularized transformation $B_{\lambda}$ を用いることができる。

## Intra-class Clustering and Inter-Model Alignment 

Sec. 3.1 で議論したように、Def. 1 で定義された compatibility inequalities は、整合だけでなく、compatibility を達成するためのより高いクラスタ集中度も要求する。この目的のために、[[#^ref-22|22]] は追加の訓練損失 $\mathcal{L}_{disc}$ を導入しているが、[[#^ref-15|15]] の influence loss とは異なり、これは旧モデルではなく新モデルの分類器に直接依拠する。しかし、$\mathcal{L}_{disc}$ は新モデルの分類器および訓練損失へのアクセスに依存するため、特に新モデルのアーキテクチャが不明な場合（たとえば private models や online models から得られる埋め込みベクトル）には適用可能性が制限される。これを克服するため、本研究では表現ベクトルに直接適用する supervised contrastive loss の利用を提案する。この損失は、整合とクラスタリングのために表現ベクトルを直接活用するため、分類器やアーキテクチャに関する知識を必要としない。supervised contrastive loss [[#^ref-54|54]] は、$\mathbf{q}_i$ と $\mathbf{p}_i$ の間の cross-entropy loss を最小化する： $$\mathcal{L_{\text{contr}}} = -\sum_{i=1}^K \mathbf{p}_i \log \mathbf{q}_i$$ ここで $\mathbf{q}_i$ は、L2 正規化された特徴 $\mathbf{h}$ と各候補との内積類似度に対して温度スケール付き softmax を適用することによりサンプル $i$ に割り当てられる確率を表し、$\mathbf{p}_i$ は、意味的に一致する（同一クラスの）候補すべてに等しい重みを与え、それ以外を 0 とする正規化済みの真値指示分布である。具体的には、本損失関数の組合せを利用し、目的関数 $\mathcal{L}_{\text{C}}$ を次のように定義する： $$\begin{aligned}
\mathcal{L}_{\text{C}} = \mathcal{L}_{\text{contr}}(F(\mathbf{h}^k), B_{\perp}(\mathbf{h}^t))\ + \mathcal{L}_{\text{contr}}(F(\mathbf{h}^k),\mathbf{h}^k)
\end{aligned}$$ この損失は、適応後表現のクラスタリングを促進すると同時に、それらを以前のモデルの表現と整合させることで、特徴表現のクラス内クラスタリングとモデル間整合を促進する。

我々のフレームワークにおける全体損失関数は、forward alignment loss $\mathcal{L}_F$、backward alignment loss $\mathcal{L}_{B}$、contrastive loss $\mathcal{L}_{\text{C}}$、および $\lambda$-Orthogonality regularization 項 $\mathcal{L}_{\lambda}$ の 4 成分の重み付き和として定義される。形式的には、総損失は次式で表される： $$\mathcal{L} = w_1 \cdot \mathcal{L}_F + w_2 \cdot \mathcal{L}_{B} + w_3 \cdot \mathcal{L}_C + \mathcal{L}_{\lambda}$$[] ここで $w_1$、$w_2$、および $w_3$ は、各項の寄与を調整するためのスカラー重みである。

## Partial Backfilling Strategy

順方向に適応されたgallery setにおけるbackfillingサンプルの有効な順序を決定することは、旧モデルの $F(\mathbf{h}^k)$ を $B_{\perp}(\mathbf{h}^t)$ に置き換えたとき、新たに独立学習されたモデルの性能を可能な限り効率的に達成するうえで極めて重要である。しかし、backfilling の最適順序を同定することは、計算的に扱いにくい組合せ最適化問題である [[#^ref-22|22]]。この課題に対処するため、FastFill [[#^ref-22|22]] は Bayesian Deep Learning に着想を得た順序付けを導入する。この手法は、アライメント誤差を多変量ガウス分布としてモデル化し、マッピング関数 $F$ の学習中にこの分布の負の対数尤度を最小化する。しかし、retrieval の観点からは、最も代表的なインスタンス、すなわち異なるクラス間の分離を大きく向上させるものは、それぞれのクラス平均に最も近い埋め込みとして同定される [[#^ref-55|55]][[#^ref-56|56]]。したがって、情報量の最も少ない埋め込みを優先的に backfilling することにより、クラス間の識別性が強化され、システム性能は向上する。そこで我々は、既に抽出された表現ベクトル $F(\mathbf{h}^k)$ に直接基づいて backfill 順序を推定する新しい手法を提案する。まず、順方向に適応されたgallery setにおける各クラス $c$ の平均表現ベクトル $\boldsymbol{\mu}_c$ を計算する。次に、各埋め込みベクトル $F(\mathbf{h}^k)$ について、その対応するクラス平均 $\boldsymbol{\mu}_c$ からの距離指標 $d$ を計算する。例えば、$d$ は平均二乗誤差でよく、$d = \| F(\mathbf{h}^k) - \boldsymbol{\mu}_c \|_2$ と表される。$\boldsymbol{\mu}$ からの距離 $d$ が最も大きいgallery埋め込みを backfilling の優先対象とすることで、新たに backward-adapted された独立学習モデル $B_{\perp}(\mathbf{h}^t)$ によって生成された query とのマッチングを促進する。

# 実験

0.48

<table>
<thead>
<tr>
<th style="text-align: center;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: center;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">43.56</td>
<td style="text-align: center;">25.18</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.10</td>
<td style="text-align: center;">0.15</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">61.61</td>
<td style="text-align: center;">35.69</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.10</td>
<td style="text-align: center;">0.15</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">50.13</td>
<td style="text-align: center;">30.93</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">57.21</td>
<td style="text-align: center;">33.00</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.10</td>
<td style="text-align: center;">0.15</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">50.63</td>
<td style="text-align: center;">31.48</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">57.21</td>
<td style="text-align: center;">33.19</td>
</tr>
<tr>
<td rowspan="5" style="text-align: center;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>44.59</strong></td>
<td style="text-align: center;"><strong>26.70</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>51.46</strong></td>
<td style="text-align: center;"><strong>33.75</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>57.41</strong></td>
<td style="text-align: center;"><strong>34.53</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>43.94</strong></td>
<td style="text-align: center;"><strong>25.75</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">61.61</td>
<td style="text-align: center;">35.69</td>
</tr>
</tbody>
</table>

0.48

<table>
<thead>
<tr>
<th style="text-align: center;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: center;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">55.62</td>
<td style="text-align: center;">26.91</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">76.62</td>
<td style="text-align: center;">56.84</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">59.39</td>
<td style="text-align: center;">42.65</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">72.54</td>
<td style="text-align: center;">49.85</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>61.17</strong></td>
<td style="text-align: center;"><strong>46.28</strong></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">73.33</td>
<td style="text-align: center;"><strong>52.83</strong></td>
</tr>
<tr>
<td rowspan="5" style="text-align: center;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>60.83</strong></td>
<td style="text-align: center;"><strong>40.69</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">61.10</td>
<td style="text-align: center;">45.91</td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>73.53</strong></td>
<td style="text-align: center;">52.06</td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>65.54</strong></td>
<td style="text-align: center;"><strong>38.55</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">76.62</td>
<td style="text-align: center;">56.84</td>
</tr>
</tbody>
</table>

## Image Retrieval Compatibility

backward compatibility は、gallery set $\mathcal{G} = \{(\mathbf{x}_i, y_i)\}_{i=1}^{N_g}$ と query set $\mathcal{Q}=\{(\mathbf{x}_i, y_i)\}_{i=1}^{N_q}$ を含む retrieval タスクにおいて極めて重要である。これらはそれぞれ $N_g$ 枚および $N_q$ 枚の画像を含み、対応するクラスラベルを有する。base model は、画像から特徴ベクトルを抽出して gallery を索引付けし、retrieval タスクにおいて query set のベクトルと照合する。Def. 1 で提示された compatibility の定義では、データセット内の全データ点間のペアワイズ距離を計算する必要がある。この処理は、データセット規模が大きくなるにつれてますます計算負荷が高くなる。さらに、ステップ $t$ で更新されたモデルが、ステップ $k$ で学習された base model と backward-compatible であると見なされるのは、Empirical Compatibility Criterion [[#^ref-15|15]] が満たされる場合である: $$M \big( \Phi_t^\mathcal{Q}, \Phi_k^\mathcal{G} \big) > 
M \big( \Phi_k^\mathcal{Q}, \Phi_k^\mathcal{G} \big), \quad \text{with } k < t$$ ここで $M$ は性能指標を表し、$\Phi^\mathcal{G}$ および $\Phi^\mathcal{Q}$ は、それぞれ抽出されたgalleryおよびqueryの特徴を表す。具体的には、$M \big( \Phi_t^\mathcal{Q}, \Phi_k^\mathcal{G} \big)$ は、ステップ $t$ の更新済みモデルからのgallery特徴とステップ $k$ のquery特徴を用いた異種モデル間 retrieval を評価する。これに対し、$M \big( \Phi_k^\mathcal{Q}, \Phi_k^\mathcal{G} \big)$ は同一モデル内 retrieval を指し、gallery と query の両特徴がともにステップ $k$ の同一モデルに由来する。

<table id="table:cub">
<caption>ImageNet1Kで事前学習され下流タスクへ適応された2つのモデルに対する互換性結果：$\phi_{\text{old}}$（ResNet-18）および $\phi_{\text{new}}$（ViT-L-16）について、逆方向アダプタとして $\lambda=12$ の $B_\lambda$ を用いている。ZS列はImageNet1KにおけるCMC-Top1性能の増加を示し、括弧内の値は新たに独立に学習したモデルと比較した増分を示す。各Query/Galleryの組合せは、結果の比較を容易にするため異なる色で強調されている。</caption>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th colspan="4" style="text-align: center;">Dataset</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>3-6</span></td>
<td style="text-align: center;"></td>
<td colspan="2" style="text-align: center;"><strong>CUB</strong></td>
<td colspan="2" style="text-align: center;"><strong>CIFAR100</strong></td>
</tr>
<tr>
<td style="text-align: left;"><span>3-6</span></td>
<td style="text-align: left;"></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">ZS</td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">ZS</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">44.82</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">51.13</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.4</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">0.8</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">71.78</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">74.08</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">0.8</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">51.10</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">57.35</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">62.13</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">69.80</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.4</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">0.8</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">54.50</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">66.17</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">61.49</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">67.23</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="5" style="text-align: left;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>51.12</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>67.29</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>59.92</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>67.72</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>70.72</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>72.08</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>60.64</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>71.85</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$</td>
<td style="text-align: center;"><table id="table:cub">
<caption>ImageNet1Kで事前学習され下流タスクへ適応された2つのモデルに対する互換性結果：$\phi_{\text{old}}$（ResNet-18）および $\phi_{\text{new}}$（ViT-L-16）について、逆方向アダプタとして $\lambda=12$ の $B_\lambda$ を用いている。ZS列はImageNet1KにおけるCMC-Top1性能の増加を示し、括弧内の値は新たに独立に学習したモデルと比較した増分を示す。各Query/Galleryの組合せは、結果の比較を容易にするため異なる色で強調されている。</caption>
<tbody>
<tr>
<td style="text-align: center;"><strong>75.44</strong> (<strong>+3.66</strong>)</td>
</tr>
</tbody>
</table></td>
<td style="text-align: center;"><strong>+0.025</strong></td>
<td style="text-align: center;"><table id="table:cub">
<caption>ImageNet1Kで事前学習され下流タスクへ適応された2つのモデルに対する互換性結果：$\phi_{\text{old}}$（ResNet-18）および $\phi_{\text{new}}$（ViT-L-16）について、逆方向アダプタとして $\lambda=12$ の $B_\lambda$ を用いている。ZS列はImageNet1KにおけるCMC-Top1性能の増加を示し、括弧内の値は新たに独立に学習したモデルと比較した増分を示す。各Query/Galleryの組合せは、結果の比較を容易にするため異なる色で強調されている。</caption>
<tbody>
<tr>
<td style="text-align: center;"><strong>78.23</strong> (<strong>+4.15</strong>)</td>
</tr>
</tbody>
</table></td>
<td style="text-align: center;"><strong>+0.112</strong></td>
</tr>
</tbody>
</table>

#### 部分的バックフィリング。

ギャラリー集合 $\Phi^\mathcal{G}$ 内の画像の順序 $\pi$ を、$\mathbf{x}_{\pi_1}, \mathbf{x}_{\pi_2}, \dots, \mathbf{x}_{\pi_n}$ と表す。また、バックフィリング比率 $\beta \in [0,1]$ を与えると、部分的にバックフィルされたギャラリー集合 $\Phi^\mathcal{G}_{\pi, \beta}$ を以下のように定義する。順序の先頭 $N_{g,\beta} = \lfloor \beta N_g \rfloor$ 枚の画像は更新後のモデルで処理し、残りの画像は旧モデルで処理する。ここで $N_g$ はギャラリー内の画像総数を表す。異なるバックフィリング戦略を評価するために、[[#^ref-22|22]]で導入されたバックフィリング指標 $\widetilde{M}$ を用いる。これは $\widetilde{M}(\Phi^\mathcal{G},\Phi^\mathcal{Q}, \pi) = \mathbb{E}_{\beta \sim [0,1]} M(\Phi^\mathcal{G}_{\pi, \beta},\Phi^\mathcal{Q}).$ と定義される。これは、$M$ によって性能を評価した際のバックフィリング曲線の下の面積である。

## 評価指標とデータセット 

モデル互換性に関する先行研究 [[#^ref-15|15]][[#^ref-25|25]] に従い、本研究では2つの指標を用いて性能を評価する。Cumulative Matching Characteristics（CMC）は、クエリ特徴とギャラリー特徴の距離を計算することにより top-$k$ の検索精度を測定し、$k$ 個の最も近いギャラリー画像の少なくとも1枚がクエリのラベルを共有していれば検索成功と見なす。mean Average Precision（mAP）は、再現率全域 $[0,1]$ にわたる精度再現率曲線の下の面積を測定する。

提案手法を検証するため、以下のデータセットを用いる：ImageNet1K [[#^ref-57|57]]、CIFAR100 [[#^ref-58|58]]、CUB200 [[#^ref-59|59]]。各データセットのvalidation/test set をクエリおよびギャラリーの両方として用い、検索時の自明な一致を避けるため、各クエリ画像はギャラリーから除外する。記法 'Query/Gallery' は、各表において埋め込みを抽出するために用いたモデルを、それぞれ示す。CUB200 と CIFAR100 は下流タスクとして用いる。

## クラス拡張設定

この設定では、クラス数を拡張することによってベースモデルを更新する。PyTorchの標準的な学習レシピ[^2]に従い、埋め込み次元128の ResNet-34 アーキテクチャを用いて、ImageNet1K の最初の500クラスで $\phi_{\text{old}}$ を、全1000クラスで $\phi_{\text{new}}$ を独立に学習する。2つのモデルを独立に学習した後、モデル層を凍結したまま、学習率 $0.001$ の Adam を用いてアダプタを最適化する。互換表現を実現するための2つの写像手法である FCT [[#^ref-25|25]] および FastFill [[#^ref-22|22]] と、本手法を比較する。Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) では、Sec. 4.2 の指標に従って各手法の性能を要約する。結果は、新しいモデル $\phi_{\text{new}}$ が旧モデル $\phi_{\text{old}}$ と直接互換ではないことを示している。さらに、2つの写像手法 FCT と FastFill は、適応後のギャラリー集合およびクエリ集合の表現について、両指標にわたり性能を向上させる。しかし、これらの手法は新たに学習されたモデルとの後方互換性は達成するが、元のモデルとの互換性は達成しない。これに対し、本手法は直交変換 $B_{\perp}$ によって新モデルと旧モデルを整合させる。これにより、新旧表現間の互換性が保証されるとともに、前方向アダプタ $F$ が提供する性能も向上する。Appendix 6 では Places365 [[#^ref-60|60]] データセットに関する追加結果を示す。

## 独立に事前学習されたモデルを下流タスクへ適応する場合 

訓練コストの増大に伴い、事前学習済みモデルは、特にローカルデータセットへの下流タスク適応において、ますます利用されている。この文脈では、PyTorch hub で利用可能な、ImageNet1K データセットで事前学習された2つのモデルを用いる。すなわち、埋め込みサイズ512の ResNet-18 と、より高度な Vision Transformer（ViT-L-16）[[#^ref-61|61]] で埋め込みサイズは1024である。ViTモデルは、その強化されたアーキテクチャにより、ResNet-18 の更新版と見なされる。Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) は、2つの事前学習済みモデルと同じデータセットを用いたアダプタ学習結果を示しており、Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) と同様の傾向を示すとともに、本手法が他のベースラインと同等の性能を達成しつつ、更新モデルと旧モデルの間の互換性を実現することを示している。FastFill と異なり、本手法は新モデルの分類器を必要とせず、抽出された埋め込みベクトルに直接依拠する。Appendix 7 では、本手法のさらなる検証のため、事前学習モデルとして用いられる異なるアーキテクチャに対して本手法を適用する。さらに Appendix 8 では、CLIP-like [[#^ref-62|62]] モデルや DINOv2 [[#^ref-63|63]] のような自己教師ありアーキテクチャを用いて、分布シフトまたは目的関数シフトを含む更新シナリオを検討する。

下流タスクにおける互換性の結果は Tab. 3 に示す。ここでは、アダプタを訓練データセットとは異なるローカルデータセット（CUB200 または CIFAR100）の表現上で学習している。$\lambda$-Orthogonality 正則化を伴う変換 $B_{\lambda}$ を用いることで、提案手法はローカルタスク性能とモデル互換性を向上させ、ベースラインを上回る。追加の下流データセット（Flower102 [[#^ref-64|64]] および Places365）に関する結果は Appendix 9 に報告する。Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) および Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) から、厳密な直交変換 $B_{\perp}$ は、独立に訓練されたモデル $\phi_{\text{new}}$ と比べて性能向上をもたらさないことが分かる。これに対し、$B_{\perp}$ に比べてより高い可塑性を与える $B_{\lambda}$ は、新しいモデルが下流タスクで性能を向上させることを可能にする。

ハイパーパラメータ $\lambda$ に関するアブレーション研究は Appendix 10 に示し、Eq. [\[eq:total_loss\]](#eq:total_loss) における損失項の構成要素ごとのアブレーションは Appendix 11 に詳述する。

<figure>
<p>![](assets/fig10.png)</p>
</figure>

<figure>
<p>![](assets/fig11.png)</p>
</figure>

[]

<table>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th colspan="2" style="text-align: center;">$\widetilde{M}$</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>2-3</span></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">mAP</td>
</tr>
<tr>
<td style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">58.72</td>
<td style="text-align: center;">33.57</td>
</tr>
<tr>
<td style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">60.49</td>
<td style="text-align: center;">35.59</td>
</tr>
<tr>
<td style="text-align: left;">Ours</td>
<td style="text-align: center;"><strong>61.20</strong></td>
<td style="text-align: center;"><strong>36.46</strong></td>
</tr>
</tbody>
</table>

<figure>
<p>![](assets/fig12.png)</p>
</figure>

<figure>
<p>![](assets/fig13.png)</p>
</figure>

[]

<table>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th colspan="2" style="text-align: center;">$\widetilde{M}$</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>2-3</span></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">mAP</td>
</tr>
<tr>
<td style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">73.86</td>
<td style="text-align: center;">52.02</td>
</tr>
<tr>
<td style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">75.06</td>
<td style="text-align: center;">55.34</td>
</tr>
<tr>
<td style="text-align: left;">Ours</td>
<td style="text-align: center;"><strong>76.59</strong></td>
<td style="text-align: center;"><strong>57.72</strong></td>
</tr>
</tbody>
</table>

[]

## Backfilling Results

本節では、Sec. 3.6 で議論した新規の backfill 戦略を評価する。実験設定は Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) および Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) に詳述したものを用いる。FCT には特定の backfilling 戦略が存在しないため、[[#^ref-22|22]] と同様にランダムな順序付けを用いる。Fig. [\[fig:backfill\]](#fig:backfill)、Tab. [\[tab:b_ext\]](#tab:b_ext)、および Tab. [\[tab:b_arch\]](#tab:b_arch) に示す結果は、提案する backfilling 戦略が他のベースラインを一定の差で上回ることを示している。特に、Fig. [\[fig:backfill\]](#fig:backfill) は、ギャラリーの 50% 未満を backfill した時点で、新たに独立に学習したモデルと同等の性能を達成できることを示している。Appendix 12 では、主実験で用いた Mean Squared Error に代わる距離尺度を用いたアブレーション研究を提示する。

# Conclusion 

モデル互換性は、多くの大規模検索システムにおける重要な課題であり、達成されない場合にはシステム更新を妨げうる。本論文では、独立に学習された表現を統一空間に整列させる写像変換を導入し、さらに supervised contrastive loss により、より強い特徴クラスタリングも実現する。また、新たに訓練された独立モデルの完全性を損なうことなく下流タスクへの適応を助けるため、直交制約の緩和を提案する。加えて、ギャラリー集合の効率的な部分 backfilling を可能にし、ギャラリーの半分未満を backfill するだけで新たに独立に学習したモデルと同等の性能を達成する、新規の backfill 順序付け戦略を提案する。提案手法は、モデルが学習された同一分布および異分布の双方において、従来手法を上回る優れた性能を示す。これらの結果を文脈化するため、手法の限界は Appendix 14 で詳細に検討する。さらに、その実用的有用性を評価するため、方法論的複雑性とより広範な適用可能性を Appendix 13 で分析する。

# Acknowledgments 

本論文は、プロジェクト "Collaborative Explainable neuro-symbolic AI for Decision Support Assistant"、CAI4DSA、CUP B13C23005640006 の支援を一部受けた。

# Extending Classes Setting on Places365 

提案手法をさらに検証するため、ImageNet1K とは異なるデータセットで学習されたモデルを用いて評価を行う。具体的には、Places205 で事前学習された ResNet-50（[ViSSL](https://github.com/facebookresearch/vissl/blob/main/MODEL_ZOO.md#supervised)）を old model とし、Places365 で事前学習された ResNet-50（[CSAILVision](https://github.com/CSAILVision/places365#pre-trained-cnn-models-on-places365-standard)）を new model とする。Tab. 4 は、Sec.4.2 で定義した評価指標を用いた各手法の性能を要約している。結果は、新しいモデル $\phi_{\text{new}}$ が本質的に old model $\phi_{\text{old}}$ と互換ではないことを示している。さらに、FCT によって与えられる適応 $F(\phi_{\text{old}})$ は、新しいモデル単体と比較して性能が劣る。これに対し、FastFill や提案手法のように、より良いクラスタリングを促進する手法は、単体の新しいモデルをさらに上回る性能を達成する。この改善は、old model と new model の双方からの情報を活用し、forward adapter の学習中に知識蒸留の一形態を実質的に実現していることに起因する。ベースラインとは異なり、提案手法はすべての適応済み表現を統一された表現空間に整列させ、それにより old model との互換性を一貫して維持する。

<table id="tab:app_places">
<caption>Compatibility evaluation on Places365 under the Extending Classes setting. We use two independently trained ResNet-50 models: $\phi_{\text{old}}$ trained on the first 205 classes, and $\phi_{\text{new}}$ trained on all classes of Places365.</caption>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: left;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">33.86</td>
<td style="text-align: center;">15.76</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.21</td>
<td style="text-align: center;">0.33</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">37.37</td>
<td style="text-align: center;">19.11</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.21</td>
<td style="text-align: center;">0.33</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">36.43</td>
<td style="text-align: center;">19.02</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">37.04</td>
<td style="text-align: center;">18.99</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.21</td>
<td style="text-align: center;">0.33</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">39.71</td>
<td style="text-align: center;">23.98</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">38.42</td>
<td style="text-align: center;">19.94</td>
</tr>
<tr>
<td rowspan="5" style="text-align: left;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>38.65</strong></td>
<td style="text-align: center;"><strong>21.88</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>39.96</strong></td>
<td style="text-align: center;"><strong>26.19</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>38.50</strong></td>
<td style="text-align: center;"><strong>21.77</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>35.47</strong></td>
<td style="text-align: center;"><strong>17.98</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">37.37</td>
<td style="text-align: center;">19.11</td>
</tr>
</tbody>
</table>

# Additional Architecture for Independently Pretrained Models Setting 

追加実験として、old model $\phi_{\text{old}}$ に DenseNet-121 を、new model $\phi_{\text{new}}$ に EfficientNet-B3 を用いる。両者はいずれも ImageNet1K で事前学習され、PyTorch Hub から取得した。これらの実験結果を ImageNet1K データセット上で Tab. 5 に示す。提案手法は全指標において最良性能を達成し、cross-model および same-model の双方の検索シナリオでベースラインを上回る。

<table id="tab:abl_arch">
<caption>Independently pretrained models設定におけるImageNet1K上の互換性結果である。旧モデル$\phi_{\text{old}}$としてDenseNet-121を、新モデル$\phi_{\text{new}}$としてEfficientNet-B3を用いた。両者ともImageNet1Kで事前学習され、PyTorch Hubから取得した。</caption>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: left;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">62.02</td>
<td style="text-align: center;">32.95</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.11</td>
<td style="text-align: center;">0.16</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">71.60</td>
<td style="text-align: center;">54.90</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.11</td>
<td style="text-align: center;">0.16</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">68.16</td>
<td style="text-align: center;">53.22</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">70.64</td>
<td style="text-align: center;">54.63</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.11</td>
<td style="text-align: center;">0.16</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">67.76</td>
<td style="text-align: center;">57.22</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">69.47</td>
<td style="text-align: center;">57.43</td>
</tr>
<tr>
<td rowspan="5" style="text-align: left;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>69.25</strong></td>
<td style="text-align: center;"><strong>50.20</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>69.29</strong></td>
<td style="text-align: center;"><strong>57.36</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>71.33</strong></td>
<td style="text-align: center;"><strong>57.50</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>67.23</strong></td>
<td style="text-align: center;"><strong>44.34</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">71.60</td>
<td style="text-align: center;">54.90</td>
</tr>
</tbody>
</table>

# DINOv2およびCLIPを独立事前学習モデルとして用いた追加実験

データ分布または目的関数の変化を伴う更新シナリオを調査するため，追加実験として，ImageNet1Kで事前学習されたResNet-18を旧モデルとし，CC12M [[#^ref-65|65]]データセットで事前学習されたCLIP [[#^ref-62|62]]およびDINOv2 [[#^ref-63|63]]（$vit\_small\_patch14\_dinov2$）を新モデルとして用いた。forward変換およびbackward変換の両方を訓練するために，ImageNet1Kデータセットと表[\[table:imagenet_arch\]](#table:imagenet_arch)と同じハイパーパラメータを用いた。この設定は，新モデルに対して，データ分布とモデル目的の両方において大きな変化を表している。なお，CLIPとDINOv2はいずれも分類器を持たないため，FastFillはこの文脈では適用できない。表[\[table:dino\]](#table:dino)では，新たな独立訓練モデルとしてDINOv2を用いた結果を報告する。我々の手法はFCTよりも良好な結果を達成しており，実世界の問題への実用的適用可能性をさらに裏付けている。

一方，表[\[table:clip\]](#table:clip)では，CC12Mで事前学習されたCLIPを新たな独立訓練モデルとして用いた結果を報告する。このシナリオでは，事前学習済みCLIPモデルはResNet-18と比較して，ImageNet1K上でより低い検索性能を示す。これはマルチモーダル学習におけるよく知られた制約であり，モダリティ内の不整合が単一モダリティ表現の品質に悪影響を及ぼし得る[[#^ref-66|66]]。具体的には，DINOv2やResNet-18が単一モダリティのみに対して学習されているのに対し，CLIPモデルは単一モダリティ検索タスクではなく，クロスモーダル検索に最適化されている。このように新モデルの性能が旧モデルより低下すると，FCTは，旧モデルの高品質な表現を新モデルの低性能な表現へ変換しようとするため，システム全体の検索能力を低下させ，互換性の達成に失敗する。対照的に，我々の手法は，特定の訓練データセット上でクラス内クラスタリングとモデル間の特徴表現整合の両方を促進する追加損失を導入する。その結果，より高い柔軟性を持つforward変換は，旧モデルの表現性能を改善する。この困難なシナリオにおいても，我々の手法はFCTを上回り，手法の頑健性をさらに検証している。

0.48

<table>
<thead>
<tr>
<th style="text-align: center;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: center;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">55.62</td>
<td style="text-align: center;">26.91</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">71.92</td>
<td style="text-align: center;">44.07</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">59.33</td>
<td style="text-align: center;">37.53</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">67.97</td>
<td style="text-align: center;">41.07</td>
</tr>
<tr>
<td rowspan="5" style="text-align: center;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>54.82</strong></td>
<td style="text-align: center;"><strong>32.14</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>61.30</strong></td>
<td style="text-align: center;"><strong>41.95</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>68.74</strong></td>
<td style="text-align: center;"><strong>43.78</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>58.73</strong></td>
<td style="text-align: center;"><strong>31.50</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">71.92</td>
<td style="text-align: center;">44.07</td>
</tr>
</tbody>
</table>

0.48

<table>
<thead>
<tr>
<th style="text-align: center;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th style="text-align: center;">CMC-Top1</th>
<th style="text-align: center;">mAP</th>
</tr>
</thead>
<tbody>
<tr>
<td rowspan="3" style="text-align: center;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">55.62</td>
<td style="text-align: center;">26.91</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">44.29</td>
<td style="text-align: center;">16.15</td>
</tr>
<tr>
<td rowspan="3" style="text-align: center;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">0.17</td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">42.58</td>
<td style="text-align: center;">16.93</td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">42.96</td>
<td style="text-align: center;">16.88</td>
</tr>
<tr>
<td rowspan="5" style="text-align: center;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>61.13</strong></td>
<td style="text-align: center;"><strong>41.22</strong></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>57.69</strong></td>
<td style="text-align: center;"><strong>41.08</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>44.93</strong></td>
<td style="text-align: center;"><strong>29.26</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>30.02</strong></td>
<td style="text-align: center;"><strong>16.68</strong></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;">44.29</td>
<td style="text-align: center;">16.15</td>
</tr>
</tbody>
</table>

# Downstream Task settingに適用された独立事前学習モデルのための追加データセット

我々は、Independently Pretrained Models Adapted on Downstream Task 設定に関する分析をさらに拡張し、より大規模な Places365 と、より細粒度な Flowers102 という2つの追加データセットを含めた。これらの追加により、より困難なシナリオにおける本手法の有効性を評価できる。結果は Tab. 8 に示す。これらの実験では、旧モデルは ResNet-18、新モデルは ViT-L-16 であり、いずれも ImageNet-1K で事前学習されている。我々は $\lambda = 12$ の affine adapter を用いる。追加の両データセットにおいて、提案手法は一貫してベースライン手法を上回る。提案する $\lambda$-Orthogonality 正則化は、下流タスクにおける retrieval 性能を向上させるだけでなく、適応後の新モデル表現 $B_{\lambda}(\phi_{\text{new}})$ が元の形を維持するようにも促す。その結果、ImageNet1K における retrieval 性能が保持される。

<table id="table:places-flowers">
<caption>ImageNet1K で事前学習され下流タスクに適応された2つのモデル、すなわち $\phi_{\text{old}}$ である ResNet-18 と $\phi_{\text{new}}$ である ViT-L-16 について、$\lambda=12$ の backward adapter $B_\lambda$ を用いた際の Places365 および Flowers102 における互換性結果。ZS 列は ImageNet1K における CMC-Top1 の性能増加を示し、括弧内の値は新たに独立学習したモデルと比較した増分を示す。</caption>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th style="text-align: center;">Query/Gallery</th>
<th colspan="2" style="text-align: center;"><strong>Places365</strong></th>
<th colspan="2" style="text-align: center;"><strong>Flowers102</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>3-6</span></td>
<td style="text-align: center;"></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">ZS</td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">ZS</td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">Ind. Train.</td>
<td style="text-align: center;">$\phi_{\text{old}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">22.41</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">84.35</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.20</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">1.20</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/\phi_{\text{new}}$</td>
<td style="text-align: center;">35.15</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">99.39</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FCT <span class="citation" data-cites="ramanujan2022forward"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.20</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">1.20</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">28.17</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">86.71</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">32.12</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">99.07</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="3" style="text-align: left;">FastFill <span class="citation" data-cites="jaeckle2023fastfill"></span></td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">0.20</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">1.20</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">26.38</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">53.78</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\phi_{\text{new}}/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">33.04</td>
<td style="text-align: center;"></td>
<td style="text-align: center;">11.12</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td rowspan="5" style="text-align: left;">Ours</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>28.84</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>83.36</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>29.80</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>89.90</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;"><strong>33.27</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>99.41</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;"><strong>29.94</strong></td>
<td style="text-align: center;"></td>
<td style="text-align: center;"><strong>98.17</strong></td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$</td>
<td style="text-align: center;"><table id="table:places-flowers">
<caption>ImageNet1K で事前学習され下流タスクに適応された2つのモデル、すなわち $\phi_{\text{old}}$ である ResNet-18 と $\phi_{\text{new}}$ である ViT-L-16 について、$\lambda=12$ の backward adapter $B_\lambda$ を用いた際の Places365 および Flowers102 における互換性結果。ZS 列は ImageNet1K における CMC-Top1 の性能増加を示し、括弧内の値は新たに独立学習したモデルと比較した増分を示す。</caption>
<tbody>
<tr>
<td style="text-align: center;"><strong>36.38</strong> (<strong>+1.23</strong>)</td>
</tr>
</tbody>
</table></td>
<td style="text-align: center;"><strong>+0.38</strong></td>
<td style="text-align: center;"><table id="table:places-flowers">
<caption>ImageNet1K で事前学習され下流タスクに適応された2つのモデル、すなわち $\phi_{\text{old}}$ である ResNet-18 と $\phi_{\text{new}}$ である ViT-L-16 について、$\lambda=12$ の backward adapter $B_\lambda$ を用いた際の Places365 および Flowers102 における互換性結果。ZS 列は ImageNet1K における CMC-Top1 の性能増加を示し、括弧内の値は新たに独立学習したモデルと比較した増分を示す。</caption>
<tbody>
<tr>
<td style="text-align: center;"><strong>99.54</strong> (<strong>+0.15</strong>)</td>
</tr>
</tbody>
</table></td>
<td style="text-align: center;"><strong>+0.01</strong></td>
</tr>
</tbody>
</table>

# ハイパーパラメータ $\boldsymbol{\lambda}$ に関するアブレーション

r0.5

![](assets/fig14.png)

我々の実験では、事前学習済みモデルの元の学習データセットである ImageNet1K における性能を保持しつつ、下流タスクへの適応性を最大化するように $\lambda$ を選択する。本手法の影響を示すため、Tab. 9 では、新たに事前学習したモデルに対して我々が提案する $\lambda$-orthogonal regularizer を適用して得られた CMC-Top1 スコアを報告する。結果は Fig. [\[fig:lambda ablation\]](#fig:lambda ablation) にも示されており、$\lambda$ を増加させることで新モデル表現の下流タスク性能が向上することを示している。

しかし、この改善は元データセットにおける性能低下を伴い、特に正則化がない場合（$\lambda = \infty$）には zero-shot（ZS）スコアの低下として顕著である。経験的には、$\lambda = 12$ に設定することが全指標にわたって最良のトレードオフを与えることが分かった。[[#^ref-36|36]] は、$\lambda = 0$ の場合に等しい soft orthogonality constraint を最適化している。しかし、この定式化は性能向上につながらず、厳密に orthogonal な変換の利用に劣る。Sec. 3.3 で議論したように、厳密な orthogonality を課すことは、モデルがタスク固有の情報を取り込む能力を妨げる可能性がある。これに対して我々の手法は、Gram 行列の単位行列からのずれを制御する調整可能なハイパーパラメータ $\lambda$ を導入することでこの制約を緩和し、表現の一貫性を保ちながら、より大きな柔軟性を許容する。

| $\lambda$ | $F(\phi_{\text{old}})/F(\phi_{\text{old}})$ | $B_{\lambda}(\phi_{\text{new}})/F(\phi_{\text{old}})$ |  | ZS |
|:---|:--:|:--:|:--:|:--:|
| $\perp$ (strict orth.) | 57.52 | 66.89 | 71.78 (+0.000) | +0.000 |
| 0 | 57.49 | 66.79 | 71.54 (--0.241) | --0.001 |
| 3 | 57.52 | 66.72 | 72.00 (+0.224) | +0.008 |
| 6 | 58.09 | 68.77 | 73.07 (+1.294) | +0.028 |
| **12** | [59.92]{.underline} | **70.72** | 75.44 (+3.659) | [+0.028]{.underline} |
| 16 | 59.68 | [70.21]{.underline} | 76.40 (+4.625) | **+0.062** |
| 22 | **60.20** | 69.50 | 77.89 (+6.109) | --0.318 |
| 36 | 59.32 | 63.34 | [78.77]{.underline} (+6.990) | --3.008 |
| $\infty$ (no reg.) | 59.26 | 62.84 | **78.89** (+7.110) | --3.526 |
**CUB データセットにおける orthogonal regularization 強度 $\lambda$ のアブレーション。対象タスク上の互換性指標と、ImageNet1K における zero-shot（ZS）CMC-Top1 の増分を示す。括弧内は、CUB データセットにおける独立学習済み新モデルに対する CMC-Top1 の増分を示す。**

本手法をさらに検証するため、$\lambda$-orthogonal regularization の損失寄与に対するスカラー重み $w$ の効果についても、2つの異なる orthogonal regularization、すなわち Soft Orthogonality（SO）[[#^ref-36|36]]——これは本手法における $\lambda = 0$ の特殊ケースに対応する——および Spectral Restricted Isometry Property（SRIP）[[#^ref-36|36]] と比較して調べる。正則化は、スカラー重みとして $w = 1$, $w = 10^{-1}$, $w = 10^{-2}$, $w = 10^{-3}$ の各値で検証する。さらに、厳密な orthogonality からのずれを示すため、学習終了時に backward transformation $B_{\lambda}$ によって達成された $\lVert W^{\top} W-I \rVert_F$ の正確な値を報告する列も追加する。

| $w$ | Method | $F(\phi_{\text{old}})/F(\phi_{\text{old}})$ | $B_{\lambda}(\phi_{\text{new}})/F(\phi_{\text{old}})$ | $B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$ | ZS | $\lVert W^{\top}W - I\rVert_F$ |
|:--:|:---|:--:|:--:|:--:|:--:|:--:|
| 1 | SO | 57.48 | 66.79 | 71.54 (--0.241) | --0.001 | 0.09 |
| 1 | SRIP | 57.38 | 66.57 | 71.66 (--0.120) | --0.001 | 0.08 |
| 1 | **Ours ($\lambda=12$)** | **59.92** | **70.72** | **75.44 (+3.659)** | **+0.028** | **12.05** |
| $10^{-1}$ | SO | 59.11 | 69.56 | 74.88 (+3.106) | +0.022 | 9.50 |
| $10^{-1}$ | SRIP | 58.88 | 63.58 | 78.77 (+6.990) | --1.467 | 29.55 |
| $10^{-1}$ | **Ours ($\lambda=12$)** | **59.93** | **70.70** | **75.20 (+3.419)** | **+0.076** | **12.12** |
| $10^{-2}$ | SO | 59.06 | 63.54 | 79.06 (+7.283) | --1.344 | 29.27 |
| $10^{-2}$ | SRIP | 59.23 | 63.42 | 78.73 (+6.955) | --3.077 | 35.42 |
| $10^{-2}$ | **Ours ($\lambda=12$)** | 59.06 | 63.54 | 79.06 (+7.283) | --1.344 | 29.27 |
| $10^{-3}$ | SO | 58.71 | 62.91 | 78.78 (+7.007) | --3.162 | 35.54 |
| $10^{-3}$ | SRIP | 58.83 | 63.18 | 78.92 (+7.145) | --3.457 | 38.63 |
| $10^{-3}$ | **Ours ($\lambda=12$)** | 58.71 | 62.91 | 78.78 (+7.007) | --3.162 | 35.54 |
**重みスケール $w$ が異なる直交正則化手法の比較である。下流タスク CUB200 における適合性指標と、ImageNet1K 上でのゼロショット（ZS）CMC-Top1 の向上を示す。括弧内は、独立に学習した新しいモデルに対する CMC-Top1 の増分を表す。最終列は $\lVert W^{\top}W - I\rVert_F$ の最終値を報告する。**

Tab. 10 に示すように、SRIP および SO のいずれにおいても、$\lVert W^{\top}W - I \rVert_F$ の最終値は最適化過程と選択されたスカラー重み $w$ によって左右される。我々の $\lambda$-orthogonal regularization とは異なり、これらの手法は $\lVert W^{\top}W - I \rVert_F$ を直接制御できない。すなわち、正則化項が総損失に占める寄与が小さくなると、逆変換 $B_{\lambda}$ に対する正則化効果も弱まる。正則化項のスカラー重み $w$ を小さくすると、特に MSE や contrastive loss $L_C$ のような競合する損失項が非直交変換を支持し得るため、最適化過程は正則化項を十分に最小化できなくなる。例えば、$w = 10^{-3}$ および $w = 10^{-2}$ のとき、SO、SRIP、そして我々の $\lambda$-orthogonal regularization による結果は、直交性制約が完全に無視される $\lambda = \infty$ の場合（Tab. 9 を参照）で観測される結果と同程度である。これは、$w$ が非常に小さい場合、最適化中における正則化項の寄与が無視できるほど小さくなるためである。こうした問題を回避するため、本手法では $\lambda$-orthogonal regularization に対して $w = 1$ と設定し、逆変換の学習中に正則化項が最適化過程へ実質的に組み込まれるようにしている。これにより、正則化項は目標しきい値 $\lambda$ を達成でき、逆変換における stability--plasticity のトレードオフを精密に制御し、下流タスクにおける表現適合性を向上させる。Tab. 10 の太字で示したように、本手法は SO および SRIP と比べて、$w = 1$ および $w = 10^{-1}$ において安定した結果を示す（小さな変動は確率的最適化に起因する）。一方、$w$ が非常に低い場合（$10^{-2}$ または $10^{-3}$）、正則化項を十分に最適化できず、本手法は SO 正則化と同様に振る舞う。これは、我々が導入した制約（$\lVert W^{\top}W - I\rVert_F\geq\lambda$）が目的関数の最小値に影響を与えるものの、実際にはその最小値が到達されないためである。対照的に、近似的な定式化であり、SO と比べて複雑性も高い SRIP は、$w$ が低いときにさらに弱い正則化効果しか示さない。

# 損失項の寄与に関する詳細分析 

本節では、学習中に最適化される最終損失（Eq. [\[eq:total_loss\]](#eq:total_loss)）に対する各項の寄与を分析する。Tab. 11 は、適応データセットが、抽出された特徴の学習に用いられたモデルの訓練データセット、すなわち ImageNet1K と一致する場合の結果を示す。この設定では、逆方向の互換性のために厳密な直交変換 $B_{\perp}$ を用いる。このとき、$\mathcal{L}_{F}$ を単独で用いると、新しいモデルの表現との互換性は確保されるが、逆方向の互換性の達成には著しく失敗することが分かる。この挙動は、$\mathcal{L}_{F}$ に内在する顕著な forward bias を示している。逆方向整列損失 $\mathcal{L}_{B}$ のみでは、逆方向の互換性は促進されるが、forward-adapted な表現性能は低下する。contrastive loss $\mathcal{L}_{C}$ のみでは、モデル間整列およびクラス内クラスタリングが大幅に改善され、逆方向と順方向の双方の互換性を支援する。$\mathcal{L}_{F} + \mathcal{L}_{B} + \mathcal{L}_{C}$ の組合せは、互換性シナリオ全体にわたって最も高い総合性能を達成し、forward transformation learning と backward transformation learning の均衡を維持する上で各損失成分が重要であることを示している。

Tab. 12 は、下流タスク設定（CUB データセット）におけるこれらの損失項の影響を示す。このとき $\phi_{old}$ は ResNet-18、$\phi_{new}$ は ViT-L-16 であり、$\lambda = 12$ の $\lambda$-Orthogonality を用いている。Tab. 11 と同様に、逆方向損失 $\mathcal{L}_{B}$ を除外しても forward compatibility は良好に保たれるが、backward compatibility の性能は著しく低下する。contrastive loss $\mathcal{L}_{C}$ を除外すると、下流タスクへの適応が大幅に低下し、$B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$ の値が低くなる。すべての損失項 $\mathcal{L}_{F} + \mathcal{L}_{B} + \mathcal{L}_{C}$ を用いると、forward および backward compatibility の双方で一貫して最良またはほぼ最良の結果が得られ、これらの項が相補的であることが示される。

これらの分析は、各損失項が、さまざまなタスクにわたって包括的なモデル互換性を達成するうえで、それぞれ独自かつ有意に寄与していることを示している。

<table id="tab:loss_combo_cmc_tick">
<caption>CMC-Top1 (%) on ImageNet1K for different loss combinations ($\checkmark$ = included, $\times$ = excluded). The setting is the same of Tab. <a href="#table:imagenet_arch" data-reference-type="ref" data-reference="table:imagenet_arch">[table:imagenet_arch]</a>, where the first model, $\phi_{\text{old}}$, is a ResNet-18, whereas the second, $\phi_{\text{new}}$, is a ViT-L-16.</caption>
<thead>
<tr>
<th colspan="3" style="text-align: center;">Losses</th>
<th colspan="5" style="text-align: center;">Query/Gallery (CMC-Top1 %)</th>
<th style="text-align: center;"></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">$\mathcal{L}_F$</td>
<td style="text-align: center;">$\mathcal{L}_{B}$</td>
<td style="text-align: center;">$\mathcal{L}_C$</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">$B_{\perp}(\phi_{\text{new}})/B_{\perp}(\phi_{\text{new}})$</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">59.09</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">72.27</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">49.34</td>
<td style="text-align: center;">62.75</td>
<td style="text-align: center;">0.04</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">61.24</td>
<td style="text-align: center;">58.63</td>
<td style="text-align: center;">64.97</td>
<td style="text-align: center;">60.83</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">54.18</td>
<td style="text-align: center;">59.29</td>
<td style="text-align: center;">62.77</td>
<td style="text-align: center;">72.46</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;"><strong>61.25</strong></td>
<td style="text-align: center;">60.43</td>
<td style="text-align: center;">65.13</td>
<td style="text-align: center;">73.44</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">60.85</td>
<td style="text-align: center;">59.09</td>
<td style="text-align: center;">65.42</td>
<td style="text-align: center;">57.90</td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">60.83</td>
<td style="text-align: center;"><strong>61.10</strong></td>
<td style="text-align: center;"><strong>65.54</strong></td>
<td style="text-align: center;"><strong>73.53</strong></td>
<td style="text-align: center;">76.63</td>
<td style="text-align: center;"></td>
</tr>
</tbody>
</table>

<table id="tab:loss_combo_cmc_tick_2">
<caption>異なる損失の組合せに対するCUB上のCMC-Top1 (%)（$\checkmark$ = 含む, $\times$ = 除外）。設定はTab. <a href="#table:cub" data-reference-type="ref" data-reference="table:cub">3</a>と同一であり、1つ目のモデル $\phi_{\text{old}}$ は ResNet-18、2つ目の $\phi_{\text{new}}$ は ViT-L-16 である。改善されたモデルを下流タスクに適応させるため、$\lambda=12$ の backward adapter $B_\lambda$ を用いる。</caption>
<thead>
<tr>
<th colspan="3" style="text-align: center;">損失</th>
<th colspan="5" style="text-align: center;">Query/Gallery (CMC-Top1 %)</th>
<th style="text-align: center;"></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">$\mathcal{L}_F$</td>
<td style="text-align: center;">$\mathcal{L}_{B}$</td>
<td style="text-align: center;">$\mathcal{L}_C$</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">$F(\phi_{\text{old}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/\phi_{\text{old}}$</td>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/F(\phi_{\text{old}})$</td>
<td style="text-align: center;">$B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">0.0</td>
<td style="text-align: center;">51.72</td>
<td style="text-align: center;">0.0</td>
<td style="text-align: center;">63.82</td>
<td style="text-align: center;">72.14</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">0.0</td>
<td style="text-align: center;">35.27</td>
<td style="text-align: center;">45.80</td>
<td style="text-align: center;">0.0</td>
<td style="text-align: center;">71.91</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">37.15</td>
<td style="text-align: center;">47.56</td>
<td style="text-align: center;">46.56</td>
<td style="text-align: center;">60.70</td>
<td style="text-align: center;">69.76</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">52.79</td>
<td style="text-align: center;">59.14</td>
<td style="text-align: center;">58.38</td>
<td style="text-align: center;">66.46</td>
<td style="text-align: center;">73.36</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">50.43</td>
<td style="text-align: center;">59.88</td>
<td style="text-align: center;">58.57</td>
<td style="text-align: center;">70.13</td>
<td style="text-align: center;">74.86</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\times$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;"><strong>53.27</strong></td>
<td style="text-align: center;">58.66</td>
<td style="text-align: center;">60.45</td>
<td style="text-align: center;">59.44</td>
<td style="text-align: center;">73.12</td>
<td style="text-align: center;"></td>
</tr>
<tr>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">$\checkmark$</td>
<td style="text-align: center;">51.12</td>
<td style="text-align: center;"><strong>59.92</strong></td>
<td style="text-align: center;"><strong>60.64</strong></td>
<td style="text-align: center;"><strong>70.72</strong></td>
<td style="text-align: center;"><strong>75.44</strong></td>
<td style="text-align: center;"></td>
</tr>
</tbody>
</table>

# 部分バックフィリング順序のための距離尺度

我々が提案する部分バックフィリング戦略は、各埋め込みベクトル $F(\mathbf{h}^k)$ と対応するクラス平均 $\boldsymbol{\mu}_c$ との非類似度を測る距離尺度 $d$ によって導かれる。本節では、ギャラリー集合内の画像をバックフィリングする際に有効な順序を決定するうえで、異なる距離尺度が与える影響を検討する。部分バックフィリングにおける画像の順位付けについて、2つの距離尺度、すなわち Mean Squared Error (MSE) と Cosine Distance を比較する。各尺度の性能は、Extending Classes 設定（Tab. [\[tab:b_ext_abl\]](#tab:b_ext_abl)）および Independently Pretrained Models 設定（Tab. [\[tab:b_arch_abl\]](#tab:b_arch_abl)）という2つの異なる実験条件の下で評価する。MSE は特徴ベクトル間のユークリッド距離を計算し、角度的差異と大きさの差異の両方を捉える。Tab. [\[tab:b_ext_abl\]](#tab:b_ext_abl) および Tab. [\[tab:b_arch_abl\]](#tab:b_arch_abl) に示すとおり、MSE は一般に堅牢な性能を示し、とりわけ CMC-Top1 の観点で優れている。これに対し、Cosine Distance は正規化された特徴ベクトル間の角度距離を測定し、大きさを無視して方向の類似性を強調する。結果から、Cosine Distance は mAP の観点でわずかに良好な性能を示し、CMC-Top1 スコアにおいては MSE と同等の性能を達成することが示される。

<figure>
<p>![](assets/fig15.png)</p>
</figure>

<figure>
<p>![](assets/fig16.png)</p>
</figure>

[]

<table>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th colspan="2" style="text-align: center;">$\widetilde{M}$</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>2-3</span></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">mAP</td>
</tr>
<tr>
<td style="text-align: left;">MSE</td>
<td style="text-align: center;">61.20</td>
<td style="text-align: center;">36.46</td>
</tr>
<tr>
<td style="text-align: left;">Cosine Distance</td>
<td style="text-align: center;"><strong>61.68</strong></td>
<td style="text-align: center;"><strong>37.10</strong></td>
</tr>
</tbody>
</table>

<figure>
<p>![](assets/fig17.png)</p>
</figure>

<figure>
<p>![](assets/fig18.png)</p>
</figure>

[]

<table>
<thead>
<tr>
<th style="text-align: left;">Method</th>
<th colspan="2" style="text-align: center;">$\widetilde{M}$</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>2-3</span></td>
<td style="text-align: center;">CMC-Top1</td>
<td style="text-align: center;">mAP</td>
</tr>
<tr>
<td style="text-align: left;">MSE</td>
<td style="text-align: center;"><strong>76.59</strong></td>
<td style="text-align: center;">57.72</td>
</tr>
<tr>
<td style="text-align: left;">Cosine Distance</td>
<td style="text-align: center;">76.49</td>
<td style="text-align: center;"><strong>58.18</strong></td>
</tr>
</tbody>
</table>

[]

# 方法の複雑性とより広い適用可能性

#### 方法の複雑性.

我々の手法では、学習すべき行列は2つのみであり、最適化すべきパラメータ数は少ない。さらに、本手法は抽出済み埋め込みのみを用いて動作するため、基盤となるモデルに関する知識を一切必要とせず、したがって異なる目的関数（Appendix 8 参照）、アーキテクチャ、ならびに学習された表現の種類をまたいで適用可能である。

先行手法が、いずれも整列損失のみに焦点を当て、表現クラスタリング損失を持たない場合（例えば FCT [[#^ref-25|25]]）、あるいは事前学習済みモデルの特定のアーキテクチャ構成要素を必要とする場合（例えば FastFill [[#^ref-22|22]] は新しいモデルの分類器へのアクセスを必要とする）とは対照的に、我々の手法はこれらの制約を解消する。加えて、既存のベースラインが前方適応のみを提供するのに対し、本手法は前方互換性と後方互換性の双方を達成するよう設計されており、先行研究が満たしていない実用上の要請に対応する。例えば以下が挙げられる。

- $B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$ は、ベースラインと比較してより高い検索値を与える。

- $B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$ は我々の手法によってのみ実現可能である。実用上、これは、すべてのギャラリー項目が $F$ によって前方適応される前であっても互換性を確立できることを意味する。

- 我々の手法は統一的な表現空間を提供するため、ギャラリーがハイブリッドな形態、すなわち一部の要素はすでに $F$ によって適応され、他はまだ適応されていない状態であっても、$B_{\perp}(\phi_{\text{new}})$ を用いることで互換性はなお保証される。これは FCT [[#^ref-25|25]] によっても FastFill [[#^ref-22|22]] によっても実現できない。

式[\[eq:contr\]](#eq:contr)で定義される対比損失は、同一クラスの埋め込みを互いに近づけ、異なるクラスの埋め込みを引き離すよう促すために、クラスラベルの利用に依拠している。クラスラベルが利用できないシナリオでは、式[\[eq:contr\]](#eq:contr)は自然に教師なし対比損失へと還元され、CLIPモデルの学習に用いられる目的関数 [[#^ref-62|62]] に類似する。この教師なし設定では、異なるモデルに由来する表現の対を対比させるが、クラスタリングは直接的には強制できないため、埋め込みの類似性の結果として副次的に生じる。したがって、本手法は柔軟であり、下流タスクにおけるラベルの利用可能性に応じて、教師あり学習と教師なし学習の双方に適用可能である。

#### より広い適用可能性.

[[#^ref-36|36]] で示されているように、soft orthogonalization は学習中の CNN の全重みを正則化するために適用されており、我々が提案する $\lambda$-orthogonal regularization によって与えられる高い可塑性の恩恵を受けうる。検索は互換性評価の標準的なシナリオであるが [[#^ref-15|15]]、我々の手法は、モデル整列と学習表現のクラスタリングに焦点を当てているため、表現適応を必要とするあらゆるタスクに広く適用可能である。下流タスク適応の実験（Sec. 4.4 参照）で示したように、我々の正則化手法は厳格な直交制約と比べてより良い性能を達成し、ドメイン適応シナリオにおいても有用である。さらに、適応性を許容しつつ幾何学的一貫性を強制することは、近年 multimodal training における continual learning の文脈で検討されている [[#^ref-67|67]]。しかし、[[#^ref-67|67]] の著者らは、この性質を正則化制約を直接適用するのではなく、知識集約損失を通じて間接的に促進している。これは、今後の研究の可能性と、表現学習のさまざまな分野における我々の $\lambda$-orthogonal regularization の潜在的適用可能性の双方を示している。

# 制約事項

我々の手法は、新しいモデルの埋め込み空間が旧モデルのそれよりも表現力が高い（例えば、検索精度が高い、クラスタリング性能が強い）という仮定に依拠している。更新後のモデルが同等でない、あるいは品質が低い場合、たとえばドメイン不一致、訓練データ不足、あるいはアーキテクチャ上の退行による場合には、順方向および逆方向の両アダプタはいずれも性能向上に失敗し、互換性をむしろ低下させる可能性がある。多くの実用システムでは、この仮定はスケーリング則 [[#^ref-68|68]][[#^ref-69|69]][[#^ref-70|70]][[#^ref-71|71]]（すなわち、より大きなモデルとより多くのデータは一般により優れた特徴表現をもたらす）によって正当化される。下流タスクへの適応については、我々の$\lambda$-orthogonal正則化アダプタは、さまざまな検索タスクにわたって高い性能と互換性を示す一方で、直交性しきい値（$\lambda$）の手動調整が必要である。元のモデルの幾何構造を保持することと、新しいデータへ適応するための十分な可塑性を許容することとのトレードオフは、$\lambda$ の選択に決定的に依存する。実運用では、このハイパーパラメータは、交差検証または下流データセットの保持部分に対する小規模なハイパーパラメータ探索によって選択できる。我々の実験では $\lambda=12$ が良好なバランスを与えることを確認したが（Appendix 10）、異なる下流ドメイン（例えば、細粒度カテゴリと粗粒度カテゴリ）や適応後の表現では、最適性能を達成するために $\lambda$ の別個の調整が必要となる場合がある。このパラメータの自動化または自己調整は、なお未解決の課題である。

[^1]: Corresponding author: `simone.ricci@unifi.it`.

[^2]: [pytorch/vision/tree/main/references/classification](https://github.com/pytorch/vision/tree/main/references/classification)

## References

[1] Florian Schroff, Dmitry Kalenichenko, and James Philbin. Facenet: A unified embedding for face recognition and clustering. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 815-823, 2015. ^ref-1

[2] Weiyang Liu, Yandong Wen, Zhiding Yu, Ming Li, Bhiksha Raj, and Le Song. Sphereface: Deep hypersphere embedding for face recognition. In 2017 IEEE Conference on Computer Vision and Pattern Recognition, CVPR 2017, Honolulu, HI, USA, July 21-26, 2017, pages 6738-6746. IEEE Computer Society, 2017. ^ref-2

[3] Jiankang Deng, Jia Guo, Niannan Xue, and Stefanos Zafeiriou. Arcface: Additive angular margin loss for deep face recognition. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 4690-4699, 2019. ^ref-3

[4] Relja Arandjelovic, Petr Gronat, Akihiko Torii, Tomas Pajdla, and Josef Sivic. Netvlad: Cnn architecture for weakly supervised place recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 5297-5307, 2016. ^ref-4

[5] Bingyi Cao, Andre Araujo, and Jack Sim. Unifying deep local and global features for image search. In Computer Vision-ECCV 2020: 16th European Conference, Glasgow, UK, August 23-28, 2020, Proceedings, Part XX 16, pages 726-743. Springer, 2020. ^ref-5

[6] Stephen Hausler, Sourav Garg, Ming Xu, Michael Milford, and Tobias Fischer. Patch-netvlad: Multi-scale fusion of locally-global descriptors for place recognition. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 14141-14152, 2021. ^ref-6

[7] Hyeonwoo Noh, Andre Araujo, Jack Sim, Tobias Weyand, and Bohyung Han. Large-scale image retrieval with attentive deep local features. In Proceedings of the IEEE international conference on computer vision, pages 3456-3465, 2017. ^ref-7

[8] Fuwen Tan, Jiangbo Yuan, and Vicente Ordonez. Instance-level image retrieval using reranking transformers. In proceedings of the IEEE/CVF international conference on computer vision, pages 12105-12115, 2021. ^ref-8

[9] Bin Yan, Yi Jiang, Jiannan Wu, Dong Wang, Ping Luo, Zehuan Yuan, and Huchuan Lu. Universal instance perception as object discovery and retrieval. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 15325-15336, 2023. ^ref-9

[10] Colin Raffel. Building machine learning models like open source software. Commun. ACM, 66(2):38–40, jan 2023. ^ref-10

[11] Prateek Yadav, Colin Raffel, Mohammed Muqeeth, Lucas Caccia, Haokun Liu, Tianlong Chen, Mohit Bansal, Leshem Choshen, and Alessandro Sordoni. A survey on model moerging: Recycling and routing among specialized experts for collaborative learning. Trans. Mach. Learn. Res., 2025. ^ref-11

[12] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timoth\'ee Lacroix, Baptiste Rozi\`ere, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971, 2023. ^ref-12

[13] Niccolò Biondi, Federico Pernici, Simone Ricci, and Alberto Del Bimbo. Stationary representations: Optimally approximating compatibility and implications for improved model replacements. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2024. ^ref-13

[14] Jessica Maria Echterhoff, Fartash Faghri, Raviteja Vemulapalli, Ting-Yao Hu, Chun-Liang Li, Oncel Tuzel, and Hadi Pouransari. MUSCLE: A model update strategy for compatible LLM evolution. In EMNLP (Findings), pages 7320-7332. Association for Computational Linguistics, 2024. ^ref-14

[15] Yantao Shen, Yuanjun Xiong, Wei Xia, and Stefano Soatto. Towards backward-compatible representation learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 6368-6377, 2020. ^ref-15

[16] Yixuan Li, Jason Yosinski, Jeff Clune, Hod Lipson, and John Hopcroft. Convergent learning: Do different neural networks learn the same representations? In Yoshua Bengio and Yann LeCun, editors, Feature Extraction: Modern Questions and Challenges, pages 196-212. PMLR, 2015. ^ref-16

[17] Sijie Yan, Yuanjun Xiong, Kaustav Kundu, Shuo Yang, Siqi Deng, Meng Wang, Wei Xia, and Stefano Soatto. Positive-congruent training: Towards regression-free model updates. In CVPR, pages 14299-14308. Computer Vision Foundation / IEEE, 2021. ^ref-17

[18] Niccolo Biondi, Federico Pernici, Matteo Bruni, and Alberto Del Bimbo. Cores: Compatible representations via stationarity. IEEE Transactions on Pattern Analysis and Machine Intelligence, pages 1-16, 2023. ^ref-18

[19] Mitchell Wortsman, Gabriel Ilharco, Samir Ya Gadre, Rebecca Roelofs, Raphael Gontijo-Lopes, Ari S Morcos, Hongseok Namkoong, Ali Farhadi, Yair Carmon, Simon Kornblith, et al. Model soups: averaging weights of multiple fine-tuned models improves accuracy without increasing inference time. In International conference on machine learning, pages 23965-23998. PMLR, 2022. ^ref-19

[20] Binjie Zhang, Yixiao Ge, Yantao Shen, Shupeng Su, Fanzi Wu, Chun Yuan, Xuyuan Xu, Yexin Wang, and Ying Shan. Towards universal backward-compatible representation learning. In IJCAI, pages 1615-1621. ijcai.org, 2022. ^ref-20

[21] Qiang Meng, Chixiang Zhang, Xiaoqiang Xu, and Feng Zhou. Learning compatible embeddings. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), pages 9939-9948, October 2021. ^ref-21

[22] Florian Jaeckle, Fartash Faghri, Ali Farhadi, Oncel Tuzel, and Hadi Pouransari. Fastfill: Efficient compatible model update. In International Conference on Learning Representations, 2023. ^ref-22

[23] Yifei Zhou, Zilu Li, Abhinav Shrivastava, Hengshuang Zhao, Antonio Torralba, Taipeng Tian, and Ser-Nam Lim. Bt\^ 2: Backward-compatible training with basis transformation. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pages 11229-11238, 2023. ^ref-23

[24] Simone Ricci, Niccol\`o Biondi, Federico Pernici, and Alberto Del Bimbo. Backward-compatible aligned representations via an orthogonal transformation layer. In ECCV Workshops (17), volume 15639 of Lecture Notes in Computer Science, pages 451-464. Springer, 2024. ^ref-24

[25] Vivek Ramanujan, Pavan Kumar Anasosalu Vasu, Ali Farhadi, Oncel Tuzel, and Hadi Pouransari. Forward compatible training for large-scale embedding retrieval systems. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 19386-19395, 2022. ^ref-25

[26] Charles Fefferman, Sanjoy Mitter, and Hariharan Narayanan. Testing the manifold hypothesis. Journal of the American Mathematical Society, 29(4):983-1049, 2016. ^ref-26

[27] Minyoung Huh, Brian Cheung, Tongzhou Wang, and Phillip Isola. Position: The platonic representation hypothesis. In ICML. OpenReview.net, 2024. ^ref-27

[28] Valentino Maiorca, Luca Moschella, Antonio Norelli, Marco Fumero, Francesco Locatello, and Emanuele Rodol\`a. Latent space translation via semantic alignment. Advances in Neural Information Processing Systems, 36, 2024. ^ref-28

[29] Marco Fumero, Marco Pegoraro, Valentino Maiorca, Francesco Locatello, and Emanuele Rodol\`a. Latent functional maps: a spectral framework for representation alignment. In NeurIPS, 2024. ^ref-29

[30] Luca Moschella, Valentino Maiorca, Marco Fumero, Antonio Norelli, Francesco Locatello, and Emanuele Rodol\`a. Relative representations enable zero-shot latent space communication. In International Conference on Learning Representations, 2023. ^ref-30

[31] Valentino Maiorca, Luca Moschella, Marco Fumero, Francesco Locatello, and Emanuele Rodol\`a. Latent space translation via inverse relative projection. arXiv preprint arXiv:2406.15057, 2024. ^ref-31

[32] Martial Mermillod, Aur\'elia Bugaiska, and Patrick Bonin. The stability-plasticity dilemma: Investigating the continuum from catastrophic forgetting to age-limited learning effects, 2013. ^ref-32

[33] Guoliang Lin, Hanlu Chu, and Hanjiang Lai. Towards better plasticity-stability trade-off in incremental learning: A simple linear connector. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 89-98, 2022. ^ref-33

[34] Dongwan Kim and Bohyung Han. On the stability-plasticity dilemma of class-incremental learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 20196-20204, 2023. ^ref-34

[35] Lirong Wu, Zicheng Liu, Jun Xia, Zelin Zang, Siyuan Li, and Stan Z Li. Generalized clustering and multi-manifold learning with geometric structure preservation. In Proceedings of the IEEE/CVF winter conference on applications of computer vision, pages 139-147, 2022. ^ref-35

[36] Nitin Bansal, Xiaohan Chen, and Zhangyang Wang. Can we gain more from orthogonality regularizations in training deep networks? Advances in Neural Information Processing Systems, 31, 2018. ^ref-36

[37] Binjie Zhang, Yixiao Ge, Yantao Shen, Yu Li, Chun Yuan, XUYUAN XU, Yexin Wang, and Ying Shan. Hot-refresh model upgrades with regression-free compatible training in image retrieval. In International Conference on Learning Representations, 2021. ^ref-37

[38] Tan Pan, Furong Xu, Xudong Yang, Sifeng He, Chen Jiang, Qingpei Guo, Feng Qian, Xiaobo Zhang, Yuan Cheng, Lei Yang, et al. Boundary-aware backward-compatible representation via adversarial learning in image retrieval. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 15201-15210, 2023. ^ref-38

[39] Mateusz Budnik and Yannis Avrithis. Asymmetric metric learning for knowledge transfer. In CVPR, pages 8228-8238. Computer Vision Foundation / IEEE, 2021. ^ref-39

[40] Niccolo Biondi, Federico Pernici, Matteo Bruni, Daniele Mugnai, and Alberto Del Bimbo. Cl2r: Compatible lifelong learning representations. ACM Transactions on Multimedia Computing, Communications and Applications, 18(2s):1-22, 2023. ^ref-40

[41] Ahmet Iscen, Jeffrey Zhang, Svetlana Lazebnik, and Cordelia Schmid. Memory-efficient incremental learning through feature adaptation. In European Conference on Computer Vision, pages 699-715. Springer, 2020. ^ref-41

[42] Chien-Yi Wang, Ya-Liang Chang, Shang-Ta Yang, Dong Chen, and Shang-Hong Lai. Unified representation learning for cross model compatibility. In 31st British Machine Vision Conference 2020, BMVC 2020. BMVA Press, 2020. ^ref-42

[43] Shupeng Su, Binjie Zhang, Yixiao Ge, Xuyuan Xu, Yexin Wang, Chun Yuan, and Ying Shan. Privacy-preserving model upgrades with bidirectional compatible training in image retrieval. arXiv preprint arXiv:2204.13919, 2022. ^ref-43

[44] Chang Wang and Sridhar Mahadevan. Manifold alignment using procrustes analysis. In Proceedings of the 25th international conference on Machine learning, pages 1120-1127, 2008. ^ref-44

[45] Mario Lezcano-Casado and David Mart-Rubio. Cheap orthogonal constraints in neural networks: A simple parametrization of the orthogonal and unitary group. In International Conference on Machine Learning, pages 3794-3803. PMLR, 2019. ^ref-45

[46] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the national academy of sciences, 114(13):3521-3526, 2017. ^ref-46

[47] Ronald Kemker, Marc McClure, Angelina Abitino, Tyler Hayes, and Christopher Kanan. Measuring catastrophic forgetting in neural networks. In Proceedings of the AAAI conference on artificial intelligence, volume 32, 2018. ^ref-47

[48] Mehrtash Harandi and Basura Fernando. Generalized backpropagation, etude de cas: Orthogonality. arXiv preprint arXiv:1611.05927, 2016. ^ref-48

[49] Mete Ozay and Takayuki Okatani. Optimization on submanifolds of convolution kernels in cnns. arXiv preprint arXiv:1610.07008, 2016. ^ref-49

[50] Lei Huang, Xianglong Liu, Bo Lang, Adams Yu, Yongliang Wang, and Bo Li. Orthogonal weight normalization: Solution to optimization over multiple dependent stiefel manifolds in deep neural networks. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 32, 2018. ^ref-50

[51] Milton Abramowitz and Irene A Stegun. Handbook of mathematical functions with formulas, graphs, and mathematical tables, volume 55. US Government printing office, 1968. ^ref-51

[52] Sagar Sharma, Simone Sharma, and Anidhya Athaiya. Activation functions in neural networks. Towards Data Sci, 6(12):310-316, 2017. ^ref-52

[53] A Iliev, Nikolay Kyurkchiev, and Svetoslav Markov. On the approximation of the step function by some sigmoid functions. Mathematics and Computers in Simulation, 133:223-234, 2017. ^ref-53

[54] Yonglong Tian, Lijie Fan, Phillip Isola, Huiwen Chang, and Dilip Krishnan. Stablerep: Synthetic images from text-to-image models make strong visual representation learners. Advances in Neural Information Processing Systems, 36, 2024. ^ref-54

[55] Bj\"orn Barz and Joachim Denzler. Hierarchy-based image embeddings for semantic image retrieval. In 2019 IEEE winter conference on applications of computer vision (WACV), pages 638-647. IEEE, 2019. ^ref-55

[56] Mikolaj Wieczorek, Barbara Rychalska, and Jacek Dabrowski. On the unreasonable effectiveness of centroids in image retrieval. In Neural Information Processing: 28th International Conference, ICONIP 2021, Sanur, Bali, Indonesia, December 8-12, 2021, Proceedings, Part IV 28, pages 212-223. Springer, 2021. ^ref-56

[57] Olga Russakovsky, Jia Deng, Hao Su, Jonathan Krause, Sanjeev Satheesh, Sean Ma, Zhiheng Huang, Andrej Karpathy, Aditya Khosla, Michael Bernstein, et al. Imagenet large scale visual recognition challenge. International journal of computer vision, 115(3):211-252, 2015. ^ref-57

[58] A. Krizhevsky. Learning Multiple Layers of Features from Tiny Images. Technical report, Univ. Toronto, 2009. ^ref-58

[59] Catherine Wah, Steve Branson, Peter Welinder, Pietro Perona, and Serge Belongie. The caltech-ucsd birds-200-2011 dataset. 2011. ^ref-59

[60] Bolei Zhou, Agata Lapedriza, Aditya Khosla, Aude Oliva, and Antonio Torralba. Places: A 10 million image database for scene recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2017. ^ref-60

[61] Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, Jakob Uszkoreit, and Neil Houlsby. An image is worth 16x16 words: Transformers for image recognition at scale. In 9th International Conference on Learning Representations, ICLR 2021, Virtual Event, Austria, May 3-7, 2021. OpenReview.net, 2021. ^ref-61

[62] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In International conference on machine learning, pages 8748-8763. PmLR, 2021. ^ref-62

[63] Maxime Oquab, Timoth\'ee Darcet, Th\'eo Moutakanni, Huy V Vo, Marc Szafraniec, Vasil Khalidov, Pierre Fernandez, Daniel HAZIZA, Francisco Massa, Alaaeldin El-Nouby, et al. Dinov2: Learning robust visual features without supervision. Transactions on Machine Learning Research. ^ref-63

[64] Maria-Elena Nilsback and Andrew Zisserman. Automated flower classification over a large number of classes. In 2008 Sixth Indian conference on computer vision, graphics \& image processing, pages 722-729. IEEE, 2008. ^ref-64

[65] Soravit Changpinyo, Piyush Sharma, Nan Ding, and Radu Soricut. Conceptual 12m: Pushing web-scale image-text pre-training to recognize long-tail visual concepts. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 3558-3568, 2021. ^ref-65

[66] Marco Mistretta, Alberto Baldrati, Lorenzo Agnolucci, Marco Bertini, and Andrew D. Bagdanov. Cross the gap: Exposing the intra-modal misalignment in CLIP via modality inversion. In The Thirteenth International Conference on Learning Representations, ICLR 2025, Singapore, April 24-28, 2025. OpenReview.net, 2025. ^ref-66

[67] Wenzhuo Liu, Fei Zhu, Longhui Wei, and Qi Tian. C-clip: Multimodal continual learning for vision-language model. In The Thirteenth International Conference on Learning Representations, 2025. ^ref-67

[68] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. arXiv preprint arXiv:2001.08361, 2020. ^ref-68

[69] Preetum Nakkiran, Gal Kaplun, Yamini Bansal, Tristan Yang, Boaz Barak, and Ilya Sutskever. Deep double descent: Where bigger models and more data hurt. Journal of Statistical Mechanics: Theory and Experiment, 2021(12):124003, 2021. ^ref-69

[70] Gabriele Prato, Simon Guiroy, Ethan Caballero, Irina Rish, and Sarath Chandar. Scaling laws for the out-of-distribution generalization of image classifiers. ICML 2021 Workshop on Uncertainty and Robustness in Deep Learning., 2021. ^ref-70

[71] Ethan Caballero, Kshitij Gupta, Irina Rish, and David Krueger. Broken neural scaling laws. In The Eleventh International Conference on Learning Representations, 2023. ^ref-71
