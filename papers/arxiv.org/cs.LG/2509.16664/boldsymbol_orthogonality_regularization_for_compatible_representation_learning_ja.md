---
title: "$\boldsymbolλ$-Orthogonality Regularization for Compatible Representation Learning（日本語訳）"
tags: [paper-translation]
---

[[boldsymbol_orthogonality_regularization_for_compatible_representation_learning|← 論文ノート]]

# はじめに 

検索タスクは、顔認識 [[#^ref-1|1]][[#^ref-2|2]][[#^ref-3|3]]、画像位置特定 [[#^ref-4|4]][[#^ref-5|5]][[#^ref-6|6]]、物体同定 [[#^ref-7|7]][[#^ref-8|8]][[#^ref-9|9]] といった実世界の応用において、ますます重要性を増している。画像検索では、ラベル付き画像からなるギャラリーとクエリ画像を照合し、関連する画像、理想的には同一クラスの画像を同定する。高次元画像の代わりに、検索では埋め込みモデルから得られる低次元の特徴ベクトルを用いる。検索性能の向上には、より表現力の高いネットワークアーキテクチャ [[#^ref-12|12]]、新しい学習技術（例えば損失関数）や学習パラダイム [[#^ref-13|13]][[#^ref-14|14]][[#^ref-15|15]] を活用するために、埋め込みモデル [[#^ref-10|10]][[#^ref-11|11]] を更新することがしばしば含まれる。しかし、ニューラルネットワークは、同一データを同一手法および同一アーキテクチャで学習した場合であっても、互換性のある特徴をほとんど生成しない [[#^ref-16|16]]。その結果、新規クエリの特徴と旧ギャラリーの特徴との照合は、非互換性のために検索性能を低下させうる [[#^ref-15|15]]。これに対処するには、旧モデルによって生成されたギャラリー特徴を新モデルによって生成された特徴で置き換える必要があるが、これは backfilling と呼ばれる計算コストの高い処理である。基盤モデルを更新しつつ、その後方互換性を保証し、backfilling を回避するという課題は、広範に研究されてきた [[#^ref-17|17]][[#^ref-15|15]][[#^ref-18|18]][[#^ref-19|19]][[#^ref-20|20]][[#^ref-21|21]]。さらに、gallery 更新の最適戦略――partial backfilling として知られる――も近年注目を集め始めている [[#^ref-22|22]]。

互換性を確保するためのアーキテクチャ変更や追加損失は、更新後モデルの性能を低下させる可能性がある [[#^ref-23|23]][[#^ref-24|24]]。この問題に対処するため、研究はパラメータ効率の高い adapter を用いて、基盤モデルの表現を、別途独立に学習された改良版モデルの表現に整合させることに焦点を当ててきた [[#^ref-22|22]][[#^ref-25|25]]。一方、manifold hypothesis [[#^ref-26|26]][[#^ref-27|27]] は、ニューラルネットワークが通常、同一データ分布の潜在空間表現を生成し、その違いは主として変換によるものであることを示唆する。したがって、関数的に等価なモデルは同一の潜在多様体を近似するため、ある表現を別の表現へ写像するのに必要なパラメータはごく少数である [[#^ref-28|28]][[#^ref-29|29]][[#^ref-27|27]]。ゆえに、新しい表現空間を以前の表現空間に整合させる単純な変換によって、更新後モデルの後方互換性を与えることができる。

![](assets/fig01.png)

検索システム更新時に表現互換性を実現するための提案手法の概要。新たに独立学習されたモデルは、幾何学的構造を保持する直交変換 $B_{\perp}$ を介して旧表現空間に整合される。順方向変換 $F$ は、旧表現を新モデルの後方整合済み空間へ写像する。学習時に最適化されるのは変換パラメータのみであり、モデルパラメータは固定されたままである。

近年の研究では、特定のデータ点を参照として用い、基盤モデルの潜在空間（source space）を他のモデルの潜在空間（target space）へ適応させるために、アフィン写像および直交写像が検討されている [[#^ref-30|30]][[#^ref-28|28]][[#^ref-31|31]]。plasticity-stability paradigm [[#^ref-32|32]] の観点では、アフィン写像は高い適応性（plasticity）を提供する一方で、source space の配置を変えてしまう可能性がある [[#^ref-33|33]][[#^ref-34|34]]。これに対し、直交写像は source space の幾何学的構造（stability）を維持するが、異なる分布への適応性は持たない。source space の幾何学的構造を保持しつつ、特にそれが target space よりも情報量が多い場合 [[#^ref-28|28]][[#^ref-35|35]] に適応性も実現するため、本研究では新たな正則化項を提案する。先行研究 [[#^ref-36|36]] と異なり，本項は、変換が直交条件から所定の近接範囲内に留まるよう制約するものであり、その程度はハイパーパラメータ $\lambda$ により制御される。

本論文では、Fig. [\[fig:compatible_adapters\]](#fig:compatible_adapters) に示すように、独立に学習されたモデル間で表現空間をまたいだ異なる変換を学習することで、互換性を保証する課題に取り組む。本研究の貢献は以下の通りである。

- $\lambda$-Orthogonality regularization を提案する。これは、元の表現空間の大域構造を保持しつつ、下流タスクに対してわずかな局所適応を可能にする、緩和された直交制約である。

- supervised contrastive loss を用いることで表現互換性を高める。これにより、モデルアーキテクチャに依存せず、クラス内クラスタリングとモデル間の特徴整合を促進する。

- 多様なアーキテクチャとデータセットにわたる大規模実験を行い、本手法がモデル間の互換性を保証するだけでなく、基盤モデルの潜在空間の幾何構造の保持も促進し、その結果として下流タスクの精度を向上させることを示す。

- 検索性能を改善しつつ gallery 更新プロセスを最適化する、新しいアーキテクチャ非依存の backfilling 戦略を提案する。

# 関連研究

[[#^ref-16|16]] により示されているように、二つのモデルから得られる特徴表現は――同一データで学習されていたとしても――一般には一致せず、検索システムにおいて高コストな backfilling を生じさせる。これを回避するため、[[#^ref-15|15]] は Backward Compatible Training (BCT) を導入した。これは、旧分類器を基準として固定し、新しい埋め込みが既存のクラスプロトタイプに整合するようにするものである。さらに同研究は、モデル表現間の互換性の形式的定義も与えた。その後の研究はこの基盤を拡張し、追加の正則化技法を組み込んで新しい表現を以前の表現により良く整合させる試み [[#^ref-21|21]][[#^ref-37|37]][[#^ref-20|20]][[#^ref-38|38]][[#^ref-39|39]] や、特定のアーキテクチャ設計の実装 [[#^ref-18|18]][[#^ref-13|13]][[#^ref-40|40]] を行ってきた。しかし、更新後の後方互換モデルの性能は、しばしば独立に学習されたモデルの性能に達しない [[#^ref-23|23]]。これは互換性を実現するために課される正則化の帰結である。これを避けるため、[[#^ref-23|23]] および [[#^ref-24|24]] は、新クラスを含むように表現空間を拡張しつつ、更新時には旧クラスの表現が整合したままであるようにすることを提案した。独立に学習されたモデル間の互換性を保証するため、写像ベースの戦略も開発されている [[#^ref-41|41]][[#^ref-42|42]][[#^ref-43|43]]。[[#^ref-25|25]] が詳述する Forward Compatible Training (FCT) は、追加の補助情報を各データ点に組み込みつつ、旧モデルの埋め込みを新モデルの空間へ整合させる関数を導入する。[[#^ref-25|25]] が指摘するように、これらの変換に伴う計算オーバーヘッドは、画像を埋め込みモデルに通す処理要求と比べて非常に小さい。FastFill [[#^ref-22|22]] は、新モデル分類器を用いることで順方向変換学習を改善し、新モデルを活用して gallery backfilling プロセスを最適化するベイズ戦略を提案する。これに対し，本研究では、モデル更新時に forward 互換性だけでなく backward 互換性も保証する一連の変換関数を提案し、とりわけ backward mapping における直交性に着目する。さらに、クラス内クラスタリングとモダリティ間整合を促進する supervised contrastive loss を提案し、これにより適応を向上させる。最後に、事前抽出された gallery 表現に対して直接動作する距離尺度に基づく新しい gallery backfilling 戦略を提案し、基盤アーキテクチャに依存しないことを実現する。

# 方法 

独立に学習されたモデル間で互換な表現を実現するために、本研究では、複数の変換から成る理論的基盤に裏打ちされたパイプラインを導入する。まず、Sec. 3.1 において [[#^ref-15|15]] により導入された互換性の定義を述べる。Sec. 3.2 および 3.3 では、厳密な直交変換、あるいは下流タスクに適応する場合には提案する $\lambda$-Orthogonality 制約によって正則化された変換のいずれかを用いて、新モデルの表現を前モデルの表現に整合させる新しい backward-compatibility 手法を導入する。次に、Sec. 3.4 では forward trasformation learning を示し、アフィン変換またはより複雑な変換を介して前モデルの表現を新たに適応されたモデルの表現へ整合させ、効率的な gallery set 更新を可能にする。さらに、変換学習の際には supervised contrastive loss（Sec. 3.5）を適用し、モデル表現間の整合を改善するとともに、クラス内クラスタのコンパクトさを高めることで、Def. 1 で定義された互換性基準を満たす。最後に、Sec. 3.6 では、改良された表現を最適化された順序で gallery に backfilling するための新しい順序付け戦略を提案する。本手法全体を通して、すべてのモデルはパラメータを凍結した固定特徴抽出器として機能し、学習されるのは変換層のみである。

![](assets/fig02.png)

![](assets/fig03.png)

![](assets/fig04.png)

異なる $\lambda$ における Eq. [\[eq:orth_smooth\]](#eq:orth_smooth) の値。

## 後方互換表現の定義 

[[#^ref-15|15]] により導入された表現間の Backward-Compatibility の定式化は、異なるモデル間の潜在空間通信の概念と密接に関連している [[#^ref-30|30]]。後方互換表現の形式的定義は次の通りである。

**Definition 1** (***Backward-Compatibility***). ステップ $k$ で学習されたあるモデルの表現は、より後のステップ $t$ で学習された別のモデルの表現と互換である。ここで $k < t$ とする。この互換性は、次の条件が満たされるときに成立する：$$\forall\,i,j:\;\bigl(y_i=y_j\implies d(\mathbf h_i^t,\mathbf h_j^k)\le d(\mathbf h_i^k,\mathbf h_j^k)\bigr)\;\wedge\;\bigl(y_i\neq y_j\implies d(\mathbf h_i^t,\mathbf h_j^k)\ge d(\mathbf h_i^k,\mathbf h_j^k)\bigr)$$ ここで $d(\cdot, \cdot)$ は距離関数であり、$y_i$ および $y_j$ は、それぞれ抽出された表現ベクトル $\mathbf{h}_{i}$ および $\mathbf{h}_{j}$ に対応するクラスラベルである。Def. 1 における不等式は、新しいモデルの表現が古い表現と比較されたとき、同一クラスの画像をクラスタリングし、異なるクラスの画像から分離するという点で、少なくとも旧モデルと同等以上に機能すべきことを示している。

## 後方変換 

relative encoding [[#^ref-30|30]] の貢献の一つは、実際には、表現空間は同一あるいは類似のデータ意味論を共有する場合、しばしば角度保存変換によってのみ異なるという観察である。さらに [[#^ref-28|28]] は、学習された意味論に差異がある場合、Procrustes analysis [[#^ref-44|44]] により学習された、角度と距離の双方を保存する変換が、角度保存写像のみよりも cross-architecture および cross-modality の分類タスクにおいて優れた性能を示すことを明らかにしている。変換 $T$ は、空間内の任意の二点 $a$ と $b$ の間の角度と距離を保存するならば isometry であると定義される。形式的には、写像 $T: \mathbb{R}^n \to \mathbb{R}^n$ が isometry であるとは、次の条件が成り立つことである：$\| T(a) - T(b) \|_2 = \| a - b \|_2, \quad \forall a, b \in \mathbb{R}^n$。ここで $\| \cdot \|_2$ はユークリッドノルムを表し、他の空間では同値に一般の距離尺度を意味する。本研究ではこの性質を利用して、直交変換を用いることで更新後モデルの空間を基盤モデルの空間に整合させ、後方互換表現を実現する。これにより、変換の等長性に由来して幾何学的性質と更新後モデルの性能を維持しつつ、更新を通じて統一された表現空間を保つことができる。

基底モデル $\phi^k$ とその更新版 $\phi^t$ があり、$k < t$ であるとする。これらに対応する表現ベクトル $\mathbf{h}^k \in \mathbb{R}^d$ および $\mathbf{h}^t \in \mathbb{R}^n$ に対して、更新モデルの埋め込み空間を基底モデルの空間へ写像する直交変換 $B_{\perp}: \mathbb{R}^n \rightarrow \mathbb{R}^n$ を学習する。厳密な直交性を課すために、一般の変換 $B$ は反対称行列 $P$ の行列指数としてパラメータ化され、$B = e^P$ とする。このとき、$P$ の上三角成分が学習可能パラメータである [[#^ref-45|45]]。更新表現空間と基底表現空間の整合を強制するため、変換後の $\mathbf{h}^t$ と $\mathbf{h}^k$ の間の平均二乗誤差損失を最小化することで変換 $B_{\perp}$ を最適化する: $$\mathcal{L}_{B} = ||B_{\perp}(\mathbf{h}^t) - \mathbf{h}^k||_2^2$$ 変換 $B_{\perp}$ は正方行列であるため、二つの表現空間の次元数が異なる場合には、高次元側の特徴ベクトルを切り詰めて低次元側の表現に合わせる。

## $\boldsymbol{\lambda}$-Orthogonality Regularization 

変換 $B$ に対して厳密な直交制約（高い安定性）を課すことは、モデル分布がアダプタの学習対象から逸脱する場合には必ずしも望ましくない。たとえば、抽出済み埋め込みのみをユーザに提供するプライベートモデルがこれに該当する。このような制約を課すと、下流タスクに必要な新規かつ関連性の高い情報の統合が制限されうる。逆に、幾何学的正則化を伴わないアフィン変換（高い可塑性）は、更新モデルの表現を破壊しうる [[#^ref-46|46]][[#^ref-47|47]]。[[#^ref-36|36]] で述べられているように、重み行列 $W \in \mathbb{R}^{n \times n}$ とバイアス項 $b \in  \mathbb{R}^n$ から成る変換 $B: \mathbb{R}^n \rightarrow \mathbb{R}^n$ に対して、ソフトな直交制約を適用できる。先行研究 [[#^ref-48|48]][[#^ref-49|49]][[#^ref-50|50]] では、重み行列の Gram 行列を恒等行列に近づけるよう制約するため、次の損失関数を最小化することが提案されている: $$\mathcal{L}_{orth} = ||W^T W - I||_F$$ ここで $||\cdot||_F$ は Frobenius ノルムを表し、$W$ は変換 $B$ の重みである。これは、パラメータ集合を Stiefel manifold [[#^ref-50|50]] に近接するよう制限する weight decay 項として解釈できる。しかし、この方法では、変換にどの程度の直交性を課すかという具体的な制御は与えられない。

そこで我々は、重み行列の Gram 行列が恒等行列にどれだけ近いべきかを規定する閾値 $\lambda$ を導入する。素朴な解としては、損失が Gram 行列に直接影響することから、重み行列の Gram 行列が閾値 $\lambda$ に達した時点で $\mathcal{L}_{orth}$ の最適化を停止する方法が考えられる: $$\min_{W} \; ||W^T W - I||_F \quad \text{s.t.} \quad ||W^T W - I||_F \geq \lambda$$ この目的は、$\lambda$ パラメータで平行移動された Heaviside step function [[#^ref-51|51]][[#^ref-52|52]] を用いて直接達成できる: $H(x-\lambda)=\mathbf{1}_{\{x\ge\lambda\}}$ この関数 $H$ は、最小化過程における直交性の度合いを制御する効率的な機構を提供し、Frobenius ノルムが閾値 $\lambda$ を超えたときに、式 [\[eq:ortho\]](#eq:ortho) の正則化項を事実上無効化する: $$\mathcal{L}_{\lambda} = H ( \| WW^T - I \|_F - \lambda) \cdot \| WW^T - I \|_F.$$ しかし、この手法は [[#^ref-53|53]] が指摘するように、損失関数に不連続性を導入する。とりわけ彼らの研究は、これらの sigmoid 関数が Heaviside step function にどれだけ近いかを評価することに焦点を当て、Hausdorff 距離に対する厳密な上界および下界を与えている。こうした理論的・実証的分析を踏まえ、我々は、閾値 $\lambda$ からの距離に応じてペナルティの重要度が増減し、制約の効果が徐々に調整されるような滑らかな調整関数を提案する。具体的には、次式で定義される損失関数を最適化することで、新たな $\lambda$-Orthogonality Regularization 項を定式化する: $$\mathcal{L}_{\lambda} = \sigma \left( \alpha \left( \| WW^T - I \|_F - \lambda \right) \right) \cdot \| WW^T - I \|_F$$ ここで $\sigma(\cdot)$ は sigmoid 関数、$\alpha$ はスケーリング係数である。

![](assets/fig05.png)

![](assets/fig06.png)

![](assets/fig07.png)

![](assets/fig08.png)

![](assets/fig09.png)

Source space

sigmoid 関数は連続的なスイッチとして機能し、Fig. [\[fig:lambda\]](#fig:lambda) に示すように、$\lambda$ の値の近傍で正則化項を徐々に有効・無効化する。一方、スケーリング係数 $\alpha$ は sigmoid 関数の傾きを制御し、これにより $\| WW^T - I \|_F$ の値が閾値 $\lambda$ に近づく際に、正則化がどれほど急峻に有効化または無効化されるかが決まる。Fig. [\[fig:alpha\]](#fig:alpha) では、正則化損失に適用される異なる傾きの水準を示している。$\alpha$ が増加するにつれて、その挙動は Heaviside step function により近く収束する。

$\lambda$-orthogonality regularization の挙動をさらに分析するため、ランダム初期化された重み行列 $W$ をもつ変換 $B$ に対して式 [\[eq:orth_smooth\]](#eq:orth_smooth) を最適化する。Fig. [\[fig:angle\]](#fig:angle) に示すように、これらの角度の kernel density estimation (KDE) は、正則化に用いる $\lambda$ の値に応じて変化する。$\lambda$ の値が小さいほど、列ベクトルはより直交的になり、特に $\lambda=0$ のとき、我々の正則化は式 [\[eq:ortho\]](#eq:ortho) に等しい。Fig. [\[fig:mnist\]](#fig:mnist) は、MNIST データセット全体で学習した source representation space（Fig. [\[fig:source\]](#fig:source)）と、MNIST の最初の 5 クラスで学習した target representation space（Fig. [\[fig:target\]](#fig:target)）を整合させるために学習した、アフィン変換（Fig. [\[fig:affine\]](#fig:affine)）、厳密直交変換（Fig. [\[fig:sorth\]](#fig:sorth)）、および $\lambda$-orthogonality regularized 変換（Fig. [\[fig:near_orth_mnist\]](#fig:near_orth_mnist)）の効果を示している。この玩具実験は、$\lambda$-orthogonal 制約が、厳密な直交性を緩和しつつ source feature space の構造の保存を促進することで、制約なし変換に比べて整合を改善することを示している。

## Forward Transformation 

新しいモデルの表現を前のモデルの表現へ写像する backward transformation に加えて、forward transformation $F: \mathbb{R}^d \rightarrow \mathbb{R}^n$ を定式化することも可能である。この変換は、前のモデルの表現ベクトル $\mathbf{h}^k \in \mathbb{R}^d$ を新しいモデルの表現 $\mathbf{h}^t \in \mathbb{R}^n$ に写像する。新しいモデルの表現は前のモデルの表現よりも優れているため、変換 $F$ は、改善された表現によりよく適応できるよう、アフィン変換（高い可塑性）または複数の投影層であるべきである。変換 $F$ は、[[#^ref-25|25]] で述べられたアプローチに従い、二つの表現間の平均二乗誤差 $|| F(\mathbf{h}^k) - \mathbf{h}^t ||_2^2$ を最小化することで学習される。この概念は latent space communication [[#^ref-30|30]][[#^ref-31|31]] と密接に関連しており、そこでは $\mathcal{T}$ を一般的な変換として $d \big(\mathbf{h}^k_{i}, \mathbf{h}^k_{j} \big) = d \big(\mathcal{T}\ \mathbf{h}^t_{i}, \mathcal{T}\ \mathbf{h}^t_{j} \big)$ が成り立つ。先行手法 [[#^ref-25|25]][[#^ref-22|22]] では、古い表現 $\mathbf{h}^k$ を変換 $F$ を通じて新しい $\mathbf{h}^t$ に直接整合させるが、その結果 $\mathbf{h}^k$ と $F(\mathbf{h}^k)$ の間に非互換性が生じる。Sec. 3.2 で述べたように、backward orthogonal transformation $B_{\perp}$ は新しい表現を古い表現へ再整合させる。古い特徴を新しい表現 $\mathbf{h}^t$ に直接適応させる代わりに、我々はそれらを $B_{\perp}(\mathbf{h}^t)$ に適応させ、モデル更新を通じて統一的な整合を保証する。さらに、変換 $F$ と $B_{\perp}$ は同一の学習データを用いるため、共同で学習可能である。したがって、我々の手法における forward alignment loss は次式で定義される:

$$\mathcal{L}_F = || F(\mathbf{h}^k) - B_{\perp}(\mathbf{h}^t) ||_2^2$$

抽出された表現が、Sec. 3.3 で議論したように、二つのモデルの訓練集合とは異なるデータセットに由来する場合には、厳密直交な $B_{\perp}$ の代わりに、$\lambda$-orthogonal regularized transformation $B_{\lambda}$ を用いることができる。

## Intra-class Clustering and Inter-Model Alignment 

Sec. 3.1 で議論したように、Def. 1 で定義された互換性不等式は、整合だけでなく、互換性を達成するためのより高いクラスタ集中度も要求する。この目的のために、[[#^ref-22|22]] は追加の訓練損失 $\mathcal{L}_{disc}$ を導入している。これは、[[#^ref-15|15]] の influence loss とは異なり、旧モデルではなく新モデルの分類器に直接依拠する。しかし、$\mathcal{L}_{disc}$ は新モデルの分類器および訓練損失へのアクセスを必要とするため、特に新モデルのアーキテクチャが未知である場合（たとえば、private model や online model から得られる埋め込みベクトル）には適用性が制限される。これを克服するため、我々は表現ベクトルに直接適用する supervised contrastive loss の利用を提案する。この損失は、整合とクラスタリングのために表現ベクトルを直接活用するため、分類器やアーキテクチャに関する知識を一切必要としない。supervised contrastive loss [[#^ref-54|54]] は、$\mathbf{q}_i$ と $\mathbf{p}_i$ の間の cross-entropy loss を最小化する: $$\mathcal{L_{\text{contr}}} = -\sum_{i=1}^K \mathbf{p}_i \log \mathbf{q}_i$$ ここで $\mathbf{q}_i$ は、L2 正規化された特徴 $\mathbf{h}$ と各候補との dot-product similarities に対して temperature-scaled softmax を適用することで、サンプル $i$ に割り当てられる確率を表し、$\mathbf{p}_i$ は、意味的に一致する（同一クラスの）候補すべてに等しい質量を与え、それ以外を 0 とする正規化された ground-truth indicator distribution である。具体的には、この損失関数の組合せを利用し、目的関数 $\mathcal{L}_{\text{C}}$ を次のように定義する: $$\begin{aligned}
\mathcal{L}_{\text{C}} = \mathcal{L}_{\text{contr}}(F(\mathbf{h}^k), B_{\perp}(\mathbf{h}^t))\ + \mathcal{L}_{\text{contr}}(F(\mathbf{h}^k),\mathbf{h}^k)
\end{aligned}$$ この損失は、適応後の表現間でのクラスタリングを促進すると同時に、それらを前のモデルの表現とも整合させることで、特徴表現の intra-class clustering および inter-model alignment を促進する。

我々の枠組みにおける全体損失関数は、四つの構成要素、すなわち forward alignment loss $\mathcal{L}_F$、backward alignment loss $\mathcal{L}_{B}$、contrastive loss $\mathcal{L}_{\text{C}}$、および $\lambda$-Orthogonality regularization 項 $\mathcal{L}_{\lambda}$ の加重和として定義される。形式的には、総損失は次式で表される: $$\mathcal{L} = w_1 \cdot \mathcal{L}_F + w_2 \cdot \mathcal{L}_{B} + w_3 \cdot \mathcal{L}_C + \mathcal{L}_{\lambda}$$[] ここで $w_1$, $w_2$, および $w_3$ は、各項の寄与をバランスさせるためのスカラー重みを表す。

## Partial Backfilling Strategy

forward-adapted gallery set におけるサンプルの backfilling の有効な順序を決定することは、旧モデルの $F(\mathbf{h}^k)$ を $B_{\perp}(\mathbf{h}^t)$ に置き換える操作を通じて、新たに独立に学習されたモデルの性能に可能な限り効率よく到達するうえで極めて重要である。しかし、backfilling の最適順序の同定は、計算的に困難な組合せ最適化問題である [[#^ref-22|22]]。この課題に対処するため、FastFill [[#^ref-22|22]] は Bayesian Deep Learning に着想を得た順序付けを導入している。この手法は、alignment error を多変量ガウス分布としてモデル化し、mapping function $F$ の学習中にこの分布の負の対数尤度を最小化する。しかし、retrieval の観点からは、最も代表的なインスタンス、すなわち異なるクラス間の分離を大きく高めるインスタンスは、それぞれのクラス平均に最も近い embedding として同定される [[#^ref-55|55]][[#^ref-56|56]]。したがって、情報量の少ない embedding を優先的に backfilling することで、クラス間の差異を強化し、システム性能を向上させることができる。この目的のために、我々は既に抽出された representation vector $F(\mathbf{h}^k)$ に直接基づいて backfill 順序を推定する新たな手法を提案する。まず、forward-adapted gallery set における各クラス $c$ の平均 representation vector $\boldsymbol{\mu}_c$ を計算する。次に、各 embedding vector $F(\mathbf{h}^k)$ と対応するクラス平均 $\boldsymbol{\mu}_c$ との距離指標 $d$ を算出する。例えば、$d$ には Mean Squared Error を用いることができ、$d = \| F(\mathbf{h}^k) - \boldsymbol{\mu}_c \|_2$ と表される。$\boldsymbol{\mu}$ からの距離 $d$ が最大となる gallery embedding を backfilling の優先対象とすることで、新たに backward-adapted された独立学習モデル $B_{\perp}(\mathbf{h}^t)$ により生成された query とのマッチングが容易になる。

# Experiments 

0.48

0.48

## Image Retrieval Compatibility

Backward compatibility は、gallery set $\mathcal{G} = \{(\mathbf{x}_i, y_i)\}_{i=1}^{N_g}$ と query set $\mathcal{Q}=\{(\mathbf{x}_i, y_i)\}_{i=1}^{N_q}$ を含む retrieval タスクにおいて重要であり、それぞれ $N_g$ および $N_q$ 枚の画像と、それに対応するクラスラベルを有する。base model は画像から特徴ベクトルを抽出して gallery を index 化し、retrieval タスクにおいて query set のベクトルとの照合に用いる。Def. 1 で提示された compatibility の定義では、データセット内の全データ点間の pairwise distance を計算する。この処理は、データセット規模が大きくなるにつれて計算負荷が著しく増大する。つぎに、ステップ $t$ で更新されたモデルが、ステップ $k$ で学習された base model と backward-compatible であるとは、Empirical Compatibility Criterion [[#^ref-15|15]] が満たされる場合を指す: $$M \big( \Phi_t^\mathcal{Q}, \Phi_k^\mathcal{G} \big) > 
M \big( \Phi_k^\mathcal{Q}, \Phi_k^\mathcal{G} \big), \quad \text{with } k < t$$ ここで $M$ は性能指標を表し、$\Phi^\mathcal{G}$ と $\Phi^\mathcal{Q}$ はそれぞれ抽出された gallery set と query set を表す。具体的には、$M \big( \Phi_t^\mathcal{Q}, \Phi_k^\mathcal{G} \big)$ は、ステップ $t$ の更新モデルの gallery 特徴とステップ $k$ の query 特徴を用いた cross-model retrieval を評価する。対照的に、$M \big( \Phi_k^\mathcal{Q}, \Phi_k^\mathcal{G} \big)$ は same-model retrieval を意味し、gallery と query の両特徴がともにステップ $k$ の同一モデルに由来する。

#### Partial Backfilling.

gallery set $\Phi^\mathcal{G}$ の画像の順序 $\pi$、すなわち $\mathbf{x}_{\pi_1}, \mathbf{x}_{\pi_2}, \dots, \mathbf{x}_{\pi_n}$ と backfilling fraction $\beta \in [0,1]$ が与えられたとき、部分的に backfill された gallery set $\Phi^\mathcal{G}_{\pi, \beta}$ を以下のように定義する。順序の先頭から $N_{g,\beta} = \lfloor \beta N_g \rfloor$ 枚の画像は更新モデルで処理し、残りの画像は旧モデルで処理する。ここで $N_g$ は gallery の総画像数を表す。異なる backfilling 戦略を評価するために、[[#^ref-22|22]] で導入された backfilling metric $\widetilde{M}$ を用いる。これは次式で定義される: $\widetilde{M}(\Phi^\mathcal{G},\Phi^\mathcal{Q}, \pi) = \mathbb{E}_{\beta \sim [0,1]} M(\Phi^\mathcal{G}_{\pi, \beta},\Phi^\mathcal{Q}).$ この指標は、$M$ を用いて性能を評価したときの backfilling curve の下の面積に相当する。

## Evaluation Metrics and Datasets 

先行研究の model compatibility [[#^ref-15|15]][[#^ref-25|25]] に従い、我々は2つの指標を用いて性能を評価する。Cumulative Matching Characteristics (CMC) は、query 特徴と gallery 特徴の距離を計算することで top-$k$ retrieval accuracy を測定し、$k$ 個の最近傍 gallery 画像の少なくとも1枚が query のラベルと一致すれば retrieval 成功と見なす。mean Average Precision (mAP) は、全 recall 範囲 $[0,1]$ にわたる precision-recall curve の下の面積を測定する。

我々の手法を検証するために、以下のデータセットを用いる: ImageNet1K [[#^ref-57|57]]、CIFAR100 [[#^ref-58|58]]、および CUB200 [[#^ref-59|59]]。各データセットの validation/test set を query と gallery の両方として使用し、探索における自明な一致を避けるため、各 query 画像は gallery から除外する。表中の 'Query/Gallery' という表記は、それぞれ embedding 抽出に用いたモデルを示す。CUB200 と CIFAR100 は downstream task として用いる。

## Extending Classes Setting

この設定では、クラス数を拡張することで base model を更新する。ImageNet1K の最初の500クラスで $\phi_{\text{old}}$ を、全1000クラスで $\phi_{\text{new}}$ を、それぞれ ResNet-34 アーキテクチャと embedding 次元128を用いて、PyTorch の標準学習レシピ[^2]に従って独立に学習する。2つのモデルを独立に学習した後、モデル層を凍結したまま、adapter を Adam と学習率 $0.001$ で最適化する。我々の手法を、互換表現を実現するための mapping method である FCT [[#^ref-25|25]] および FastFill [[#^ref-22|22]] と比較する。Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) では、Sec. 4.2 の指標に従って各手法の性能を要約している。結果は、新しいモデル $\phi_{\text{new}}$ が古いモデル $\phi_{\text{old}}$ と直接には互換でないことを示している。さらに、2つの mapping method である FCT と FastFill は、gallery と query set の適応済み representation に対して両指標で性能を向上させる。しかし、これらの手法が達成するのは新たに学習されたモデルとの backward compatibility であり、元のモデルとの互換性ではない。これに対して、我々の手法は orthogonal transformation $B_{\perp}$ を通じて新モデルを旧モデルに整合させる。これにより、新旧の representation 間の互換性が確保されると同時に、forward adapter $F$ が提供する性能も向上する。Appendix 6 では、Places365 [[#^ref-60|60]] データセットに関する追加結果を示す。

## Independently Pretrained Models adapted on Downstream Task 

訓練コストの増大に伴い、特に局所データセットを用いた downstream task への適応において、pretrained model の利用が増加している。この文脈で、我々は PyTorch hub で利用可能な、ImageNet1K データセットで事前学習された2つのモデルを用いる。すなわち、embedding サイズ512の ResNet-18 と、embedding サイズ1024のより高度な Vision Transformer (ViT-L-16) [[#^ref-61|61]] である。ViT モデルは、その強化されたアーキテクチャのため、ResNet-18 に対する更新版と見なされる。Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) は、2つの pretrained model と同じデータセットを用いた adapter 学習結果を示しており、Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) と同様の傾向を示すとともに、我々の手法が他の baseline と同等の性能を示しつつ、更新モデルと旧モデルの互換性を実現することを示している。FastFill とは異なり、我々の手法は新モデルの classifier を必要とせず、抽出された embedding vector に直接依拠する。Appendix 7 では、我々の手法をさらに検証するため、pretrained model として用いられる異なるアーキテクチャに対して本手法を適用する。さらに Appendix 8 では、CLIP-like [[#^ref-62|62]] モデルや DINOv2 [[#^ref-63|63]] のような self-supervised architecture を用いて、distribution shift または objective shift を伴う更新シナリオを検討する。

downstream task における互換性の結果は Tab. [\[table:cub\]](#table:cub) に報告する。そこでは、ローカルデータセット（CUB200 または CIFAR100）の表現に対して、学習データセットとは異なるデータ上で adapter を学習している。$\lambda$-Orthogonality regularization を伴う transformation $B_{\lambda}$ を用いることで、我々の手法は local task 性能と model compatibility を向上させ、baseline を上回る。追加の downstream データセット（Flower102 [[#^ref-64|64]] および Places365）の結果は Appendix 9 に示す。Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) および Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) から、厳密な orthogonal transformation である $B_{\perp}$ は、独立に学習されたモデル $\phi_{\text{new}}$ に対して性能向上をもたらさないことが分かる。これに対し、$B_{\perp}$ よりも高い plasticity を与える $B_{\lambda}$ は、新モデルが downstream task において性能を向上させることを可能にする。

ハイパーパラメータ $\lambda$ に関する ablation study を Appendix 10 に示し、Eq. [\[eq:total_loss\]](#eq:total_loss) における損失項の構成要素ごとの ablation を Appendix 11 に詳述する。

<figure>
<p>![](assets/fig10.png)</p>
</figure>

<figure>
<p>![](assets/fig11.png)</p>
</figure>

[]

+---------------------------------+-----------------------+
| Method                          | $\widetilde{M}$       |
+:================================+:=========:+:=========:+
| 2-3                             | CMC-Top1  | mAP       |
+---------------------------------+-----------+-----------+
| FCT [[#^ref-25|25]]     | 58.72     | 33.57     |
+---------------------------------+-----------+-----------+
| FastFill [[#^ref-22|22]] | 60.49     | 35.59     |
+---------------------------------+-----------+-----------+
| Ours                            | **61.20** | **36.46** |
+---------------------------------+-----------+-----------+

<figure>
<p>![](assets/fig12.png)</p>
</figure>

<figure>
<p>![](assets/fig13.png)</p>
</figure>

[]

+---------------------------------+-----------------------+
| Method                          | $\widetilde{M}$       |
+:================================+:=========:+:=========:+
| 2-3                             | CMC-Top1  | mAP       |
+---------------------------------+-----------+-----------+
| FCT [[#^ref-25|25]]     | 73.86     | 52.02     |
+---------------------------------+-----------+-----------+
| FastFill [[#^ref-22|22]] | 75.06     | 55.34     |
+---------------------------------+-----------+-----------+
| Ours                            | **76.59** | **57.72** |
+---------------------------------+-----------+-----------+

[]

## Backfilling Results

本節では、Sec. 3.6 で議論した新規の backfill 戦略を評価する。ここでは、Tab. [\[table:imagenet_ext\]](#table:imagenet_ext) および Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) に詳述した実験設定を考慮する。FCT には特定の backfilling 戦略が存在しないため、[[#^ref-22|22]] と同様にランダム順序を用いる。Fig. [\[fig:backfill\]](#fig:backfill)、Tab. [\[tab:b_ext\]](#tab:b_ext)、および Tab. [\[tab:b_arch\]](#tab:b_arch) に示す結果は、我々の backfilling 戦略が他の baseline を一定の差で上回ることを示している。特に、Fig. [\[fig:backfill\]](#fig:backfill) は、gallery の50%未満を backfill した段階で、新たに独立に学習されたモデルと同等の性能を達成できることを示している。Appendix 12 では、主実験で用いた Mean Squared Error とは異なる距離指標を用いた ablation study を提示する。

# Conclusion

モデル互換性は、多くの大規模検索システムにおける重要な課題であり、これが達成されない場合にはシステム更新を妨げうる。本論文では、独立に学習された表現を統一空間に整列させる写像変換を導入し、さらに教師ありコントラスト損失によってより良い特徴クラスタリングを実現する。また、新たに学習された独立モデルの完全性を損なうことなく、下流タスクへの適応を支援するために、直交制約の緩和も提案する。加えて、ギャラリー集合の効率的な部分バックフィルを可能にする新規のバックフィル順序戦略を提案し、ギャラリーの半分未満をバックフィルするだけで、新たに独立学習したモデルと同等の性能を達成する。本手法は、モデルが学習された同一分布および異なる分布の双方において、既存手法を上回る優れた性能を示す。これらの結果を文脈づけるため、手法の限界については Appendix 14 で詳細に検討する。さらに、その実用的有用性を評価するため、方法論的複雑性とより広範な適用可能性を Appendix 13 で分析する。

# 謝辞

本論文は、プロジェクト \"Collaborative Explainable neuro-symbolic AI for Decision Support Assistant\"、CAI4DSA、CUP B13C23005640006 により一部助成を受けた。

# Places365 におけるクラス拡張設定

本手法をさらに検証するため、ImageNet1K とは異なるデータセットで学習されたモデルを用いて評価を行う。具体的には、Places205 で事前学習された ResNet-50（[ViSSL](https://github.com/facebookresearch/vissl/blob/main/MODEL_ZOO.md#supervised)）を旧モデルとし、Places365 で事前学習された ResNet-50（[CSAILVision](https://github.com/CSAILVision/places365#pre-trained-cnn-models-on-places365-standard)）を新モデルとする。Tab. [\[tab:app_places\]](#tab:app_places) は、Sec.4.2 で定義した評価指標を用いた各手法の性能を要約している。結果は、新モデル $\phi_{\text{new}}$ が旧モデル $\phi_{\text{old}}$ と本質的に互換ではないことを示している。さらに、FCT により提供される適応 $F(\phi_{\text{old}})$ は、新モデル単独と比較しても性能が劣る。これに対し、FastFill や本提案手法のように、より良いクラスタリングを促進する手法は、単独の新モデルを上回る性能を達成する。この改善は、旧モデルと新モデルの双方からの情報を活用し、順方向アダプタの学習中に知識蒸留の一形態を効果的に実装することに起因する。ベースラインとは異なり、本手法は適応後のすべての表現を統一された表現空間に整列させ、それにより旧モデルとの互換性を一貫して維持する。

# 独立事前学習モデル設定における追加アーキテクチャ

旧モデル $\phi_{\text{old}}$ として DenseNet-121 を、新モデル $\phi_{\text{new}}$ として EfficientNet-B3 を用いた追加実験を行う。いずれも ImageNet1K で事前学習されており、PyTorch Hub から取得したものである。これらの ImageNet1K データセット上での実験結果を Tab. [\[tab:abl_arch\]](#tab:abl_arch) に示す。本手法はすべての指標において最良の性能を達成し、クロスモデル検索および同一モデル検索の双方においてベースラインを上回る。

# DINOv2 と CLIP を独立事前学習モデルとして用いた追加実験

データ分布または目的のシフトを伴う更新シナリオを調査するため、旧モデルとして ImageNet1K で事前学習された ResNet-18 を用い、新モデルとしては CC12M [[#^ref-65|65]] データセットで事前学習された CLIP  [[#^ref-62|62]] と DINOv2  [[#^ref-63|63]] ($vit\_small\_patch14\_dinov2$) の双方を用いて追加実験を行う。順方向変換と逆方向変換の両方を学習するために、ImageNet1K データセットと Tab. [\[table:imagenet_arch\]](#table:imagenet_arch) と同一のハイパーパラメータを用いる。この設定は、新モデルに対してデータ分布とモデル目的の両面で大きな変化を表している。特筆すべき点として、CLIP と DINOv2 のいずれも分類器を持たないため、この文脈では FastFill を適用できない。Tab. [\[table:dino\]](#table:dino) では、新たに独立学習されたモデルとして DINOv2 を用いた結果を報告する。本手法は FCT より良い結果を達成し、実世界の問題への実用的適用可能性をさらに裏づける。

一方、Tab. [\[table:clip\]](#table:clip) では、CC12M で事前学習された CLIP を新たに独立学習されたモデルとして用いた結果を報告する。このシナリオでは、事前学習済み CLIP モデルは ImageNet1K 上で ResNet-18 と比べて低い検索性能を示す。これはマルチモーダル学習におけるよく知られた制約であり、モダリティ内の不整合が単一モダリティ表現の品質に悪影響を及ぼしうる [[#^ref-66|66]]。具体的には、CLIP モデルは単一モダリティ検索タスクではなく、クロスモーダル検索に最適化されているのに対し、DINOv2 や ResNet-18 は単一モダリティのみに基づいて学習されている。このように新モデルの性能が旧モデルを下回ると、FCT は旧モデルの高品質な表現を新モデルの低性能な表現へ変換しようとするため、互換性を達成できず、システム全体の検索能力を低下させる。これに対し、本手法は追加損失を導入し、特定の学習データセット上でクラス内クラスタリングとモデル間整列の双方を促進する。その結果、より高い柔軟性を持つ順方向変換は、旧モデルの表現性能を改善する。この困難なシナリオにおいても、本手法は FCT を上回り、手法の頑健性をさらに検証する。

0.48

0.48

# 下流タスク設定に適応した独立事前学習モデルのための追加データセット

我々は、さらに二つの追加データセット、すなわちより大規模な Places365 と、きめ細かな Flowers102 を加えることで、Independently Pretrained Models Adapted on Downstream Task 設定に関する分析を拡張する。これにより、より困難なシナリオにおける本手法の有効性を評価できる。結果は Tab. [\[table:places-flowers\]](#table:places-flowers) に報告する。これらの実験では、旧モデルは ResNet-18、新モデルは ViT-L-16 であり、いずれも ImageNet-1K で事前学習されている。$\lambda = 12$ のアフィンアダプタを用いる。追加の両データセットにおいて、本手法は一貫してベースライン手法を上回る。提案する $\lambda$-Orthogonality 正則化は、下流タスクにおける検索性能を改善するだけでなく、適応後の新モデル表現 $B_{\lambda}(\phi_{\text{new}})$ が元の形を維持するよう促進する。その結果、ImageNet1K 上での検索性能が保持される。

# ハイパーパラメータ $\boldsymbol{\lambda}$ に関するアブレーション

r0.5

![](assets/fig14.png)

本実験では、下流タスクへの適応性を最大化しつつ、事前学習済みモデルの元の学習データセットである ImageNet1K 上での性能を保持するように $\lambda$ を選択する。提案手法の影響を示すため、Tab. [\[table:lambda_ablation\]](#table:lambda_ablation) では、新しい事前学習済みモデルに対して提案する $\lambda$-orthogonal regularizer を適用した際の CMC-Top1 スコアを報告する。Fig. [\[fig:lambda ablation\]](#fig:lambda ablation) にも示されるように、$\lambda$ を増加させると、下流タスクにおける新モデル表現の性能が向上する。

しかし、この改善は元のデータセット上での性能低下を伴い、特に正則化がない場合（$\lambda = \infty$）にはゼロショット（ZS）スコアの低下として顕著に現れる。経験的には、$\lambda = 12$ が全指標にわたって最良のトレードオフを与えることが分かる。[[#^ref-36|36]] はソフト直交制約を最適化しており、これは $\lambda = 0$ の場合に相当する。しかし、この定式化では性能向上は得られず、厳密な直交変換を用いた場合に劣る。Sec. 3.3 で議論したように、厳密な直交性の課すことは、モデルがタスク固有情報を取り込む能力を妨げうる。これに対し、本手法は、Gram 行列の単位行列からの逸脱を制御する調整可能なハイパーパラメータ $\lambda$ を導入することでこの制約を緩和し、表現の一貫性を保ちながらより高い柔軟性を可能にする。

本手法をさらに検証するため、$\lambda$-orthogonal regularization の損失寄与に対するスカラー重み $w$ の効果を、二つの異なる直交正則化、すなわち Soft Orthogonality (SO)[[#^ref-36|36]]――本手法における $\lambda =0$ の特別場合に対応する――および Spectral Restricted Isometry Property (SRIP)[[#^ref-36|36]] と比較して調べる。正則化項のスカラー重みとして、$w = 1$, $w = 10^{-1}$, $w = 10^{-2}$, $w = 10^{-3}$ を試す。さらに、厳密直交性からの逸脱を示すため、学習終了時点で逆方向変換 $B_{\lambda}$ が到達した $\lVert W^{\top} W-I \rVert_F$ の厳密な値を報告する列も設ける。

Tab. [\[table:method_comparison\]](#table:method_comparison) に示すように、SRIP と SO の双方において、$\lVert W^{\top}W - I \rVert_F$ の最終値は最適化過程と選択したスカラー重み $w$ に支配される。本手法の $\lambda$-orthogonal regularization とは異なり、これらの手法は $\lVert W^{\top}W - I \rVert_F$ を直接制御できない。総損失に対する正則化項の寄与が小さいほど、逆方向変換 $B_{\lambda}$ に対する正則化効果は弱まる。正則化項のスカラー重み $w$ を減少させると、特に MSE やコントラスト損失 $L_C$ のような競合する損失成分が非直交変換を支持しうるため、最適化過程は正則化項を十分に最小化できなくなる。例えば、$w = 10^{-3}$ および $w = 10^{-2}$ の場合、SO、SRIP、および本手法の $\lambda$-orthogonal regularization による結果は、直交性制約が完全に無視される $\lambda = \infty$ の場合（Tab. [\[table:lambda_ablation\]](#table:lambda_ablation) を参照）と同程度である。これは、そのように小さい $w$ では、最適化中に正則化項の寄与が無視できるほど小さくなるためである。この問題を避けるため、本手法では $\lambda$-orthogonal regularization に対して $w = 1$ を設定し、逆方向変換の学習中に正則化項が最適化過程に効果的に組み込まれるようにしている。これにより、正則化項は目標閾値 $\lambda$ に到達し、逆方向変換における安定性--可塑性トレードオフを精密に制御できるようになり、下流タスクにおける表現互換性が向上する。Tab. [\[table:method_comparison\]](#table:method_comparison) の太字エントリが示すように、本手法は $w = 1$ および $w = 10^{-1}$ において、SO や SRIP とは対照的に安定した結果を生成する（わずかな変動は確率的最適化に起因する）。逆に、$w$ が非常に低い場合（$10^{-2}$ または $10^{-3}$）、正則化項は十分に最適化されず、本手法は SO 正則化と同様に振る舞う。これは、本手法で導入した制約（$\lVert W^{\top}W - I \rVert_F\geq\lambda$）が目的関数の最小値に影響を与えるが、実際にはその最小値に到達しないためである。対照的に、その近似的定式化と SO に比べてより高い複雑性のため、SRIP は $w$ が低いときにさらに弱い正則化効果しか示さない。

# 損失項寄与の詳細分析

本節では、学習時に最適化される最終損失（Eq. [\[eq:total_loss\]](#eq:total_loss)）に対して、各項の寄与を解析する。Tab. [\[tab:loss_combo_cmc_tick\]](#tab:loss_combo_cmc_tick) は、特徴が抽出されたモデルの学習に用いたデータセット、すなわち ImageNet1K と適応データセットが一致する場合の結果を示している。このシナリオでは、後方互換性のために厳密な直交変換 $B_{\perp}$ を用いる。単独で用いた場合、$\mathcal{L}_{F}$ は新しいモデルの表現との互換性は保証するものの、後方互換性の達成には著しく失敗することが観察される。この挙動は、$\mathcal{L}_{F}$ に固有の顕著な前方バイアスを示している。後方整列損失 $\mathcal{L}_{B}$ のみでは後方互換性を促進する一方で、前方適応済み表現の性能を低下させる。対照損失 $\mathcal{L}_{C}$ のみでは、モデル間整列およびクラス内クラスタリングが大幅に改善され、後方互換性と前方互換性の双方を支える。$\mathcal{L}_{F} + \mathcal{L}_{B} + \mathcal{L}_{C}$ の組み合わせは、互換性の各シナリオにおいて総合的に最も高い性能を達成しており、前方変換学習と後方変換学習のバランスを維持するうえで各損失成分が重要であることを強調している。

Tab. [\[tab:loss_combo_cmc_tick_2\]](#tab:loss_combo_cmc_tick_2) は、下流タスク設定（CUB dataset）におけるこれら損失項の影響を示している。このとき、$\phi_{old}$ は ResNet-18、$\phi_{new}$ は ViT-L-16 であり、$\lambda = 12$ の $\lambda$-Orthogonality を用いている。Tab. [\[tab:loss_combo_cmc_tick\]](#tab:loss_combo_cmc_tick) と同様に、後方損失 $\mathcal{L}_{B}$ を除外しても前方互換性は良好に保たれるが、後方互換性の性能は著しく低下する。対照損失 $\mathcal{L}_{C}$ を除外すると、下流タスクへの適応が大きく低下し、$B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$ の値が低下する。すべての損失項 $\mathcal{L}_{F} + \mathcal{L}_{B} + \mathcal{L}_{C}$ を用いると、前方・後方互換性の双方において一貫して最良またはそれに近い結果が得られ、これらの項が相補的であることが示される。

これらの分析は、各損失項が、さまざまなタスクにわたる包括的なモデル互換性の達成に向けて、それぞれ独自かつ重要な寄与を持つことを示している。

# Distance metric for Partial Backfilling Ordering 

提案する partial backfilling 戦略は、距離指標 $d$ によって導かれる。この指標は、各埋め込みベクトル $F(\mathbf{h}^k)$ と対応するクラス平均 $\boldsymbol{\mu}_c$ との非類似度を測定する。本節では、gallery set における画像の backfilling の有効な順序付けを決定するうえで、異なる距離指標が与える影響を調べる。partial backfilling における画像の順位付けのために、2 つの距離指標――Mean Squared Error (MSE) と Cosine Distance――を比較する。各指標の性能は、Extending Classes 設定（Tab. [\[tab:b_ext_abl\]](#tab:b_ext_abl)）と Independently Pretrained Models 設定（Tab. [\[tab:b_arch_abl\]](#tab:b_arch_abl)）という 2 つの異なる実験条件の下で評価される。MSE は特徴ベクトル間のユークリッド距離を計算し、角度差と大きさの差の双方を捉える。Tab. [\[tab:b_ext_abl\]](#tab:b_ext_abl) および Tab. [\[tab:b_arch_abl\]](#tab:b_arch_abl) に示すように、MSE は一般に堅牢な性能を示し、とりわけ CMC-Top1 の観点で優れている。対照的に、Cosine Distance は正規化された特徴ベクトル間の角度距離を測定し、大きさを無視して方向の類似性を強調する。結果は、Cosine Distance が mAP の観点でわずかに良好な性能を達成し、MSE と同等の CMC-Top1 スコアを与えることを示している。

<figure>
<p>![](assets/fig15.png)</p>
</figure>

<figure>
<p>![](assets/fig16.png)</p>
</figure>

[]

+-----------------+-----------------------+
| Method          | $\widetilde{M}$       |
+:================+:=========:+:=========:+
| 2-3             | CMC-Top1  | mAP       |
+-----------------+-----------+-----------+
| MSE             | 61.20     | 36.46     |
+-----------------+-----------+-----------+
| Cosine Distance | **61.68** | **37.10** |
+-----------------+-----------+-----------+

<figure>
<p>![](assets/fig17.png)</p>
</figure>

<figure>
<p>![](assets/fig18.png)</p>
</figure>

[]

+-----------------+-----------------------+
| Method          | $\widetilde{M}$       |
+:================+:=========:+:=========:+
| 2-3             | CMC-Top1  | mAP       |
+-----------------+-----------+-----------+
| MSE             | **76.59** | 57.72     |
+-----------------+-----------+-----------+
| Cosine Distance | 76.49     | **58.18** |
+-----------------+-----------+-----------+

[]

# Method Complexity and Broader Applicability 

#### Method Complexity.

我々の手法は 2 つの行列のみの学習を必要とし、最適化すべきパラメータ数は少ない。さらに、本手法は抽出済み埋め込みのみに基づいて動作するため、基盤となるモデルに関する知識を一切必要とせず、したがって異なる目的関数（Appendix 8 参照）、アーキテクチャ、および学習された表現の種類にまたがって適用可能である。

表現クラスタリング損失を伴わない整列損失のみに焦点を当てる手法（例えば FCT [[#^ref-25|25]]）や、事前学習済みモデルの特定のアーキテクチャ要素を必要とする手法（例えば FastFill [[#^ref-22|22]] は新しいモデルの classifier へのアクセスを必要とする）とは対照的に、本手法はこれらの制約に対処する。加えて、既存のベースラインが前方適応のみを提供するのに対し、本手法は前方互換性と後方互換性の双方を達成するよう設計されており、従来研究が満たしていない実用上の要請に対応している。例えば以下の通りである。

- $B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$ は、ベースラインと比較してより高い retrieval 値を与える。

- $B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$ は、本手法によってのみ達成可能である。実用上、これは gallery の全要素が $F$ によって前方適応される前であっても互換性を確立できることを意味する。

- 本手法は統一された表現空間を提供するため、gallery がハイブリッド形式、すなわち一部の要素はすでに $F$ により適応済みで、他は未適応である場合でも、$B_{\perp}(\phi_{\text{new}})$ を用いることで互換性を依然として保証できる。これは FCT [[#^ref-25|25]] によっても FastFill [[#^ref-22|22]] によっても達成できない。

Eq. [\[eq:contr\]](#eq:contr) で定義される対照損失は、同一クラスの埋め込みを互いに近づけ、異なるクラスの埋め込みを引き離すために、クラスラベルの利用に依拠している。クラスラベルが利用できないシナリオでは、Eq. [\[eq:contr\]](#eq:contr) は自然に教師なし対照損失へと帰着し、これは CLIP モデルの学習に用いられる目的関数 [[#^ref-62|62]] に類似している。この教師なし設定では、異なるモデルに由来する表現のペアを対比し、クラスタリングは――直接的に強制できないため――埋め込みの類似性に起因する副産物となる。したがって、本手法は柔軟であり、下流タスクにおけるラベルの有無に応じて、教師あり学習と教師なし学習の双方のシナリオに適用可能である。

#### Broader Applicability.

[[#^ref-36|36]] で示されているように、soft orthogonalization は学習中の CNN の全重みを正則化するために適用されており、我々が提案する $\lambda$-orthogonal regularization がもたらす高い可塑性の恩恵を受け得る。retrieval は互換性評価の標準的シナリオであるが [[#^ref-15|15]]、本手法は学習された表現のモデル整列とクラスタリングに焦点を当てているため、表現適応を必要とするあらゆるタスクに広く適用可能である。下流タスク適応実験（Sec. 4.4 参照）で示されるように、我々の正則化手法は厳密な直交制約と比較して性能を改善し、domain adaptation シナリオにおいても価値ある手法である。さらに、幾何学的一貫性を保ちつつ適応性を許容することは、近年 multimodal training における continual learning の文脈で検討されている [[#^ref-67|67]]。しかし [[#^ref-67|67]] の著者らは、この性質を正則化制約を直接適用するのではなく、知識統合損失を通じて間接的に促進している。これは、今後の研究可能性と、さまざまな表現学習分野における我々の $\lambda$-orthogonal regularization の潜在的適用可能性の双方を浮き彫りにしている。

# Limitations 

本手法は、新しいモデルの埋め込み空間が古いモデルのそれよりも表現力に富む（例えば、retrieval 精度が高い、クラスタリングが強い）という仮定に依拠している。更新後のモデルが同等でない、あるいは品質が低い場合、たとえば domain mismatch、学習データ不足、アーキテクチャ上の劣化などに起因して、前方・後方の両方のアダプタが性能向上に寄与しないか、あるいは互換性をさらに損なう可能性がある。多くの実用システムでは、大規模化則 [[#^ref-68|68]][[#^ref-69|69]][[#^ref-70|70]][[#^ref-71|71]]（すなわち、より大きなモデルとより多くのデータは一般により良い特徴表現をもたらす）により、この仮定は正当化される。下流タスク適応については、我々の $\lambda$-orthogonal regularized adapter はさまざまな retrieval タスクにわたり高い性能と互換性を示す一方で、直交閾値（$\lambda$）の手動調整が必要である。元のモデルの幾何構造を保持することと、新しいデータへ適応するのに十分な可塑性を許容することのトレードオフは、$\lambda$ の選択に決定的に依存する。実際には、このハイパーパラメータは、交差検証または下流データセットの保留部分に対する小規模なハイパーパラメータ探索によって選択できる。我々の実験では $\lambda=12$ が良好なバランスを与えることが分かったが（Appendix 10）、異なる下流ドメイン（例えば、fine-grained カテゴリと coarse カテゴリ）や適応済み表現では、最適性能を達成するために $\lambda$ の異なる調整が必要となる可能性がある。このパラメータの自動化または自己調整は未解決課題として残されている。

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
