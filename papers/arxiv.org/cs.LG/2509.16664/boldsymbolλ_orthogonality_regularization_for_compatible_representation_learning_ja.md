---
title: "$\boldsymbolλ$-Orthogonality Regularization for Compatible Representation Learning（日本語訳）"
tags: [paper-translation]
---

[[boldsymbolλ_orthogonality_regularization_for_compatible_representation_learning|← 論文ノート]]

# $\boldsymbol{\lambda}$-Orthogonality Regularization for Compatible Representation Learning

Simone Ricci 1,2 Niccolò Biondi 1,2 Federico Pernici 1,2 Ioannis Patras 3 Alberto Del Bimbo 1,2 1 DINFO (Department of Information Engineering), University of Florence, Italy 2 MICC (Media Integration and Communication Center) 3 Queen Mary University of London, UK Corresponding author: simone.ricci@unifi.it .

###### Abstract

検索システムは、ますます高性能なモデルによって学習された表現に依存している。しかし、学習コストの高さと学習済み表現の不整合性のため、表現間の通信を容易にし、独立に学習されたニューラルネットワーク間で互換性を確保することへの関心が高まっている。文献では、異なる学習済み表現を適応させるために主として二つのアプローチが用いられる。すなわち、特定の分布にはよく適合するが元の表現を大きく変化させうるアフィン変換と、厳しい幾何学的制約の下で元の構造を保存する一方、適応性が制限される直交変換である。重要な課題は、更新されたモデルの潜在空間を、下流分布上で従来モデルの潜在空間と整合させつつ、新たに学習された表現空間を保持することである。本論文では、アフィン変換を学習しつつ、緩和された直交制約、すなわち $\lambda$-Orthogonality regularization を課すことで、元の学習済み表現を保持したまま分布特有の適応を実現する。多様なアーキテクチャとデータセットにわたる広範な実験により、本手法がモデルのゼロショット性能を保持し、モデル更新間の互換性を確保することを検証する。コードは [https://github.com/miccunifi/lambda_orthogonality](https://github.com/miccunifi/lambda_orthogonality.git) で利用可能である。

## 1 Introduction

検索タスクは、顔認識 [[#^ref-1|1]] ; [[#^ref-2|2]] ; [[#^ref-3|3]] 、画像位置特定 [[#^ref-4|4]] ; [[#^ref-5|5]] ; [[#^ref-6|6]] 、および物体同定 [[#^ref-7|7]] ; [[#^ref-8|8]] ; [[#^ref-9|9]] などの実世界応用においてますます重要になっている。画像検索では、ラベル付き画像からなるギャラリーとクエリ画像とを照合し、理想的には同一クラスに属する関連画像を同定する。高次元画像の代わりに、検索では埋め込みモデルから得られる低次元の特徴ベクトルを用いる。検索性能の向上は、より表現力の高いネットワークアーキテクチャ [[#^ref-12|12]] 、新しい学習技法（例：損失関数）や学習パラダイム [[#^ref-13|13]] ; [[#^ref-14|14]] ; [[#^ref-15|15]] を活用するために、埋め込みモデル [[#^ref-10|10]] ; [[#^ref-11|11]] を更新することによって達成されることが多い。しかし、ニューラルネットワークは、同一のデータを同一の手法およびアーキテクチャで学習した場合であっても、互換的な特徴をほとんど生成しない [[#^ref-16|16]] 。その結果、新しいクエリの特徴を古いギャラリーの特徴と照合することは、不整合のために検索性能を低下させうる [[#^ref-15|15]] 。この問題に対処するには、旧モデルが生成したギャラリー特徴を新モデルが生成したものに置き換える必要があるが、この計算コストの高い処理は backfilling として知られる。ベースモデルを更新しつつ、その後方互換性を確保し、backfilling を回避するという課題は、広範に研究されてきた [[#^ref-17|17]] ; [[#^ref-15|15]] ; [[#^ref-18|18]] ; [[#^ref-19|19]] ; [[#^ref-20|20]] ; [[#^ref-21|21]] 。さらに、partial backfilling として知られるギャラリー更新の最適戦略も、近年注目を集め始めている [[#^ref-22|22]] 。

アーキテクチャの変更や互換性確保のための追加損失は、更新モデルの性能を低下させうる [[#^ref-23|23]] ; [[#^ref-24|24]] 。この問題に対処するため、研究は、パラメータ効率の高いアダプタを用いて、ベースモデルの表現を独立に学習された改良モデルの表現に整合させることに焦点を当ててきた [[#^ref-22|22]] ; [[#^ref-25|25]] 。一方、マニフォールド仮説 [[#^ref-26|26]] ; [[#^ref-27|27]] は、ニューラルネットワークが通常、同一データ分布に対する潜在空間表現を生成し、それらは主として変換によって異なるにすぎないことを示唆する。したがって、ある表現を別の表現に写像するには、機能的に等価なモデルが同一の潜在多様体を近似するため、少数のパラメータで足りる [[#^ref-28|28]] ; [[#^ref-29|29]] ; [[#^ref-27|27]] 。ゆえに、新しい表現空間を以前のものに整列させる単純な変換によって、更新モデルの後方互換性を与えることができる。

Figure 1 : 検索システム更新時に表現互換性を達成するための提案手法の概観。新たに独立に学習されたモデルは、幾何学的構造を保持する直交変換 $B_{\perp}$ により旧表現空間へ整列される。前方変換 $F$ は、旧表現を新モデルの後方整列済み空間へ写像する。学習時には変換パラメータのみを最適化し、モデルパラメータは固定のままである。

![](assets/fig01.png)

最近の研究では、特定のデータ点を参照として用いながら、ベースモデルの潜在空間（source space）を別モデルの潜在空間（target space）へ適応させるためのアフィン写像および直交写像に焦点が当てられている [[#^ref-30|30]] ; [[#^ref-28|28]] ; [[#^ref-31|31]] 。plasticity-stability パラダイム [[#^ref-32|32]] の観点では、アフィン写像は高い適応性（plasticity）を提供する一方で、source space の構成を変化させうる [[#^ref-33|33]] ; [[#^ref-34|34]] 。逆に、直交写像は source space の幾何学的構造（stability）を維持するが、異なる分布への適応性は持たない。source space の幾何学的構造、特にそれが target space よりも情報量に富む場合 [[#^ref-28|28]] ; [[#^ref-35|35]] を保存しつつ、適応性も実現するために、本論文では新たな正則化項を提案する。先行研究 [[#^ref-36|36]] とは異なり、本項は、超パラメータ $\lambda$ により制御される所定の近接範囲内に変換を直交条件の近傍に留めるよう制約する。

本論文では、図 [1](https://arxiv.org/html/2509.16664v2#S1.F1) に示すように、異なる表現空間間での変換を学習することにより、独立に学習されたモデル間の互換性を確保する課題に取り組む。本研究の貢献は以下の通りである。

- • 我々は $\lambda$-Orthogonality regularization を提案する。これは、元の表現空間の大域的構造を保持しつつ、下流タスクに対して局所的なわずかな適応を可能にする、緩和された直交制約である。
- • 我々は supervised contrastive loss を用いて表現互換性を高める。これは、モデルアーキテクチャに依存せずに、同一クラス内クラスタリングとモデル間の特徴整列を促進する。
- • 我々は多様なアーキテクチャとデータセットにわたる広範な実験を行い、本手法がモデル間の互換性を確保するだけでなく、ベースモデルの潜在空間の幾何構造の保持も促進し、下流タスクでの精度向上をもたらすことを示す。
- • 我々は、検索性能を改善しつつギャラリー更新プロセスを最適化する、新しいアーキテクチャ非依存の backfilling 戦略を提案する。

## 2 Related Works

[[#^ref-16|16]] が示したように、二つのモデルの特徴表現は、同じデータで学習されていたとしても一般には一致せず、検索システムにおいて高コストな backfilling を生じさせる。これを回避するため、[[#^ref-15|15]] は Backward Compatible Training (BCT) を導入し、旧分類器を参照として固定することで、新しい埋め込みが既存クラスのプロトタイプに整合するようにした。加えて、モデル表現間の互換性に関する形式的定義も与えた。その後の研究はこの基盤を拡張し、新表現を以前の表現によりよく整合させるための追加正則化技法を取り入れ [[#^ref-21|21]] ; [[#^ref-37|37]] ; [[#^ref-20|20]] ; [[#^ref-38|38]] ; [[#^ref-39|39]] 、特定のアーキテクチャ設計も実装してきた [[#^ref-18|18]] ; [[#^ref-13|13]] ; [[#^ref-40|40]] 。しかし、更新された backward-compatible モデルの性能は、しばしば独立に学習されたモデルの性能に届かない [[#^ref-23|23]] 。これは、互換性を達成するために課される正則化の帰結である。これを避けるため、[[#^ref-23|23]] および [[#^ref-24|24]] は、更新時に旧クラスの表現を整列させたまま、新クラスを含むよう表現空間を拡張することを提案した。独立に学習されたモデル間の互換性を確保するため、写像ベースの戦略が開発されてきた [[#^ref-41|41]] ; [[#^ref-42|42]] ; [[#^ref-43|43]] 。[[#^ref-25|25]] により詳述された Forward Compatible Training (FCT) は、各データ点に対する追加の副情報を組み込みながら、旧モデルの埋め込みを新モデルの空間へ整列させる関数を導入する。[[#^ref-25|25]] が指摘するように、これらの変換に伴う計算オーバーヘッドは、画像を埋め込みモデルに通すための要求に比べればごく小さい。FastFill [[#^ref-22|22]] は、新モデルの分類器を用いることで前方変換学習を改善し、新モデルを活用してギャラリー backfilling プロセスを最適化するベイズ戦略を提案する。これに対して我々は、モデル更新時に前方互換性だけでなく後方互換性も確保する一連の変換関数を提案し、とりわけ後方写像における直交性に焦点を当てる。さらに、同一クラス内クラスタリングとモダリティ間整列を促進する supervised contrastive loss を提案し、これにより適応を強化する。最後に、事前抽出されたギャラリー表現上で直接動作する距離尺度に基づく新しいギャラリー backfilling 戦略を提案し、基盤となるアーキテクチャに依存しないものとする。

## 3 Method

独立に学習されたモデル間で互換的な表現を達成するために、複数の変換から成る理論的基盤を持つパイプラインを導入する。まず、Sec. [3.1](https://arxiv.org/html/2509.16664v2#S3.SS1) では、[[#^ref-15|15]] により導入された互換性の定義を述べる。Sec. [3.2](https://arxiv.org/html/2509.16664v2#S3.SS2) および [3.3](https://arxiv.org/html/2509.16664v2#S3.SS3) では、新しい後方互換性手法を導入する。これは、新モデルの表現を旧モデルの表現に整列させるものであり、厳密な直交変換、あるいは下流タスクへの適応時には、我々が提案する $\lambda$-Orthogonality 制約によって正則化された変換のいずれかを用いる。次に、Sec. [3.4](https://arxiv.org/html/2509.16664v2#S3.SS4) では、前方変換学習を提示する。これは、アフィン変換またはより複雑な変換を介して、旧モデルの表現を新たに適応されたモデルの表現へ整列させ、効果的なギャラリー集合の更新を可能にする。さらに、変換学習中に supervised contrastive loss（Sec. [3.5](https://arxiv.org/html/2509.16664v2#S3.SS5)）を適用し、モデル表現間の整列を改善するとともに、同一クラス内クラスタのコンパクト性を高めることで、Def. [3.1](https://arxiv.org/html/2509.16664v2#S3.Thmtheorem1) で定義された互換性基準を満たす。最後に、Sec. [3.6](https://arxiv.org/html/2509.16664v2#S3.SS6) では、改善された表現でギャラリーを最適化された順序で backfilling するための新しい順序付け戦略を提案する。本手法全体を通して、すべてのモデルはパラメータを凍結した固定の特徴抽出器として扱われ、変換層のみが学習される。

(a) 異なる $\lambda$ における Eq. 6 の値。

![](assets/fig02.png)

### 3.1 Backward-Compatible Representations Definition

[[#^ref-15|15]] により導入された表現間の Backward-Compatibility の定式化は、異なるモデル間の潜在空間通信の概念と密接に関係している [[#^ref-30|30]] 。Backward-compatible representations の形式的定義は次のように規定される。

###### Definition 3.1 ( Backward-Compatibility ) .

ステップ $k$ で学習されたモデルの表現が、後続ステップ $t$ で学習された別のモデルの表現と互換的であるとは、$k<t$ であり、かつ次の条件が満たされる場合をいう：

|    | $$\forall\,i,j:\;\bigl(y_{i}=y_{j}\implies d(\mathbf{h}_{i}^{t},\mathbf{h}_{j}^{k})\leq d(\mathbf{h}_{i}^{k},\mathbf{h}_{j}^{k})\bigr)\;\wedge\;\bigl(y_{i}\neq y_{j}\implies d(\mathbf{h}_{i}^{t},\mathbf{h}_{j}^{k})\geq d(\mathbf{h}_{i}^{k},\mathbf{h}_{j}^{k})\bigr)$$   |    | (1)   |
|----|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----|-------|

ここで、$d(\cdot,\cdot)$ は距離関数であり、$y_{i}$ および $y_{j}$ は、それぞれ抽出された表現ベクトル $\mathbf{h}_{i}$ と $\mathbf{h}_{j}$ に対応するクラスラベルである。Def. [3.1](https://arxiv.org/html/2509.16664v2#S3.Thmtheorem1) の不等式は、新しいモデルの表現が、旧い表現と比較して、同一クラスの画像をクラスタリングし、異なるクラスの画像からそれらを分離するという点で、少なくとも従来モデルと同等以上に機能すべきことを示している。

### 3.2 Backward Transformation

relative encoding [[#^ref-30|30]] の貢献の一つは、実際には、表現空間が同一または類似のデータ意味論を共有する場合、しばしば角度保存変換によってのみ互いに異なるという観察である。さらに、[[#^ref-28|28]] は、学習された意味論に差異がある場合には、Procrustes analysis [[#^ref-44|44]] により学習された、角度と距離の双方を保存する変換が、角度保存写像のみよりも、クロスアーキテクチャおよびクロスモダリティの分類タスクにおいて優れた性能を示すことを実証している。変換 $T$ は、空間内の任意の 2 点 $a$ と $b$ の間の角度と距離を保存するとき、isometry と定義される。形式的には、写像 $T:\mathbb{R}^{n}\to\mathbb{R}^{n}$ が isometry であるとは、次の条件が成り立つことである：$\|T(a)-T(b)\|_{2}=\|a-b\|_{2},\quad\forall a,b\in\mathbb{R}^{n}$。ここで $\|\cdot\|_{2}$ はユークリッドノルムを表し、同値に、他の空間における一般的な距離計量を表す。我々はこの性質を利用し、直交変換を用いて更新モデルの空間をベースモデルの空間に整列させることで、後方互換な表現を実現する。これにより、更新をまたいで統一された表現空間が維持され、変換の等長性により更新モデルの幾何学的性質と性能が保存される。

ベースモデル $\phi^{k}$ とその更新版 $\phi^{t}$ を考え、$k&lt;t$ とし、それぞれの表現ベクトルを $\mathbf{h}^{k}\in\mathbb{R}^{d}$ および $\mathbf{h}^{t}\in\mathbb{R}^{n}$ とする。このとき、更新モデルの埋め込み空間をベースモデルの空間へ写像する直交変換 $B_{\perp}:\mathbb{R}^{n}\rightarrow\mathbb{R}^{n}$ を学習する。厳密な直交性を課すために、一般的な変換 $B$ は歪対称行列 $P$ の行列指数としてパラメータ化され、$B=e^{P}$ とする。ここで、$P$ の上三角成分は学習可能パラメータである [[#^ref-45|45]] 。更新表現空間とベース表現空間の整列を強制するため、$\mathbf{h}^{k}$ と変換後の $\mathbf{h}^{t}$ の間の Mean Squared Error 損失を最小化することにより、変換 $B_{\perp}$ を最適化する：

|    | $$\mathcal{L}_{B}=&#124;&#124;B_{\perp}(\mathbf{h}^{t})-\mathbf{h}^{k}&#124;&#124;_{2}^{2}$$   |    | (2)   |
|----|------------------------------------------------------------------------------------------------|----|-------|

変換 $B_{\perp}$ は正方行列であるため、2つの表現空間の次元が異なる場合には、より高次元の特徴ベクトルを切り詰めて、より小さい表現空間の次元に合わせる。

### 3.3 $\boldsymbol{\lambda}$-Orthogonality Regularization

変換 $B$ に対する厳密な直交制約（高い安定性）は、モデル分布がアダプタの学習対象と異なる場合、すなわち、プライベートモデルが抽出埋め込みのみをユーザに提供する場合には、必ずしも理想的ではない。このような制約を課すと、下流タスクにとって新たに有用な情報の統合が制限されうる。これに対し、幾何学的正則化を伴わないアフィン変換（高い可塑性）は、更新モデルの表現を破壊しうる [[#^ref-46|46]] ; [[#^ref-47|47]] 。[[#^ref-36|36]] で述べられているように、重み行列 $W\in\mathbb{R}^{n\times n}$ とバイアス項 $b\in\mathbb{R}^{n}$ から成る変換 $B:\mathbb{R}^{n}\rightarrow\mathbb{R}^{n}$ に対して、ソフトな直交制約を適用できる。先行研究 [[#^ref-48|48]] ; [[#^ref-49|49]] ; [[#^ref-50|50]] は、次のように定義される損失関数を最小化することで、重み行列の Gram 行列を単位行列に近づける制約を提案している。

|    | $$\mathcal{L}_{orth}=&#124;&#124;W^{T}W-I&#124;&#124;_{F}$$   |    | (3)   |
|----|---------------------------------------------------------------|----|-------|

ここで $||\cdot||_{F}$ は Frobenius ノルムを表し、$W$ は変換 $B$ の重みである。これは、パラメータ集合を Stiefel manifold [[#^ref-50|50]] の近傍に制限する重み減衰項として解釈できる。しかし、このアプローチでは、変換に課すことのできる直交性の具体的な程度を制御できない。

このため、重み行列の Gram 行列が単位行列にどの程度近いかを指定するしきい値 $\lambda$ を導入する。素朴な解としては、損失が Gram 行列に直接影響することから、重み行列の Gram 行列がしきい値 $\lambda$ に達した時点で $\mathcal{L}_{orth}$ の最適化を停止する方法が考えられる。

|    | $$\min_{W}\;&#124;&#124;W^{T}W-I&#124;&#124;_{F}\quad\text{s.t.}\quad&#124;&#124;W^{T}W-I&#124;&#124;_{F}\geq\lambda$$   |    | (4)   |
|----|--------------------------------------------------------------------------------------------------------------------------|----|-------|

この目的は、Heaviside step function [[#^ref-51|51]] ; [[#^ref-52|52]] をパラメータ $\lambda$ により平行移動したもの、すなわち $H(x-\lambda)=\mathbf{1}_{\{x\geq\lambda\}}$ を用いることで直接達成できる。この関数 $H$ は、最小化過程における直交性の程度を制御する効率的な機構を提供し、Frobenius ノルムがしきい値 $\lambda$ を超えたときに、Eq. [3](https://arxiv.org/html/2509.16664v2#S3.E3) の正則化項を実質的に無効化する。

|    | $$\mathcal{L}_{\lambda}=H(\&#124;WW^{T}-I\&#124;_{F}-\lambda)\cdot\&#124;WW^{T}-I\&#124;_{F}.$$   |    | (5)   |
|----|---------------------------------------------------------------------------------------------------|----|-------|

しかし、このアプローチは、[[#^ref-53|53]] で指摘されているように、損失関数に不連続性を導入する。特に同研究は、これらの sigmoid 関数と Heaviside step function との近さの評価に焦点を当て、Hausdorff distance に対する厳密な上界および下界を与えている。これらの理論的・実証的分析を踏まえ、我々は、制約の効果が徐々に調整され、しきい値 $\lambda$ からの距離に応じて罰則が強まったり弱まったりすることを保証する、滑らかな調整関数を提案する。具体的には、次の損失関数を最適化する新しい $\lambda$-Orthogonality Regularization 項を定式化する。

|    | $$\mathcal{L}_{\lambda}=\sigma\left(\alpha\left(\&#124;WW^{T}-I\&#124;_{F}-\lambda\right)\right)\cdot\&#124;WW^{T}-I\&#124;_{F}$$   |    | (6)   |
|----|-------------------------------------------------------------------------------------------------------------------------------------|----|-------|

ここで $\sigma(\cdot)$ は sigmoid 関数、$\alpha$ はスケーリング係数である。

(a) Source space

![](assets/fig03.png)

sigmoid 関数は連続的なスイッチとして機能し、Fig. [2(a)](https://arxiv.org/html/2509.16664v2#S3.F2.sf1) に示すように、$\lambda$ の値の近傍で正則化項を徐々にオン・オフする。一方、スケーリング係数 $\alpha$ は sigmoid 関数の急峻さを制御し、それにより $\|WW^{T}-I\|_{F}$ の値がしきい値 $\lambda$ に近づく際に、正則化がどれほど急激に有効化・無効化されるかを決定する。Fig. [2(b)](https://arxiv.org/html/2509.16664v2#S3.F2.sf2) では、正則化損失に適用される異なる急峻さのレベルを示している。$\alpha$ が増加するほど、その挙動は Heaviside step function により近く収束する。

$\lambda$-orthogonality regularization の挙動をさらに分析するため、ランダム初期化された重み行列 $W$ を持つ変換 $B$ に Eq. [6](https://arxiv.org/html/2509.16664v2#S3.E6) を適用して最適化する。Fig. [2(c)](https://arxiv.org/html/2509.16664v2#S3.F2.sf3) に示すように、これらの角度の kernel density estimation (KDE) は、正則化に用いる $\lambda$ の値に応じて変化する。$\lambda$ の値が小さいほど、列ベクトルはより直交的になり、特に $\lambda=0$ のとき、我々の正則化は Eq. [3](https://arxiv.org/html/2509.16664v2#S3.E3) に等しい。Fig. [3](https://arxiv.org/html/2509.16664v2#S3.F3) は、source representation space (Fig. [3(a)](https://arxiv.org/html/2509.16664v2#S3.F3.sf1) ) を full MNIST dataset 上で学習し、target representation space (Fig. [3(b)](https://arxiv.org/html/2509.16664v2#S3.F3.sf2) ) を MNIST の最初の 5 クラス上で学習したものに整列させるために学習された、アフィン変換（Fig. [3(c)](https://arxiv.org/html/2509.16664v2#S3.F3.sf3) ）、厳密な直交変換（Fig. [3(d)](https://arxiv.org/html/2509.16664v2#S3.F3.sf4) ）、および $\lambda$-orthogonality regularized 変換（Fig. [3(e)](https://arxiv.org/html/2509.16664v2#S3.F3.sf5) ）の効果を示している。この玩具実験は、$\lambda$-orthogonal 制約が、厳密な直交性を緩和しつつ source feature space の構造の保存を促すことで整列を改善し、制約のない変換とは対照的であることを示している。

### 3.4 Forward Transformation

新しいモデルの表現を旧いモデルの表現へ写像する backward transformation に加えて、forward transformation $F:\mathbb{R}^{d}\rightarrow\mathbb{R}^{n}$ を定式化することも可能である。この変換は、旧いモデルの表現ベクトル $\mathbf{h}^{k}\in\mathbb{R}^{d}$ を、新しいモデルの表現 $\mathbf{h}^{t}\in\mathbb{R}^{n}$ に写像する。新しいモデルの表現は旧いモデルの表現より優れているため、変換 $F$ は、改善された表現によりよく適応するよう、アフィン（高可塑性）または複数の射影層であるべきである。変換 $F$ は、[[#^ref-25|25]] で述べられているアプローチに従い、2つの表現間の Mean Squared Error、すなわち $||F(\mathbf{h}^{k})-\mathbf{h}^{t}||_{2}^{2}$ を最小化することで学習される。この概念は latent space communication [[#^ref-30|30]] ; [[#^ref-31|31]] と密接に関連しており、ここでは $d\big(\mathbf{h}^{k}_{i},\mathbf{h}^{k}_{j}\big)=d\big(\mathcal{T}\ \mathbf{h}^{t}_{i},\mathcal{T}\ \mathbf{h}^{t}_{j}\big)$ であり、$\mathcal{T}$ は一般的な変換である。先行手法 [[#^ref-25|25]] ; [[#^ref-22|22]] では、旧い表現 $\mathbf{h}^{k}$ は変換 $F$ を通じて新しい $\mathbf{h}^{t}$ に直接整列されるが、$\mathbf{h}^{k}$ と $F(\mathbf{h}^{k})$ の間に非互換性が生じる。Sec. [3.2](https://arxiv.org/html/2509.16664v2#S3.SS2) で述べたように、後方の直交変換 $B_{\perp}$ は新しい表現を旧い表現に再整列させる。旧い特徴を新しい表現 $\mathbf{h}^{t}$ に直接適合させるのではなく、我々はそれらを $B_{\perp}(\mathbf{h}^{t})$ に適合させ、モデル更新をまたいだ統一的な整列を保証する。さらに、変換 $F$ と $B_{\perp}$ は同一の学習データを利用するため、同時に学習可能である。したがって、我々の方法論における forward alignment loss は次のように定義される：

|    | $$\mathcal{L}_{F}=&#124;&#124;F(\mathbf{h}^{k})-B_{\perp}(\mathbf{h}^{t})&#124;&#124;_{2}^{2}$$   |    | (7)   |
|----|---------------------------------------------------------------------------------------------------|----|-------|

抽出された表現が、Sec. [3.3](https://arxiv.org/html/2509.16664v2#S3.SS3) で論じたように、2つのモデルの訓練集合とは異なるデータセットに由来する場合、厳密に直交な $B_{\perp}$ の代わりに、$\lambda$-orthogonal regularized transformation $B_{\lambda}$ を用いることができる。

### 3.5 Intra-class Clustering and Inter-Model Alignment

Sec. [3.1](https://arxiv.org/html/2509.16664v2#S3.SS1) で述べたように、Def. [3.1](https://arxiv.org/html/2509.16664v2#S3.Thmtheorem1) で定義された compatibility inequalities は、compatibility を達成するために、alignment だけでなく、より高い cluster の集中も必要とする。これに対し、[[#^ref-22|22]] は追加の訓練損失 $\mathcal{L}_{disc}$ を導入している。これは [[#^ref-15|15]] の influence loss とは異なり、旧モデルではなく新モデルの classifier に直接依拠する。しかし、$\mathcal{L}_{disc}$ は新モデルの classifier および訓練損失へのアクセスに依存するため、特に新モデルのアーキテクチャが未知である場合（例えば、private または online model 由来の embedding vector）には適用可能性が制限される。これを克服するために、representation vector に直接適用する supervised contrastive loss の使用を提案する。この損失は、alignment と clustering のために representation vector を直接活用するため、classifier やアーキテクチャに関する知識を必要としない。Supervised contrastive loss [[#^ref-54|54]] は、$\mathbf{q}_{i}$ と $\mathbf{p}_{i}$ の間の cross-entropy loss を最小化する。

|    | $$\mathcal{L_{\text{contr}}}=-\sum_{i=1}^{K}\mathbf{p}_{i}\log\mathbf{q}_{i}$$   |    | (8)   |
|----|----------------------------------------------------------------------------------|----|-------|

ここで $\mathbf{q}_{i}$ は、L2-normalized feature $\mathbf{h}$ と各候補との dot-product similarities に temperature-scaled softmax を適用することで、サンプル $i$ に割り当てられる確率を表し、$\mathbf{p}_{i}$ は、意味的に一致する（同一クラスの）候補すべてに等しい重みを置き、それ以外には 0 を与える正規化された ground-truth indicator distribution である。具体的には、この損失関数の組合せを用い、目的関数 $\mathcal{L}_{\text{C}}$ を次のように定義した。

|    | $$\displaystyle\mathcal{L}_{\text{C}}=\mathcal{L}_{\text{contr}}(F(\mathbf{h}^{k}),B_{\perp}(\mathbf{h}^{t}))\ +\mathcal{L}_{\text{contr}}(F(\mathbf{h}^{k}),\mathbf{h}^{k})$$   |    | (9)   |
|----|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----|-------|

この損失は、適応された表現間での clustering を促進すると同時に、それらを旧モデルの表現と整列させることで、feature representation の intra-class clustering と inter-model alignment を促進する。

本フレームワークの全体損失関数は、4つの構成要素、すなわち forward alignment loss $\mathcal{L}_{F}$、backward alignment loss $\mathcal{L}_{B}$、contrastive loss $\mathcal{L}_{\text{C}}$、および $\lambda$-Orthogonality regularization term $\mathcal{L}_{\lambda}$ の重み付き和として定義される。形式的には、全損失は次のように表される。

|    | $$\mathcal{L}=w_{1}\cdot\mathcal{L}_{F}+w_{2}\cdot\mathcal{L}_{B}+w_{3}\cdot\mathcal{L}_{C}+\mathcal{L}_{\lambda}$$   |    | (10)   |
|----|-----------------------------------------------------------------------------------------------------------------------|----|--------|

ここで $w_{1}$、$w_{2}$、$w_{3}$ は、各項の寄与を調整するためのスカラー重みである。

### 3.6 Partial Backfilling Strategy

forward-adapted gallery set において、旧モデルの $F(\mathbf{h}^{k})$ を $B_{\perp}(\mathbf{h}^{t})$ に置き換える backfilling サンプルの効果的な順序を決定することは、新たに独立学習されたモデルの性能を可能な限り効率的に達成するうえで極めて重要である。しかし、backfilling の最適順序の特定は、計算的に扱いにくい組合せ最適化問題である [[#^ref-22|22]] 。この課題に対処するため、FastFill [[#^ref-22|22]] は Bayesian Deep Learning に着想を得た順序付けを導入する。このアプローチでは、alignment error を多変量ガウス分布としてモデル化し、mapping function $F$ の訓練中にこの分布の negative log-likelihood を最小化する。しかし、retrieval の観点からは、最も代表的なインスタンス、すなわち異なるクラス間の分離を大きく高めるものは、それぞれの class mean に最も近い embedding である [[#^ref-55|55]] ; [[#^ref-56|56]] 。したがって、情報量の少ない embedding を優先して backfilling することは、クラス間の区別を強化することでシステム性能を向上させる。これを踏まえ、既に抽出済みの representation vector $F(\mathbf{h}^{k})$ に直接基づいて backfill 順序を推定する新たな手法を提案する。まず、forward-adapted gallery set における各クラス $c$ の平均表現ベクトル $\boldsymbol{\mu}_{c}$ を計算する。次に、各 embedding vector $F(\mathbf{h}^{k})$ について、その対応する class mean $\boldsymbol{\mu}_{c}$ からの距離指標 $d$ を算出する。たとえば $d$ は Mean Squared Error として、$d=\|F(\mathbf{h}^{k})-\boldsymbol{\mu}_{c}\|_{2}$ と表せる。$\boldsymbol{\mu}$ からの距離 $d$ が最大の gallery embedding を backfilling の優先対象とし、これにより、新たに backward-adapted independent trained model $B_{\perp}(\mathbf{h}^{t})$ によって生成された query とのマッチングを容易にする。

## 4 Experiments

### 4.1 Image Retrieval Compatibility

Backward compatibility は、gallery set $\mathcal{G}=\{(\mathbf{x}_{i},y_{i})\}_{i=1}^{N_{g}}$ と query set $\mathcal{Q}=\{(\mathbf{x}_{i},y_{i})\}_{i=1}^{N_{q}}$ を含む retrieval task において重要である。これらはそれぞれ $N_{g}$ 枚および $N_{q}$ 枚の画像からなり、対応する class label を持つ。base model は画像から feature vector を抽出して gallery を索引付けし、それらは retrieval task において query set のベクトルとの照合に用いられる。Def. [3.1](https://arxiv.org/html/2509.16664v2#S3.Thmtheorem1) で示された compatibility の定義は、データセット内のすべての datapoint 間の pairwise distance の計算を含む。データセットサイズが大きくなるにつれて、この処理はますます計算負荷が高くなる。次に、ステップ $t$ で更新されたモデルが、ステップ $k$ で訓練された base model と backward-compatible であるとは、Empirical Compatibility Criterion [[#^ref-15|15]] が満たされる場合を指す。

|    | $$M\big(\Phi_{t}^{\mathcal{Q}},\Phi_{k}^{\mathcal{G}}\big)>M\big(\Phi_{k}^{\mathcal{Q}},\Phi_{k}^{\mathcal{G}}\big),\quad\text{with }k<t$$   |    | (11)   |
|----|----------------------------------------------------------------------------------------------------------------------------------------------|----|--------|

ここで $M$ は性能指標を表し、$\Phi^{\mathcal{G}}$ および $\Phi^{\mathcal{Q}}$ は、それぞれ抽出された gallery set と query set を表す。具体的には、$M\big(\Phi_{t}^{\mathcal{Q}},\Phi_{k}^{\mathcal{G}}\big)$ は、ステップ $t$ の更新後モデルの gallery features とステップ $k$ の query features を用いた cross-model retrieval を評価する。これに対し、$M\big(\Phi_{k}^{\mathcal{Q}},\Phi_{k}^{\mathcal{G}}\big)$ は same-model retrieval を指し、gallery features と query features の両方がステップ $k$ における同一モデルに由来する。

#### Partial Backfilling.

gallery set $\Phi^{\mathcal{G}}$ 内の画像の順序 $\pi$ を、$\mathbf{x}_{\pi_{1}},\mathbf{x}_{\pi_{2}},\dots,\mathbf{x}_{\pi_{n}}$ と表し、backfilling fraction $\beta\in[0,1]$ を与えると、部分的に backfilling された gallery set $\Phi^{\mathcal{G}}_{\pi,\beta}$ を次のように定義する。順序の先頭から $N_{g,\beta}=\lfloor\beta N_{g}\rfloor$ 枚の画像は更新後モデルで処理し、残りの画像は旧モデルで処理する。ここで $N_{g}$ は gallery 内の総画像数である。異なる backfilling strategy を評価するために、[[#^ref-22|22]] で導入された backfilling metric $\widetilde{M}$ を用いる。これは次のように定義される。$\widetilde{M}(\Phi^{\mathcal{G}},\Phi^{\mathcal{Q}},\pi)=\mathbb{E}_{\beta\sim[0,1]}M(\Phi^{\mathcal{G}}_{\pi,\beta},\Phi^{\mathcal{Q}}).$ この指標は、$M$ を用いて性能を評価したときの backfilling curve の下の面積である。

### 4.2 Evaluation Metrics and Datasets

先行研究の model compatibility [[#^ref-15|15]] ; [[#^ref-25|25]] に従い、我々は2つの指標を用いて性能を評価する。Cumulative Matching Characteristics (CMC) は、query と gallery features 間の距離を計算することで top-$k$ retrieval accuracy を測定し、$k$ 個の最も近い gallery image のうち少なくとも1つが query の label と一致すれば retrieval 成功とみなす。mean Average Precision (mAP) は、recall の全範囲 $[0,1]$ にわたる precision-recall curve の下の面積を測定する。

提案手法を検証するため、ImageNet1K [[#^ref-57|57]]、CIFAR100 [[#^ref-58|58]]、および CUB200 [[#^ref-59|59]] を用いる。各データセットの validation/test set は query と gallery の両方として機能し、検索時の自明な一致を避けるため、各 query image は gallery から除外する。表中の 'Query/Gallery' という表記は、それぞれ埋め込みを抽出するために用いたモデルを示す。CUB200 と CIFAR100 は downstream task として用いる。

### 4.3 Extending Classes Setting

この設定では、base model を class 数を拡張することで更新する。ImageNet1K の最初の 500 クラスで $\phi_{\text{old}}$ を、全 1000 クラスで $\phi_{\text{new}}$ を、それぞれ独立に学習する。両者とも、PyTorch の標準的な訓練手順 1 1 1 [pytorch/vision/tree/main/references/classification](https://github.com/pytorch/vision/tree/main/references/classification) に従い、embedding dimension 128 の ResNet-34 architecture を用いる。2つのモデルを独立に訓練した後、モデル層を固定したまま Adam と学習率 $0.001$ で adapter を最適化する。我々は、compatible representations を達成するための mapping method である FCT [[#^ref-25|25]] と FastFill [[#^ref-22|22]] を比較対象とする。Tab. [1(a)](https://arxiv.org/html/2509.16664v2#S4.T1.st1) では、Sec. [4.2](https://arxiv.org/html/2509.16664v2#S4.SS2) の指標に従って各手法の性能を要約している。結果は、新しいモデル $\phi_{\text{new}}$ が旧モデル $\phi_{\text{old}}$ と直接は compatible でないことを示している。さらに、2つの mapping method である FCT と FastFill は、gallery および query set の適応済み表現において、両指標の性能を向上させる。しかし、これらの手法が達成するのは新たに訓練されたモデルとの backward compatibility であり、元のモデルとの互換性ではない。対照的に、我々の手法は orthogonal transformation $B_{\perp}$ を通じて新モデルを旧モデルに整列させる。これにより、新旧表現間の compatibility が保証されるとともに、forward adapter $F$ によってもたらされる性能が向上する。Appendix [A](https://arxiv.org/html/2509.16664v2#A1) では、Places365 [[#^ref-60|60]] データセットに関する追加結果を示す。

### 4.4 Independently Pretrained Models adapted on Downstream Task

学習コストの高騰に伴い、事前学習済みモデルの利用はますます一般的になっており、特にローカルデータセットを用いた下流タスクへの適応において重要である。この文脈において、PyTorch hub で利用可能な ImageNet1K データセットで事前学習された2つのモデルを用いる。すなわち、埋め込みサイズ512の ResNet-18 と、より高度な Vision Transformer（ViT-L-16）[[#^ref-61|61]] であり、その埋め込みサイズは1024である。ViT モデルは、改良されたアーキテクチャを有するため、ResNet-18 の更新版とみなされる。Tab. [1(b)](https://arxiv.org/html/2509.16664v2#S4.T1.st2) は、2つの事前学習済みモデルと同一のデータセットを用いたアダプタ学習結果を示しており、Tab. [1(a)](https://arxiv.org/html/2509.16664v2#S4.T1.st1) と同様の傾向を示すとともに、本手法が他のベースラインと同等の性能を達成しつつ、更新されたモデルと旧モデルとの互換性を有することを示している。FastFill とは異なり、本手法では新モデルの分類器を必要とせず、抽出された埋め込みベクトルに直接依拠する。Appendix [B](https://arxiv.org/html/2509.16664v2#A2) では、本手法をさらに検証するため、事前学習済みモデルとして用いられる異なるアーキテクチャにも本手法を適用する。さらに、Appendix [C](https://arxiv.org/html/2509.16664v2#A3) では、CLIP-like [[#^ref-62|62]] モデルおよび DINOv2 [[#^ref-63|63]] のような自己教師ありアーキテクチャを用い、分布変化または目的変化を伴う更新シナリオを調査する。

下流タスクにおける互換性の結果は Tab. [2](https://arxiv.org/html/2509.16664v2#S4.T2) に報告されており、そこでは学習データセットとは異なるローカルデータセット（CUB200 または CIFAR100）の表現に対してアダプタを学習している。$\lambda$-Orthogonality 正則化を伴う変換 $B_{\lambda}$ を採用することで、本手法はローカルタスク性能とモデル互換性を向上させ、ベースラインを上回る。追加の下流データセット（Flower102 [[#^ref-64|64]] および Places365）での結果は Appendix [D](https://arxiv.org/html/2509.16664v2#A4) に示す。Tab. [1(a)](https://arxiv.org/html/2509.16664v2#S4.T1.st1) と Tab. [1(b)](https://arxiv.org/html/2509.16664v2#S4.T1.st2) から、厳密な直交変換である $B_{\perp}$ は、独立に学習されたモデル $\phi_{\text{new}}$ と比較して性能向上をもたらさないことが分かる。これに対し、$B_{\perp}$ に比べてより高い可塑性を与える $B_{\lambda}$ は、新モデルが下流タスクの性能を向上させることを可能にする。ハイパーパラメータ $\lambda$ に関するアブレーション研究は Appendix [E](https://arxiv.org/html/2509.16664v2#A5) に示し、Eq. [10](https://arxiv.org/html/2509.16664v2#S3.E10) における損失項の構成要素ごとのアブレーションは Appendix [F](https://arxiv.org/html/2509.16664v2#A6) に詳述する。

[Uncaptioned image]

![](assets/fig04.png)

### 4.5 Backfilling Results

本節では、Sec. [3.6](https://arxiv.org/html/2509.16664v2#S3.SS6) で述べた新規のバックフィル戦略を評価する。評価では、Tab. [1(a)](https://arxiv.org/html/2509.16664v2#S4.T1.st1) および Tab. [1(b)](https://arxiv.org/html/2509.16664v2#S4.T1.st2) に詳述された実験設定を考慮する。FCT には特定のバックフィル戦略が存在しないため、[[#^ref-22|22]] と同様にランダム順序を採用する。Fig. [5](https://arxiv.org/html/2509.16664v2#S4.F5) 、Tab. [2](https://arxiv.org/html/2509.16664v2#S4.T2a) 、および Tab. [3](https://arxiv.org/html/2509.16664v2#S4.T3) に示す結果は、本手法のバックフィル戦略が他のベースラインを一定の差で上回ることを示している。特に、Fig. [5](https://arxiv.org/html/2509.16664v2#S4.F5) は、ギャラリーの50%未満をバックフィルした段階で、新たに独立に学習したモデルと同等の性能を達成できることを示している。Appendix [G](https://arxiv.org/html/2509.16664v2#A7) では、主実験で用いた Mean Squared Error に代わる距離尺度を用いたアブレーション研究を提示する。

## 5 Conclusion

モデル互換性は多くの大規模検索システムにおける重要な課題であり、これが達成されない場合、システム更新の妨げとなり得る。本論文では、独立に学習された表現を統一空間へ整合させる写像変換を導入し、さらに教師ありコントラスト学習損失を通じて、より強い特徴クラスタリングも実現する。また、更新された独立モデルの整合性を損なうことなく下流タスクへの適応を助けるため、直交制約を緩和する手法も提案する。加えて、ギャラリー集合の効率的な部分バックフィルを可能にする新しいバックフィル順序戦略を提案し、ギャラリーの半分未満をバックフィルするだけで、新たに独立に学習したモデルと同等の性能を達成する。本手法は、モデルが学習された同一分布および異なる分布の双方において、従来手法を上回る性能を示す。これらの結果を位置づけるため、本手法の限界については Appendix [I](https://arxiv.org/html/2509.16664v2#A9) で詳細に検討する。さらに、その実用性を評価するため、方法論的複雑性とより広範な適用可能性を Appendix [H](https://arxiv.org/html/2509.16664v2#A8) で分析する。

## Acknowledgments

本論文は、プロジェクト「Collaborative Explainable neuro-symbolic AI for Decision Support Assistant」、CAI4DSA、CUP B13C23005640006 の支援を一部受けた。

## References

- [1] Florian Schroff, Dmitry Kalenichenko, and James Philbin. Facenet: A unified embedding for face recognition and clustering. In Proceedings of the IEEE conference on computer vision and pattern recognition , pages 815-823, 2015. ^ref-1
- [2] Weiyang Liu, Yandong Wen, Zhiding Yu, Ming Li, Bhiksha Raj, and Le Song. Sphereface: Deep hypersphere embedding for face recognition. In 2017 IEEE Conference on Computer Vision and Pattern Recognition, CVPR 2017, Honolulu, HI, USA, July 21-26, 2017 , pages 6738-6746. IEEE Computer Society, 2017. ^ref-2
- [3] Jiankang Deng, Jia Guo, Niannan Xue, and Stefanos Zafeiriou. Arcface: Additive angular margin loss for deep face recognition. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 4690-4699, 2019. ^ref-3
- [4] Relja Arandjelovic, Petr Gronat, Akihiko Torii, Tomas Pajdla, and Josef Sivic. Netvlad: Cnn architecture for weakly supervised place recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition , pages 5297-5307, 2016. ^ref-4
- [5] Bingyi Cao, Andre Araujo, and Jack Sim. Unifying deep local and global features for image search. In Computer Vision-ECCV 2020: 16th European Conference, Glasgow, UK, August 23-28, 2020, Proceedings, Part XX 16 , pages 726-743. Springer, 2020. ^ref-5
- [6] Stephen Hausler, Sourav Garg, Ming Xu, Michael Milford, and Tobias Fischer. Patch-netvlad: Multi-scale fusion of locally-global descriptors for place recognition. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition , pages 14141-14152, 2021. ^ref-6
- [7] Hyeonwoo Noh, Andre Araujo, Jack Sim, Tobias Weyand, and Bohyung Han. Large-scale image retrieval with attentive deep local features. In Proceedings of the IEEE international conference on computer vision , pages 3456-3465, 2017. ^ref-7
- [8] Fuwen Tan, Jiangbo Yuan, and Vicente Ordonez. Instance-level image retrieval using reranking transformers. In proceedings of the IEEE/CVF international conference on computer vision , pages 12105-12115, 2021. ^ref-8
- [9] Bin Yan, Yi Jiang, Jiannan Wu, Dong Wang, Ping Luo, Zehuan Yuan, and Huchuan Lu. Universal instance perception as object discovery and retrieval. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 15325-15336, 2023. ^ref-9
- [10] Colin Raffel. Building machine learning models like open source software. Commun. ACM , 66(2):38-40, jan 2023. ^ref-10
- [11] Prateek Yadav, Colin Raffel, Mohammed Muqeeth, Lucas Caccia, Haokun Liu, Tianlong Chen, Mohit Bansal, Leshem Choshen, and Alessandro Sordoni. A survey on model moerging: Recycling and routing among specialized experts for collaborative learning. Trans. Mach. Learn. Res. , 2025. ^ref-11
- [12] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971 , 2023. ^ref-12
- [13] Niccolò Biondi, Federico Pernici, Simone Ricci, and Alberto Del Bimbo. Stationary representations: Optimally approximating compatibility and implications for improved model replacements. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) , 2024. ^ref-13
- [14] Jessica Maria Echterhoff, Fartash Faghri, Raviteja Vemulapalli, Ting-Yao Hu, Chun-Liang Li, Oncel Tuzel, and Hadi Pouransari. MUSCLE: A model update strategy for compatible LLM evolution. In EMNLP (Findings) , pages 7320-7332. Association for Computational Linguistics, 2024. ^ref-14
- [15] Yantao Shen, Yuanjun Xiong, Wei Xia, and Stefano Soatto. Towards backward-compatible representation learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 6368-6377, 2020. ^ref-15
- [16] Yixuan Li, Jason Yosinski, Jeff Clune, Hod Lipson, and John Hopcroft. Convergent learning: Do different neural networks learn the same representations? In Yoshua Bengio and Yann LeCun, editors, Feature Extraction: Modern Questions and Challenges , pages 196-212. PMLR, 2015. ^ref-16
- [17] Sijie Yan, Yuanjun Xiong, Kaustav Kundu, Shuo Yang, Siqi Deng, Meng Wang, Wei Xia, and Stefano Soatto. Positive-congruent training: Towards regression-free model updates. In CVPR , pages 14299-14308. Computer Vision Foundation / IEEE, 2021. ^ref-17
- [18] Niccolo Biondi, Federico Pernici, Matteo Bruni, and Alberto Del Bimbo. Cores: Compatible representations via stationarity. IEEE Transactions on Pattern Analysis and Machine Intelligence , pages 1-16, 2023. ^ref-18
- [19] Mitchell Wortsman, Gabriel Ilharco, Samir Ya Gadre, Rebecca Roelofs, Raphael Gontijo-Lopes, Ari S Morcos, Hongseok Namkoong, Ali Farhadi, Yair Carmon, Simon Kornblith, et al. Model soups: averaging weights of multiple fine-tuned models improves accuracy without increasing inference time. In International conference on machine learning , pages 23965-23998. PMLR, 2022. ^ref-19
- [20] Binjie Zhang, Yixiao Ge, Yantao Shen, Shupeng Su, Fanzi Wu, Chun Yuan, Xuyuan Xu, Yexin Wang, and Ying Shan. Towards universal backward-compatible representation learning. In IJCAI , pages 1615-1621. ijcai.org, 2022. ^ref-20
- [21] Qiang Meng, Chixiang Zhang, Xiaoqiang Xu, and Feng Zhou. Learning compatible embeddings. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV) , pages 9939-9948, October 2021. ^ref-21
- [22] Florian Jaeckle, Fartash Faghri, Ali Farhadi, Oncel Tuzel, and Hadi Pouransari. Fastfill: Efficient compatible model update. In International Conference on Learning Representations , 2023. ^ref-22
- [23] Yifei Zhou, Zilu Li, Abhinav Shrivastava, Hengshuang Zhao, Antonio Torralba, Taipeng Tian, and Ser-Nam Lim. Btˆ 2: Backward-compatible training with basis transformation. In Proceedings of the IEEE/CVF International Conference on Computer Vision , pages 11229-11238, 2023. ^ref-23
- [24] Simone Ricci, Niccolò Biondi, Federico Pernici, and Alberto Del Bimbo. Backward-compatible aligned representations via an orthogonal transformation layer. In ECCV Workshops (17) , volume 15639 of Lecture Notes in Computer Science , pages 451-464. Springer, 2024. ^ref-24
- [25] Vivek Ramanujan, Pavan Kumar Anasosalu Vasu, Ali Farhadi, Oncel Tuzel, and Hadi Pouransari. Forward compatible training for large-scale embedding retrieval systems. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 19386-19395, 2022. ^ref-25
- [26] Charles Fefferman, Sanjoy Mitter, and Hariharan Narayanan. Testing the manifold hypothesis. Journal of the American Mathematical Society , 29(4):983-1049, 2016. ^ref-26
- [27] Minyoung Huh, Brian Cheung, Tongzhou Wang, and Phillip Isola. Position: The platonic representation hypothesis. In ICML . OpenReview.net, 2024. ^ref-27
- [28] Valentino Maiorca, Luca Moschella, Antonio Norelli, Marco Fumero, Francesco Locatello, and Emanuele Rodolà. Latent space translation via semantic alignment. Advances in Neural Information Processing Systems , 36, 2024. ^ref-28
- [29] Marco Fumero, Marco Pegoraro, Valentino Maiorca, Francesco Locatello, and Emanuele Rodolà. Latent functional maps: a spectral framework for representation alignment. In NeurIPS , 2024. ^ref-29
- [30] Luca Moschella, Valentino Maiorca, Marco Fumero, Antonio Norelli, Francesco Locatello, and Emanuele Rodolà. Relative representations enable zero-shot latent space communication. In International Conference on Learning Representations , 2023. ^ref-30
- [31] Valentino Maiorca, Luca Moschella, Marco Fumero, Francesco Locatello, and Emanuele Rodolà. Latent space translation via inverse relative projection. arXiv preprint arXiv:2406.15057 , 2024. ^ref-31
- [32] Martial Mermillod, Aurélia Bugaiska, and Patrick Bonin. The stability-plasticity dilemma: Investigating the continuum from catastrophic forgetting to age-limited learning effects, 2013. ^ref-32
- [33] Guoliang Lin, Hanlu Chu, and Hanjiang Lai. Towards better plasticity-stability trade-off in incremental learning: A simple linear connector. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 89-98, 2022. ^ref-33
- [34] Dongwan Kim and Bohyung Han. On the stability-plasticity dilemma of class-incremental learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 20196-20204, 2023. ^ref-34
- [35] Lirong Wu, Zicheng Liu, Jun Xia, Zelin Zang, Siyuan Li, and Stan Z Li. Generalized clustering and multi-manifold learning with geometric structure preservation. In Proceedings of the IEEE/CVF winter conference on applications of computer vision , pages 139-147, 2022. ^ref-35
- [36] Nitin Bansal, Xiaohan Chen, and Zhangyang Wang. Can we gain more from orthogonality regularizations in training deep networks? Advances in Neural Information Processing Systems , 31, 2018. ^ref-36
- [37] Binjie Zhang, Yixiao Ge, Yantao Shen, Yu Li, Chun Yuan, XUYUAN XU, Yexin Wang, and Ying Shan. Hot-refresh model upgrades with regression-free compatible training in image retrieval. In International Conference on Learning Representations , 2021. ^ref-37
- [38] Tan Pan, Furong Xu, Xudong Yang, Sifeng He, Chen Jiang, Qingpei Guo, Feng Qian, Xiaobo Zhang, Yuan Cheng, Lei Yang, et al. Boundary-aware backward-compatible representation via adversarial learning in image retrieval. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition , pages 15201-15210, 2023. ^ref-38
- [39] Mateusz Budnik and Yannis Avrithis. Asymmetric metric learning for knowledge transfer. In CVPR , pages 8228-8238. Computer Vision Foundation / IEEE, 2021. ^ref-39
- [40] Niccolo Biondi, Federico Pernici, Matteo Bruni, Daniele Mugnai, and Alberto Del Bimbo. Cl2r: Compatible lifelong learning representations. ACM Transactions on Multimedia Computing, Communications and Applications , 18(2s):1-22, 2023. ^ref-40
- [41] Ahmet Iscen, Jeffrey Zhang, Svetlana Lazebnik, and Cordelia Schmid. Memory-efficient incremental learning through feature adaptation. In European Conference on Computer Vision , pages 699-715. Springer, 2020. ^ref-41
- [42] Chien-Yi Wang, Ya-Liang Chang, Shang-Ta Yang, Dong Chen, and Shang-Hong Lai. Unified representation learning for cross model compatibility. In 31st British Machine Vision Conference 2020, BMVC 2020 . BMVA Press, 2020. ^ref-42
- [43] Shupeng Su, Binjie Zhang, Yixiao Ge, Xuyuan Xu, Yexin Wang, Chun Yuan, and Ying Shan. Privacy-preserving model upgrades with bidirectional compatible training in image retrieval. arXiv preprint arXiv:2204.13919 , 2022. ^ref-43
- [44] Chang Wang and Sridhar Mahadevan. Manifold alignment using procrustes analysis. In Proceedings of the 25th international conference on Machine learning , pages 1120-1127, 2008. ^ref-44
- [45] Mario Lezcano-Casado and David Martınez-Rubio. Cheap orthogonal constraints in neural networks: A simple parametrization of the orthogonal and unitary group. In International Conference on Machine Learning , pages 3794-3803. PMLR, 2019. ^ref-45
- [46] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the national academy of sciences , 114(13):3521-3526, 2017. ^ref-46
- [47] Ronald Kemker, Marc McClure, Angelina Abitino, Tyler Hayes, and Christopher Kanan. Measuring catastrophic forgetting in neural networks. In Proceedings of the AAAI conference on artificial intelligence , volume 32, 2018. ^ref-47
- [48] Mehrtash Harandi and Basura Fernando. Generalized backpropagation, etude de cas: Orthogonality. arXiv preprint arXiv:1611.05927 , 2016. ^ref-48
- [49] Mete Ozay and Takayuki Okatani. Optimization on submanifolds of convolution kernels in cnns. arXiv preprint arXiv:1610.07008 , 2016. ^ref-49
- [50] Lei Huang, Xianglong Liu, Bo Lang, Adams Yu, Yongliang Wang, and Bo Li. Orthogonal weight normalization: Solution to optimization over multiple dependent stiefel manifolds in deep neural networks. In Proceedings of the AAAI Conference on Artificial Intelligence , volume 32, 2018. ^ref-50
- [51] Milton Abramowitz and Irene A Stegun. Handbook of mathematical functions with formulas, graphs, and mathematical tables , volume 55. US Government printing office, 1968. ^ref-51
- [52] Sagar Sharma, Simone Sharma, and Anidhya Athaiya. Activation functions in neural networks. Towards Data Sci , 6(12):310-316, 2017. ^ref-52
- [53] A Iliev, Nikolay Kyurkchiev, and Svetoslav Markov. On the approximation of the step function by some sigmoid functions. Mathematics and Computers in Simulation , 133:223-234, 2017. ^ref-53
- [54] Yonglong Tian, Lijie Fan, Phillip Isola, Huiwen Chang, and Dilip Krishnan. Stablerep: Synthetic images from text-to-image models make strong visual representation learners. Advances in Neural Information Processing Systems , 36, 2024. ^ref-54
- [55] Björn Barz and Joachim Denzler. Hierarchy-based image embeddings for semantic image retrieval. In 2019 IEEE winter conference on applications of computer vision (WACV) , pages 638-647. IEEE, 2019. ^ref-55
- [56] Mikolaj Wieczorek, Barbara Rychalska, and Jacek Dabrowski. On the unreasonable effectiveness of centroids in image retrieval. In Neural Information Processing: 28th International Conference, ICONIP 2021, Sanur, Bali, Indonesia, December 8-12, 2021, Proceedings, Part IV 28 , pages 212-223. Springer, 2021. ^ref-56
- [57] Olga Russakovsky, Jia Deng, Hao Su, Jonathan Krause, Sanjeev Satheesh, Sean Ma, Zhiheng Huang, Andrej Karpathy, Aditya Khosla, Michael Bernstein, et al. Imagenet large scale visual recognition challenge. International journal of computer vision , 115(3):211-252, 2015. ^ref-57
- [58] A. Krizhevsky. Learning Multiple Layers of Features from Tiny Images. Technical report, Univ. Toronto, 2009. ^ref-58
- [59] Catherine Wah, Steve Branson, Peter Welinder, Pietro Perona, and Serge Belongie. The caltech-ucsd birds-200-2011 dataset. 2011. ^ref-59
- [60] Bolei Zhou, Agata Lapedriza, Aditya Khosla, Aude Oliva, and Antonio Torralba. Places: A 10 million image database for scene recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence , 2017. ^ref-60
- [61] Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, Jakob Uszkoreit, and Neil Houlsby. An image is worth 16x16 words: Transformers for image recognition at scale. In 9th International Conference on Learning Representations, ICLR 2021, Virtual Event, Austria, May 3-7, 2021 . OpenReview.net, 2021. ^ref-61
- [62] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In International conference on machine learning , pages 8748-8763. PmLR, 2021. ^ref-62
- [63] Maxime Oquab, Timothée Darcet, Théo Moutakanni, Huy V Vo, Marc Szafraniec, Vasil Khalidov, Pierre Fernandez, Daniel HAZIZA, Francisco Massa, Alaaeldin El-Nouby, et al. Dinov2: Learning robust visual features without supervision. Transactions on Machine Learning Research . ^ref-63
- [64] Maria-Elena Nilsback and Andrew Zisserman. Automated flower classification over a large number of classes. In 2008 Sixth Indian conference on computer vision, graphics &amp; image processing , pages 722-729. IEEE, 2008. ^ref-64
- [65] Soravit Changpinyo, Piyush Sharma, Nan Ding, and Radu Soricut. Conceptual 12m: Pushing web-scale image-text pre-training to recognize long-tail visual concepts. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition , pages 3558-3568, 2021. ^ref-65
- [66] Marco Mistretta, Alberto Baldrati, Lorenzo Agnolucci, Marco Bertini, and Andrew D. Bagdanov. Cross the gap: Exposing the intra-modal misalignment in CLIP via modality inversion. In The Thirteenth International Conference on Learning Representations, ICLR 2025, Singapore, April 24-28, 2025 . OpenReview.net, 2025. ^ref-66
- [67] Wenzhuo Liu, Fei Zhu, Longhui Wei, and Qi Tian. C-clip: Multimodal continual learning for vision-language model. In The Thirteenth International Conference on Learning Representations , 2025. ^ref-67
- [68] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. arXiv preprint arXiv:2001.08361 , 2020. ^ref-68
- [69] Preetum Nakkiran, Gal Kaplun, Yamini Bansal, Tristan Yang, Boaz Barak, and Ilya Sutskever. Deep double descent: Where bigger models and more data hurt. Journal of Statistical Mechanics: Theory and Experiment , 2021(12):124003, 2021. ^ref-69
- [70] Gabriele Prato, Simon Guiroy, Ethan Caballero, Irina Rish, and Sarath Chandar. Scaling laws for the out-of-distribution generalization of image classifiers. ICML 2021 Workshop on Uncertainty and Robustness in Deep Learning. , 2021. ^ref-70
- [71] Ethan Caballero, Kshitij Gupta, Irina Rish, and David Krueger. Broken neural scaling laws. In The Eleventh International Conference on Learning Representations , 2023.

## Appendix A Extending Classes Setting on Places365

To validate our approach further, we evaluate it using a model trained on a dataset different from ImageNet1K. Specifically, we use a ResNet-50 pretrained on Places205 (from [ViSSL](https://github.com/facebookresearch/vissl/blob/main/MODEL_ZOO.md#supervised) ) as the old model, and a ResNet-50 pretrained on Places365 (from [CSAILVision](https://github.com/CSAILVision/places365#pre-trained-cnn-models-on-places365-standard) ) as the new model. Tab. [4](https://arxiv.org/html/2509.16664v2#A1.T4) summarizes the performance of each method using the evaluation metrics defined in Sec. [4.2](https://arxiv.org/html/2509.16664v2#S4.SS2) . The results demonstrate that the new model $\phi_{\text{new}}$ is not inherently compatible with the old model, $\phi_{\text{old}}$. Moreover, the adaptation $F(\phi_{\text{old}})$ provided by FCT underperforms when compared to the new model alone. In contrast, methods that promote better clustering, such as FastFill and our proposed approach, achieve even higher performance than the standalone new model. This improvement arises from leveraging information from both the old and new models, effectively implementing a form of knowledge distillation during the learning of the forward adapter. Unlike the baselines, our method aligns all adapted representations within a unified representation space, thereby consistently maintaining compatibility with the old model.

## Appendix B Additional Architecture for Independently Pretrained Models Setting

We conduct additional experiments using a DenseNet-121 as the old model, $\phi_{\text{old}}$, and an EfficientNet-B3 as the new model, $\phi_{\text{new}}$, both pretrained on ImageNet1K and obtained from the PyTorch Hub. The results of these experiments on the ImageNet1K dataset are presented in Tab. [5](https://arxiv.org/html/2509.16664v2#A2.T5) . Our approach achieves the best performance across all metrics, outperforming the baselines in both cross-model and same-model retrieval scenarios.

## Appendix C Additional Experiments with DINOv2 and CLIP as Independently Pretrained Models

To investigate update scenarios involving data distribution or objective shifts, we conduct additional experiments using a ResNet-18 pretrained on ImageNet1K as the old model, and both a CLIP [radford2021learning](https://arxiv.org/html/2509.16664v2#bib.bib62) pretrained on CC12M [changpinyo2021conceptual](https://arxiv.org/html/2509.16664v2#bib.bib65) dataset and a DINOv2 [oquabdinov2](https://arxiv.org/html/2509.16664v2#bib.bib63) ($vit\_small\_patch14\_dinov2$) as the new models. To train both the forward and backward transformations, the ImageNet1K dataset and the same hyperparameters of Tab. [1(b)](https://arxiv.org/html/2509.16664v2#S4.T1.st2) are used. This setup represents a considerable shift in both data distribution and model objective relative to the new models. Notably, FastFill cannot be applied in this context, as both CLIP and DINOv2 lack classifiers. In Tab. [6(a)](https://arxiv.org/html/2509.16664v2#A3.T6.st1) , we report the results obtained using DINOv2 as the new, independently trained model. Our approach achieves better results than FCT, further validating its practical applicability to real-world problems.

Instead, in Tab. [6(b)](https://arxiv.org/html/2509.16664v2#A3.T6.st2) , we report the results obtained using CLIP pretrained on CC12M as the new, independently trained model. In this scenario, the pretrained CLIP model exhibits lower retrieval performance on ImageNet1K compared to ResNet-18. This is a well-known limitation of multi-modal training, where intra-modal misalignment can negatively impact the quality of single-modality representations [mistrettacross](https://arxiv.org/html/2509.16664v2#bib.bib66) . Specifically, CLIP models are optimized for cross-modal retrieval rather than single-modality retrieval tasks, in contrast to DINOv2 or ResNet-18, which are trained exclusively on a single modality. This reduction in performance of the new model relative to the old one causes FCT to degrade the overall retrieval capacity of the system, failing to achieve compatibility, as it attempts to transform the higher-quality representations of the old model into the lower-performing representations of the new model. In contrast, our method introduces an additional loss that encourages both intra-class clustering and inter-model alignment of feature representations on the specific training dataset. As a result, the forward transformation, due to its greater flexibility, improves the performance of the old model's representations. Even in this challenging scenario, our approach outperforms FCT, further validating the robustness of our method.

## Appendix D Additional Datasets for Independently Pretrained Models adapted on Downstream Task setting

We further extend our analysis of the Independently Pretrained Models Adapted on Downstream Task setting by including two additional datasets: the larger Places365 and the fine-grained Flowers102. These additions allow us to evaluate our method's effectiveness in more challenging scenarios. The results are reported in Tab. [7](https://arxiv.org/html/2509.16664v2#A4.T7) . In these experiments, the old model is a ResNet-18 and the new model is a ViT-L-16, both pretrained on ImageNet-1K. We employ an affine adapter with $\lambda=12$. On both additional datasets, our approach consistently outperforms the baseline methods. The proposed $\lambda$-Orthogonality regularization not only improves retrieval performance on the downstream tasks but also encourages the adapted new model representation, $B_{\lambda}(\phi_{\text{new}})$, to remain consistent with its original form. As a result, retrieval performance on ImageNet1K is preserved.

## Appendix E Ablation on the hyperparameter $\boldsymbol{\lambda}$

Figure 6 : Ablation on our $\lambda$-orthogonal regularization on CUB dataset. Displayed are the compatibility metrics on CUB and the zero-shot (ZS) improvement on ImageNet1K at different value of $\lambda$. Results correspond to those in Tab. 8 .

![](assets/fig05.png)

In our experiments, we select $\lambda$ to maximize adaptability to downstream tasks while preserving the pre-trained model's performance on its original training dataset, ImageNet1K. To illustrate the impact of our approach, Tab. [8](https://arxiv.org/html/2509.16664v2#A5.T8) reports the CMC-Top1 scores obtained by applying our proposed $\lambda$-orthogonal regularizer to the new pre-trained model. The results, also reported in Fig. [6](https://arxiv.org/html/2509.16664v2#A5.F6) , indicate that increasing $\lambda$ enhances the performance of the new model's representations on the downstream task.

However, this improvement comes at the expense of reduced performance on the original dataset, as evidenced by a decrease in zero-shot (ZS) scores, particularly pronounced in the absence of regularization ($\lambda=\infty$). Empirically, we find that setting $\lambda=12$ yields the best trade-off across all metrics. [bansal2018can](https://arxiv.org/html/2509.16664v2#bib.bib36) optimize a soft orthogonality constraint, equal to case where $\lambda=0$. However, this formulation does not lead to performance improvements and is outperformed by the use of a strictly orthogonal transformation. As discussed in Sec. [3.3](https://arxiv.org/html/2509.16664v2#S3.SS3) , imposing strict orthogonality may hinder the model's ability to incorporate task-specific information. In contrast, our approach relaxes this constraint by introducing a tunable hyperparameter $\lambda$ that controls the deviation of the Gram matrix from the identity, allowing greater flexibility while preserving representational consistency.

To further validate our aproach we also study the effect of a scalar weight $w$ to the loss contributions of our $\lambda$-orthogonal regularization compared with two different orthogonal regularizations: Soft Orthogonality (SO) [bansal2018can](https://arxiv.org/html/2509.16664v2#bib.bib36) -witch correspond to the spacial case of $\lambda$ =0 in our aproach- and Spectral Restricted Isometry Property (SRIP) [bansal2018can](https://arxiv.org/html/2509.16664v2#bib.bib36) . We test the regularizers across different values of scalar weight: $w=1$, $w=10^{-1}$, $w=10^{-2}$, and $w=10^{-3}$. Additionally, we include a column reporting the exact value of $\lVert W^{\top}W-I\rVert_{F}$ reached by the backward transformation $B_{\lambda}$ at the end of training, to indicate the deviation from strict orthogonality.

As shown in the Tab. [9](https://arxiv.org/html/2509.16664v2#A5.T9) , for both SRIP and SO, the final value of $\lVert W^{\top}W-I\rVert_{F}$ is governed by the optimization process and the chosen scalar weight $w$. Unlike our $\lambda$-orthogonal regularization, these approaches do not provide direct control over $\lVert W^{\top}W-I\rVert_{F}$; a smaller contribution of the regularizer to the total loss results in a diminished regularization effect on the backward transformation $B_{\lambda}$. When the scalar weight $w$ of the regularizer is reduced, the optimization process is unable to fully minimize the regularization term, particularly because competing loss components (such as MSE and the contrastive loss $L_{C}$) may favor a non-orthogonal transformation. For instance, when $w=10^{-3}$ and $w=10^{-2}$, the results obtained with SO, SRIP, and our $\lambda$-orthogonal regularization are comparable to those observed in the case of $\lambda=\infty$ (see Tab. [8](https://arxiv.org/html/2509.16664v2#A5.T8) ), where the orthogonality constraint is entirely ignored. This occurs because, at such a small value of $w$, the contribution of the regularizer becomes negligible during optimization. To avoid this issue, in our method we set $w=1$ for the $\lambda$-orthogonal regularization, thereby ensuring that the regularization term is effectively incorporated into the optimization process during the training of the backward transformation. This ensures that the regularization term achieves the target threshold $\lambda$, enabling precise control over the stability-plasticity trade-off in the backward transformation and leads to higher representation compatibility on the downstream task. As highlighted by the bold entries in the Tab. [9](https://arxiv.org/html/2509.16664v2#A5.T9) , our method produces stable results (minor fluctuations are attributable to stochastic optimization) for $w=1$ and $w=10^{-1}$ in contrast to SO and SRIP. Conversely, when $w$ is very low ($10^{-2}$ or $10^{-3}$), the regularizer cannot be fully optimized, and our method behaves similarly to SO regularization, as our introduced constrains ($\lVert W^{\top}W-I\rVert_{F}\geq\lambda$) influences the minimum of the objective, which is never reached in practice. In contrast, due to its approximate formulation and greater complexity relative to SO, SRIP exhibits an even weaker regularization effect when $w$ is low.

## Appendix F Detailed Analysis of Loss Term Contributions

In this section, we analyze the contribution of each term to the final loss (Eq. [10](https://arxiv.org/html/2509.16664v2#S3.E10) ) optimized during training. Tab. [10](https://arxiv.org/html/2509.16664v2#A6.T10) presents the results obtained when the adaptation dataset matches the dataset used to train the models from which the features were extracted, namely ImageNet1K. In this scenario, a strict orthogonal transformation $B_{\perp}$ is employed for backward-compatibility. We observe that when used independently, $\mathcal{L}_{F}$ ensures compatibility with the representations of the new model but significantly fails to achieve backward compatibility. This behavior highlights a pronounced forward bias inherent to $\mathcal{L}_{F}$. The backward alignment loss $\mathcal{L}_{B}$ alone promotes backward compatibility but degrades forward-adapted representation performance. The contrastive loss $\mathcal{L}_{C}$ alone significantly improves inter-model alignment and intra-class clustering, supporting both backward and forward compatibility. The combination $\mathcal{L}_{F}+\mathcal{L}_{B}+\mathcal{L}_{C}$ achieves the highest overall performance across compatibility scenarios, underscoring the importance of each loss component in maintaining balance between forward and backward trasformation learning.

Tab. [11](https://arxiv.org/html/2509.16664v2#A6.T11) shows the impact of these loss terms in a downstream task setting (CUB dataset), where $\phi_{old}$ is ResNet-18 and $\phi_{new}$ is ViT-L-16, using $\lambda$-Orthogonality with $\lambda=12$. Similar to Tab. [10](https://arxiv.org/html/2509.16664v2#A6.T10) , excluding the backward loss $\mathcal{L}_{B}$ still yields good forward compatibility but significantly reduces backward compatibility performance. Excluding the contrastive loss $\mathcal{L}_{C}$ substantially decreases the adaptation to the downstream task leading to lower $B_{\lambda}(\phi_{\text{new}})/B_{\lambda}(\phi_{\text{new}})$ values. Using all loss terms $\mathcal{L}_{F}+\mathcal{L}_{B}+\mathcal{L}_{C}$ consistently achieves the best or near-best results in forward and backward compatibility, demonstrating the complementary nature of these terms.

These analyses underline that each loss term contributes uniquely and significantly to achieving comprehensive and model compatibility across various tasks.

## Appendix G Distance metric for Partial Backfilling Ordering

Our proposed partial backfilling strategy is guided by a distance metric $d$, which measures the dissimilarity between each embedding vector $F(\mathbf{h}^{k})$ and its corresponding class mean $\boldsymbol{\mu}_{c}$. This section investigates the impact of different distance metrics on determining an effective ordering for backfilling images in the gallery set. We compare two distance metrics-Mean Squared Error (MSE) and Cosine Distance-for ranking images during partial backfilling. The performance of each metric is evaluated under two distinct experimental conditions: the Extending Classes setting (Tab. [11](https://arxiv.org/html/2509.16664v2#A7.T11) ) and the Independently Pretrained Models setting (Tab. [12](https://arxiv.org/html/2509.16664v2#A7.T12) ). MSE computes the Euclidean distance between feature vectors, capturing both angular and magnitude discrepancies. As shown in Tab. [11](https://arxiv.org/html/2509.16664v2#A7.T11) and Tab. [12](https://arxiv.org/html/2509.16664v2#A7.T12) , MSE generally yields robust performance, particularly in terms of CMC-Top1. In contrast, Cosine Distance measures the angular distance between normalized feature vectors, emphasizing directional similarity while ignoring magnitude. The results indicate that Cosine Distance achieves slightly better performance in terms of mAP and provides comparable CMC-Top1 scores relative to MSE.

[Uncaptioned image]

![](assets/fig06.png)

## Appendix H Method Complexity and Broader Applicability

#### Method Complexity.

Our approach requires training only two matrices, resulting in a small number of parameters to optimize. Because our method operates solely on the extracted embeddings, it does not require any knowledge of the underlying models and is therefore applicable across different objectives (see Appendix [C](https://arxiv.org/html/2509.16664v2#A3) ), architectures, and types of learned representations.

In contrast to previous methods, which either focus solely on alignment loss without any representation clustering loss (e.g., FCT [ramanujan2022forward](https://arxiv.org/html/2509.16664v2#bib.bib25) ), or require specific architectural components of the pretrained models (e.g., FastFill [jaeckle2023fastfill](https://arxiv.org/html/2509.16664v2#bib.bib22) , which requires access to the classifier of the new model), our approach addresses these limitations. Additionally, while existing baselines provide only forward adaptation, our method is designed to achieve both forward and backward compatibility, thereby addressing practical needs that prior works do not meet. For instance:

- • $B_{\perp}(\phi_{\text{new}})/F(\phi_{\text{old}})$ yields higher retrieval values compared to the baselines.
- • $B_{\perp}(\phi_{\text{new}})/\phi_{\text{old}}$ can be achieved exclusively by our method. From a practical standpoint, this allows compatibility to be established even before all gallery items are forward-adapted using $F$.
- • Since our approach provides a unified representation space, even when the gallery is in a hybrid form (i.e., with some elements already adapted by $F$ and others not), using $B_{\perp}(\phi_{\text{new}})$ still ensures compatibility. This can not be achieved neither by FCT [ramanujan2022forward](https://arxiv.org/html/2509.16664v2#bib.bib25) nor FastFill [jaeckle2023fastfill](https://arxiv.org/html/2509.16664v2#bib.bib22) .

The contrastive loss defined in Eq. [8](https://arxiv.org/html/2509.16664v2#S3.E8) relies on the availability of class labels to encourage embeddings from the same class to cluster together while pushing apart embeddings from different classes. In scenarios where class labels are not available, Eq. [8](https://arxiv.org/html/2509.16664v2#S3.E8) naturally reduces to an unsupervised contrastive loss, similar to the objective used for training CLIP models [radford2021learning](https://arxiv.org/html/2509.16664v2#bib.bib62) . In this unsupervised setting, we contrast pairs of representations originating from different models, and clustering-since it cannot be enforced directly-becomes a byproduct resulting from embedding similarity. Consequently, our approach is flexible and can be applied in both supervised and unsupervised training scenarios, depending on the availability of labels for the downstream task.

#### Broader Applicability.

As it is demonstrated in [bansal2018can](https://arxiv.org/html/2509.16664v2#bib.bib36) , soft orthogonalization has been applied to regularize all the weights of a CNN during training, and could benefit from the increased plasticity offered by our proposed $\lambda$-orthogonal regularization. While retrieval is the standard scenario for evaluating compatibility [shen2020towards](https://arxiv.org/html/2509.16664v2#bib.bib15) , our approach is broadly applicable to any task that requires representation adaptation, as it focuses on model alignment and clustering of learned representations. As demonstrated in our downstream task adaptation experiments (see Sec. [4.4](https://arxiv.org/html/2509.16664v2#S4.SS4) ), our regularization approach yields improved performance compared to a strict orthogonal constraint, making it a valuable approach in domain adaptation scenarios as well. Furthermore, enforcing geometrical consistency while allowing adaptability has recently been investigated in the context of continual learning for multimodal training [liu2025c](https://arxiv.org/html/2509.16664v2#bib.bib67) . However, the authors of [liu2025c](https://arxiv.org/html/2509.16664v2#bib.bib67) promote this property indirectly through a knowledge consolidation loss, rather than by directly applying a regularization constraint. This highlights both possible future research and the potential applicability of our $\lambda$-orthogonal regularization across various areas of representation learning.

## Appendix I Limitations

Our approach relies on the assumption that the new model's embedding space is more expressive (e.g., higher retrieval accuracy, stronger clustering) than that of the old model. If the updated model is not comparable or lower quality, due, for instance, to domain mismatch, insufficient training data, or architectural regressions, then both the forward and backward adapters may fail to improve performance or could even degrade compatibility. In many practical systems, this assumption is justified by scaling laws [kaplan2020scaling](https://arxiv.org/html/2509.16664v2#bib.bib68) ; [nakkiran2021deep](https://arxiv.org/html/2509.16664v2#bib.bib69) ; [prato2021scaling](https://arxiv.org/html/2509.16664v2#bib.bib70) ; [caballero2023broken](https://arxiv.org/html/2509.16664v2#bib.bib71) (i.e., larger models and more data generally yield better feature representations). For downstream tasks adaptation, while our $\lambda$-orthogonal regularized adapter shows strong performance and compatibility across various retrieval tasks, a manual tuning of the orthogonality threshold ($\lambda$) is needed. The trade-off between preserving the original model's geometry and allowing sufficient plasticity to adapt to new data hinges critically on the choice of $\lambda$. In practice, this hyperparameter could be selected via cross-validation or a small hyperparameter search on a held-out portion of the downstream dataset. Although we found that $\lambda=12$ provides a good balance in our experiments (Appendix [E](https://arxiv.org/html/2509.16664v2#A5) ), different downstream domains (e.g., fine-grained vs. coarse categories) and adapted representations may require different tuning of $\lambda$ to achieve optimal performance. Automating or self-tuning this parameter remains an open challenge. ^ref-71