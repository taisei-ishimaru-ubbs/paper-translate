---
title: "Closing the Modality Gap for Mixed Modality Search（日本語訳）"
tags: [paper-translation]
---

[[closing_the_modality_gap_for_mixed_modality_search|← 論文ノート]]

# Introduction

デジタル世界における情報は、text、images、video、audio、およびそれらのさまざまな組合せという複数のモダリティにまたがって存在する。従来の検索システムは主として、**homogeneous** なコーパス内での検索、すなわち text-to-text や text-to-image retrieval に焦点を当ててきた [[#^ref-26|26]][[#^ref-13|13]][[#^ref-15|15]][[#^ref-25|25]] が、現実の応用では、**heterogeneous** なモダリティを横断して関連コンテンツを検索・取得する能力、すなわち text-to-{text, image, or both} retrieval がますます求められている [[#^ref-29|29]]。たとえば、ユーザが "Mountain Fuji" を検索する場合、その山を説明する text 文書、単独の images、ならびに両モダリティを組み合わせた multimodal webpages のすべてを見つけられることを期待するであろう（Figure [\[fig:pull\]](#fig:pull)a）。

この実用的重要性にもかかわらず、**mixed modality search** の課題は依然として十分に研究されていない [[#^ref-29|29]]。中心的な課題は、画像と "Mountain Fuji" の textual description のように、モダリティをまたいで意味的に類似する内容を近接した位置に写像できる、統一された embedding space を構築することにある。これにより、クエリと文書のモダリティに依存せず、意味的類似度を正確に測定できる。近年の multimodal contrastive learning、特に CLIP-based models [[#^ref-25|25]][[#^ref-33|33]][[#^ref-34|34]] の進展は、大規模な paired image-text datasets での学習を通じて text と image の embeddings を整列させることにより、有望な解決策を与える。

本研究では、これらの contrastive models が現実的な mixed modality search シナリオでどの程度機能するかを検討する。具体的には、CLIP は vision と language のための 2 つの独立した encoder から構成される [[#^ref-25|25]]。各 corpus item については、image-only および text-only documents をそれぞれの encoder で encode する。image と text の両方を含む multimodal documents については、それらを表現するために image と text の embeddings の線形結合を計算する（Figure [\[fig:pull\]](#fig:pull)b）。embedding が得られた後は、query embedding と各 corpus item の cosine similarity を計算して similarity search を行い、relevance に基づく上位10件の結果の品質を測る NDCG@10 [[#^ref-11|11]] などの標準的な retrieval metrics を用いて性能を評価する。

我々の分析は、CLIP-style contrastive models の根本的な限界を明らかにする。すなわち、それらの embedding space には顕著な **modality gap** [[mind_the_gap_understanding_the_modality_gap_in_multi_modal_contrastive_representation_learning|17]][[#^ref-35|35]][[#^ref-36|36]] が存在し、mixed modality 設定における retrieval performance を大きく低下させる。これらのモデルは image-text pairs を整列させるように学習されているにもかかわらず、image と text の embeddings は separate clusters を形成し、embedding space 上で依然として大きく離れている（Figure [\[fig:pull\]](#fig:pull)c）。この clustering は強い *intra-modal ranking bias*（§3）を引き起こし、同一モダリティ間の類似度（たとえば image-to-image や text-to-text）が異なるモダリティ間の類似度（たとえば image-to-text）よりはるかに高くなり、retrieval rankings を歪める（Figure [\[fig:pull\]](#fig:pull)d）。たとえば、text query "Mountain Fuji" が与えられた場合、Mountain Fuji を描写した image は、"this is a great paper." のような無関係な text snippet よりも下位にランク付けされてしまう。さらに、modality gap は *inter-modal fusion*（§4）を損なう。すなわち、image と text の embeddings を linear interpolation により結合すると、しばしば features が最適でない領域へ押しやられ、意味表現が弱まり、image あるいは text のみを用いる場合よりも性能が低下する。

![](assets/fig01.png)

**Overview of mixed modality search.** **(a) Problem Formulation:** Mixed modality search aims to retrieve relevant information from a heterogeneous corpus containing multimodal documents. This is achieved by embedding both the query and documents, followed by similarity-based retrieval. **(b) Embedding Method:** Unimodal documents are embedded using CLIP's modality-specific encoder, while multimodal documents are embedded via a weighted fusion of image and text features. **(c) Modality Gap:** CLIP's embedding space exhibits a modality gap: embeddings form distinct clusters for each modality and remain largely separated across modalities. **(d) Cosine Similarity Across Modalities:** Due to this modality gap, documents that share the same modality as the query tend to have higher cosine similarity scores and are ranked higher, introducing systematic ranking bias. **(e) Performance on MixBench:** On our newly created MixBench benchmark---specifically designed for the task of mixed modality search---GR-CLIP, a lightweight post-hoc calibration method that closes the modality gap, significantly improves performance and outperforms the state-of-the-art VLM2Vec  [[#^ref-12|12]] baseline with substantially lower computational cost.

modality gap に起因する ranking bias と fusion failure に対処するため，我々は **GR-CLIP** を導入する。これは CLIP の embedding space から modality gap を除去する軽量な post-hoc calibration method である（GR は gap-removed を表す）。先行研究 [[#^ref-35|35]][[#^ref-36|36]] は、CLIP-like models における modality gap が、image と text の embedding subspace に直交する定数ベクトルによって近似できることを示している。この理論に基づき，我々はすべての image および text データの mean embeddings を計算し，その差分を用いて modality gap を推定し，retrieval を行う前にこのベクトルを全 embeddings から減算する。この方法は mean embeddings を計算するためにデータセットを 1 回走査するだけでよく，計算オーバーヘッドは無視できるほど小さい。

mixed modality search のために明示的に設計された 4 つの subset（Google-WIT [[#^ref-27|27]], MSCOCO [[#^ref-18|18]], OVEN [[#^ref-10|10]], VisualNews [[#^ref-19|19]]）から成る **MixBench** で評価したところ，GR-CLIP は元の CLIP models を一貫して上回り，NDCG@10 において最大 26 percentage points の改善を達成した。また，最新の vision-language generative embedding methods である VLM2Vec [[#^ref-12|12]] を 4 percentage points 上回り，かつ計算コストを 75$\times$ 削減した。さらに，本手法が異なる CLIP variants（たとえば OpenAI CLIP [[#^ref-25|25]], OpenCLIP [[#^ref-33|33]], SigLIP [[#^ref-34|34]]）およびモダリティ（たとえば text-to-image, text-to-audio, text-to-video）にまたがって汎化することも示す。

要するに，我々は、ユーザが多様なモダリティ型を含む heterogeneous corpus を検索する web search engines のような現実世界のシナリオを反映する **mixed modality search** の問題を定式化し，検討する。最先端の contrastive models が modality gap に起因して ranking bias と fusion failure に苦しむことを示し，これに対処する軽量な post-hoc calibration method を提案する。我々の知見は，有効な mixed modality search のためには，真に統一された embedding space を構築することが重要であることを強調している。

# Preliminaries 

本節では，mixed modality search タスクを定義し，その課題および課題に関連する 3 つの設定を導入し，さらに用いる手法と評価指標を説明する。

## Problem Formulation

Mixed modality search は，クエリと文書の双方が text，image，audio，video など異なるモダリティの組合せから構成され得るときに，意味的に関連するコンテンツを検索することを目的とする。$\mathcal{M}$ をサポートされるモダリティの集合（たとえば，$\mathcal{M} = \{\text{text}, \text{image}, \text{audio}, \text{video}\}$）とする。クエリは $q$ で表し，そのモダリティ集合を $m_q \subseteq \mathcal{M}$ とする。retrieval corpus は $\mathcal{C} = \{d_i\}_{i=1}^N$ と定義され，各文書 $d_i$ はモダリティ集合 $m_i \subseteq \mathcal{M}$ を伴う。目的は，各文書に対する similarity score $s(q, d_i)$ を計算し，クエリと文書の間でモダリティがどのように分布していても，意味的関連性に基づいて ranked list を返すことである。

mixed modality search は従来の retrieval task と比べて 2 つの性質によって特徴づけられる。**1) heterogeneous corpus:** 文書ごとにモダリティ構成が異なる，すなわち $d_i, d_j \in \mathcal{C}$ であって $m_i \ne m_j$ を満たすものが存在する。たとえば，一つの文書は text-only（$m_i = \{\text{text}\}$），別の文書は image-only（$m_j = \{\text{image}\}$），さらに別の文書は multimodal（$m_k = \{\text{text}, \text{image}\}$）であり得る。**b) multimodal documents:** 一部の文書は 1 つのエントリ内に複数のモダリティを含み，すなわち $|m_i| > 1$ である。これらのモダリティはしばしば相補的な情報を提供し，効果的な理解のためには統合する必要がある（たとえば，説明的な caption を伴う image）。

## Settings

heterogeneous corpus と multimodal documents の組合せは，2 つの中心的な modeling challenge を生み出す。**1) cross-modal alignment:** たとえば "Mount Fuji" の text と image が representation space 内で近接した位置に埋め込まれるように，異なるモダリティ間で類似した概念の表現を比較可能に保つこと。**2) multimodal fusion:** たとえば "Mount Fuji" の text と image を統合して，その概念のより豊かな表現を生成するように，文書内の複数モダリティを効果的に結合し，統一された意味的に妥当な表現を形成すること。これらの課題を体系的に調べるため，以下の 3 つの設定を定義する。

**Ablated setting 1: only heterogeneous corpus (§3).** 各文書は unimodal（$|m_i| = 1$）であるが，コーパスは複数のモダリティにまたがる（$|\mathcal{M}| > 1$）。たとえば，Figure [\[fig:pull\]](#fig:pull)a の $d_1$ と $d_2$ に対応するように，同一概念の text-only および image-only の記述を含み得る。これは cross-modal alignment のみを検証する設定であり，モデルがモダリティ間で比較可能な表現を符号化できるかを問う。

**Ablated setting 2: only multimodal documents (§4).** すべての文書が同一のモダリティ集合を含む（$m_i = \mathcal{M}$ かつ $|m_i| > 1$）。たとえば，Figure [\[fig:pull\]](#fig:pull)a の $d_3$ に対応するように，各文書は image とそれに対応する caption の両方を含む。この設定は純粋に multimodal fusion に焦点を当て，モデルが複数モダリティを効果的に結合できるかを評価する。

**Full setting: mixed modality search (§5).** 文書は unimodal または multimodal のいずれでもあり得（$|m_i| \ge 1$），かつコーパスは heterogeneous である。たとえば，一部の文書は text-only，別の文書は image-only，さらに別の文書はそれらの組合せであり，Figure [\[fig:pull\]](#fig:pull)a の $d_1$，$d_2$，$d_3$ がすべて存在する状況に対応する。これは最も現実的かつ一般的な設定であり，ニュース記事，商品リスト，科学データセットのような実世界のコーパスを反映している。これは 2 つの核心的課題を統合し，我々の主要な評価シナリオとなる。

## Methods 

クエリ $q$ と文書 $d_i$ が与えられたとき，我々は embedding model $f$ を用いてそれらの embeddings $e_q = f(q)$ および $e_i = f(d_i)$ を計算し，cosine similarity により文書を順位付けする：$s(q, d_i) = \frac{e_q \cdot e_i}{\|e_q\| \cdot \|e_i\|}$。以下の embedding approaches を評価する。

**CLIP (baseline) [[#^ref-25|25]].** CLIP は，paired image-text inputs を整列させるよう学習された contrastive vision-language model である。image encoder $f^I$ と text encoder $f^T$ を用いて，各モダリティを別々に符号化する。unimodal な text または image documents $d_i$ および $d_j$ については，モダリティ固有の encoder を用いて embedding を計算する：$e_i = f^I(d_i)$ および $e_j = f^T(d_j)$。image と text の入力 $d_k^I$ および $d_k^T$ を含む multimodal documents $d_k$ については，weighted interpolation を計算する：$e_k = \alpha \cdot f^T(d_k^T) + (1 - \alpha) \cdot f^I(d_k^I)$，ここで $\alpha \in [0, 1]$ は各モダリティの寄与を調整する。

**VLM2Vec (baseline) [[#^ref-12|12]].** VLM2Vecは、最先端のマルチモーダル生成埋め込み手法であり、大規模視覚言語モデル$f$（たとえばLLaVA [[#^ref-21|21]]、Qwen-VL [[#^ref-1|1]]）を自己回帰的に適応させて文書埋め込みを生成する。各文書$d_i$は、テキスト入力と画像入力を組み合わせた指示形式プロンプト$p_i$（たとえば*"Generate the embedding for the document: \[image tokens\] \[text tokens\]"*）として整形され、その後、自己回帰的に処理される。最終デコーダ層から得られるプール表現を埋め込みとして用い、$e_i = f(p_i)$と定義する。本手法は、二つのモダリティの共同モデリングとインストラクション・チューニングを通じて、高次の意味的整合を捉える。

**GR-CLIP (ours).** CLIPはモダリティ間整合を目的としているにもかかわらず、先行研究は、その埋め込み空間に持続的なモダリティギャップが存在することを示している。すなわち、画像埋め込みとテキスト埋め込みは別々のクラスターを形成し、互いに離れたままである [[mind_the_gap_understanding_the_modality_gap_in_multi_modal_contrastive_representation_learning|17]]。対応する画像・テキストの埋め込み$e_i^T$と$e_i^I$が与えられたとき、その関係は$e_i^T - e_i^I \approx c_\perp$とモデル化できる。ここで$c_\perp$は共有埋め込み部分空間に直交する定数ベクトルであり、モダリティギャップを表す [[#^ref-36|36]]。GR-CLIP（GRはgap-removedの略）は、このギャップをモダリティ固有の平均を差し引くことで除去する軽量な事後較正手法である：$e_i^{\prime T} = e_i^T - \mathbb{E}_i[e_i^T], e_i^{\prime I} = e_i^I - \mathbb{E}_i[e_i^I]$。このゼロ中心化によりモダリティギャップは消失する [[#^ref-36|36]]。なぜなら、$e_i^{\prime T} - e_i^{\prime I} = (e_i^T - e_i^I) - (\mathbb{E}_i[e_i^T] - \mathbb{E}_i[e_i^I]) \approx c_\perp - c_\perp = 0$となり、推論コストをほとんど増やさずにクロスモーダル整合が改善されるからである。マルチモーダル文書に対しては、較正後の埋め込みに同じ補間を適用する。Figure [\[fig:setting1\]](#fig:setting1)bはこの過程を示している。実際には、この単純な較正によってCLIPの性能が大幅に向上し、計算量を大きく削減しながらVLM2Vecをも上回ることが分かった。

## Evaluation Metrics

我々は、検索性能を**NDCG@10**（Normalized Discounted Cumulative Gain [[#^ref-11|11]]）を用いて評価する。これは、上位10件の検索文書の関連性と順位の双方を反映する広く用いられている指標である。NDCG@10が高いほど性能が良いことを意味する。詳細はAppendixに示す。

# Retrieval with Heterogeneous Corpus 

![](assets/fig02.png)

**異種コーパスにおける検索。** **(a) Dataset Construction:** テキスト文書を、そのテキストのスクリーンショット表現または対応する画像で確率$p$によりランダムに置換することで、異種コーパスを構築する。意味内容は不変であるため、完全なクロスモーダル整合を備えた検索システムであれば、$p$に依存せず同一の性能を維持すべきである。**(b) Initial Results & Simulation:** 驚くべきことに、CLIPはテキストがスクリーンショットに置換されるにつれてU字型の性能曲線を示す。この挙動は、CLIPの埋め込み空間におけるモダリティギャップに起因すると考えられる。クロスモーダル文書に人工的なペナルティを課すシミュレーション実験は同じU字型傾向を再現し、この仮説を確認する。**(c) Method --- GR-CLIP:** 先行研究に基づき、我々は**GR-CLIP**を提案する。これは、テキストおよび画像埋め込みの平均中心化によりモダリティギャップを除去する、単純な事後較正である。**(d) Improved Results:** GR-CLIPはU字型曲線を平坦化し、検索精度を大幅に改善し、はるかに少ない計算量でVLM2Vecベースラインに匹敵またはそれ以上の性能を達成する。**(e) Generalization Across Models, Datasets, and Modalities:** 一般化性能を評価するため、GR-CLIPを3種類のCLIP変種、3つの追加データセット、および3つの他モダリティに対して検証する（詳細はAppendix参照）。すべての場合において、所見と改善は一貫して成立する。

§2で議論したように、我々はまず、混合モダリティ検索というアブレーション設定から出発する。すなわち、単一モダリティ文書（たとえばテキストのみ、あるいは画像のみ；Figure [\[fig:setting1\]](#fig:setting1)a参照）から構成される異種コーパスである。この設定は、検索モデルがクロスモーダル整合の課題を効果的に扱えるかを評価する。

## Dataset Construction 

既存データセットの中にこの設定に従うものはないため、我々はこのタスクに特化した新規データセットを、合成スクリーンショットに基づく手法と画像置換に基づく手法という相補的な2つの戦略で構築する。

**Screenshot replacement.** クエリとコーパス文書の双方がテキストである標準的なテキスト検索データセットから出発し、テキスト文書を画像ベースのスクリーンショットとして合成的にレンダリングする。具体的には、各テキスト文書$d_i^T$について、同一内容を含むスクリーンショット版$d_i^I$を生成し、確率$p$でそれに置換する（Figure [\[fig:setting1\]](#fig:setting1)a）。この合成設定は意味内容を厳密に保存するため、制御された実験に理想的である。完全なクロスモーダル整合を持つモデルであれば、対応するテキスト文書とスクリーンショット文書を埋め込み空間で同様に表現できるはずであり、したがって$p$の値が変化しても検索性能は不変であるべきである。我々はこの変換を2つのデータセット、NFCorpus [[#^ref-3|3]]とSciFact  [[#^ref-30|30]]に適用する。

**Real image replacement.** 画像・キャプション対を含むデータセットに対しては、テキストキャプション$d_i^T$を対応する画像$d_i^I$で確率$p$により置換する。この設定はより現実的である一方、モダリティ間にわずかな意味差を導入する。それでも、基礎にある意味的整合を踏まえれば、検索性能は異なる置換比率$p$の下でも安定していると期待される。我々はこの手法を用いて2つのデータセット、Google WIT [[#^ref-27|27]]、MSCOCO [[#^ref-18|18]]を構築する。

## Initial Results & Simulation

我々はまず、意味内容が厳密に保存されるため、合成スクリーンショットに基づく設定に注目する。理想的には、完全なクロスモーダル整合を持つモデルであれば、スクリーンショットに置換された文書数にかかわらず一貫した検索性能を示すはずである。

**Models exhibit a U-shaped performance curve when mixing texts and screenshots.** 驚くべきことに、期待された平坦な傾向ではなく、U字型の性能曲線が観測された（Figure [\[fig:setting1\]](#fig:setting1)b）。スクリーンショットがテキスト文書を置換する割合が増えるにつれて（$p$の増加）、性能は当初低下する。すなわち、$p=0$（すべてテキスト）で0.22から、$p=0.99$（99%がスクリーンショット）で0.02まで落ち込む。しかし、$p=1$（すべてスクリーンショット）では性能が再び0.36へと改善し、$p$の関数として明瞭なU字型を形成する。興味深いことに、CLIPはテキストから画像への検索（$p=1$）において、テキストからテキストへの検索（$p=0$）よりも高い性能を示す。これは、おそらくその学習目的がクロスモーダル対照損失であり、単一モダリティ検索の明示的最適化を伴わないためである。

**The U-shape arises from the modality gap.** 我々は、このU字型性能をモダリティギャップに起因すると考える。第一に、モダリティギャップはモダリティ内類似度の偏りを生む。CLIPは共有空間でテキスト埋め込みと画像埋め込みを整合させる一方で、テキストと画像のクラスターは依然として分離したままである（Figure [\[fig:pull\]](#fig:pull)c）。その結果、モダリティ内類似度スコアが体系的に高くなる（Figure [\[fig:pull\]](#fig:pull)d）。第二に、この偏りが順位の歪みを引き起こす。スクリーンショットがより多くのテキスト項目を置換するにつれ、関連するスクリーンショットは低いクロスモーダル類似度のために不利に扱われ、一方で無関係なテキスト文書は、単にモダリティ内整合を持つという理由だけでより高く順位付けされうる。$p=0.99$では、残存するわずかなテキスト文書が、関連性にかかわらず順位を支配する。$p=1$では、すべての文書が画像となりモダリティバイアスが消失するため、性能が改善する。したがってU字型曲線が生じる。

**Push-down simulation confirms the hypothesis.** この説明を検証するため、我々はすべてのスクリーンショットに固定類似度0を割り当てることで、モダリティ起因の順位バイアスをシミュレートし、スクリーンショットをランキングの最下位へ押し下げる。得られた性能曲線（Figure [\[fig:setting1\]](#fig:setting1)b）は実際のCLIP曲線と極めてよく一致し、U字型がモダリティギャップに起因する順位歪みから生じるという仮説を裏づける。

## GR-CLIP with Improved Results

モダリティギャップが性能低下を引き起こす以上、我々はこのギャップを緩和して性能を改善する。

**Closing the modality gap via mean-shift calibration.** 埋め込み空間における平均シフトとしてモダリティギャップを特徴づけた先行研究 [[#^ref-36|36]]に従い、我々はGR-CLIPという軽量な事後較正手法を提案する。テキストおよび画像モダリティの平均埋め込みを計算し、それぞれの表現から差し引くことで、共有空間において両モダリティを中心化する。これにより、モダリティ間の分離が低減される（Figure [\[fig:setting1\]](#fig:setting1)d；導出は§2参照）。

**Flattened curves and improved performance after removing the modality gap.** GR-CLIPを適用すると、検索性能は大幅に向上し、異なる$p$値にわたってU字型曲線は平坦化される（Figure [\[fig:setting1\]](#fig:setting1)e）。GR-CLIPはまた、最近の生成埋め込み手法であるVLM2Vec [[#^ref-12|12]]を上回る。VLM2Vecは同程度に平坦な性能を達成するが、75$\times$多くの計算資源を要する。これらの結果は、モダリティギャップの低減が、混合モダリティ検索設定におけるCLIPベースモデルの性能向上に対して、効率的かつ有効であることを示している。

## Generalization across Models, Datasets, and Modalities

我々の所見の一般性を評価するため、GR-CLIPを異なるモデル、データセット、モダリティにわたって検証する。**1) Across models:** Figure [\[fig:setting1\]](#fig:setting1)f（上段）に示すように、U字型曲線は3種類のCLIP変種、すなわちOpenAI CLIP [[#^ref-25|25]]、OpenCLIP [[#^ref-33|33]]、SigLIP [[#^ref-34|34]]にわたって観測される。GR-CLIPは一貫して曲線を平坦化し、性能を改善する。**2) Across datasets:** Figure [\[fig:setting1\]](#fig:setting1)f（中段）に示すように、我々の所見は合成スクリーンショット設定（NFCorpus [[#^ref-3|3]]およびSciFact [[#^ref-30|30]]）を超えて、実世界データセット（Google WIT [[#^ref-27|27]]およびMSCOCO [[#^ref-18|18]]）にも拡張される。**3) Across modalities.** 我々はさらに、テキストから動画、テキストから音声への検索への一般化も検証する。結果はAppendixに示す。

# Retrieval with Multimodal Documents 

![](assets/fig03.png)

**マルチモーダル文書における検索。** **(a) Dataset Construction:** 各文書は画像とテキストの両方を含み、埋め込みはモダリティ固有特徴の融合によって得られる。モデルがマルチモーダル情報を統合する能力を評価するため、融合係数$\alpha$を変化させる。**(b) Results:** GR-CLIPは3つのモデル変種と4つのデータセットにわたって一貫してCLIPを上回り、モダリティギャップが効果的なマルチモーダル融合を妨げていること、そしてそれを除去することで検索性能が大幅に向上することを示している。

ここでは§3とは補完的なアブレーションを考える。すなわち、検索コーパスは一様であるが、各文書は画像とテキストの両方のモダリティを含むマルチモーダル文書である（Figure [\[fig:setting2\]](#fig:setting2)a）。この設定は、画像とテキストがいずれか単独よりも豊かな意味的手掛かりを提供しうる状況において、モデルがマルチモーダル情報を融合する能力を評価する。

## Dataset Construction

我々は、各文書が画像成分とテキスト成分の両方を含む、4つの実世界のマルチモーダルデータセットを用いる。**OVEN** [[#^ref-10|10]] は、クエリからマルチモーダル文書への形式を採用した既存の検索ベンチマークである。**MSCOCO** [[#^ref-18|18]] と **VisualNews** [[#^ref-19|19]] では、各画像が1つ以上の短いキャプションと対応付けられている。我々は短いキャプションのうち1つをクエリとしてランダムにサンプリングし、画像と短いキャプションを条件としてGPTを用いて長いキャプションを生成し、それを文書として構成する。**Google WIT** [[#^ref-27|27]] では、各画像にタイトル、短いキャプション、長いキャプションが付与されている。我々はタイトルと短いキャプションの連結をクエリとし、画像と長いキャプションを組み合わせたものを文書とする。これらのデータセットは、自然に対応づけられた画像・テキストデータを含む多様なドメインにまたがっている。各文書は視覚的信号とテキスト的信号を相補的に提供するため、モダリティ融合の評価に適している。

## Results

モダリティギャップがモダリティ融合に与える影響を分析するため、融合重み $\alpha \in [0, 1]$ を変化させる。これは、融合埋め込みに対する各モダリティの寄与を制御するものであり、$e_i = \alpha \cdot e_i^T + (1 - \alpha) \cdot e_i^I$ で与えられる。

**モダリティギャップは有効な融合を妨げる。** Figure [\[fig:setting2\]](#fig:setting2)b の青い曲線に示すように、元のCLIP埋め込みでは、性能は通常どちらか一方の単モダリティ端点（$\alpha = 0$ または $\alpha = 1$）で最大となり、中間の $\alpha$ による融合はこれらの単モダリティベースラインを上回れない。これは、モダリティギャップがモダリティ間の有効な統合を妨げていることを示唆する。線形補間はしばしば融合特徴を埋め込み空間内の準最適領域へ押し込み、意味的品質を低下させ、その結果、画像のみまたはテキストのみを用いる場合よりも性能が悪化する。

**モダリティギャップを閉じた後、融合は大幅に改善する。** 一度モダリティギャップが除去されると（§3で述べた平均シフト較正による）、融合は著しく効果的になる。Figure [\[fig:setting2\]](#fig:setting2)b の橙色の曲線に示すように、性能は中間の $\alpha$ で最大となり、両方の単モダリティベースラインを上回る。これは、ギャップを除去したモデルであるGR-CLIPが、画像とテキストの相補的情報をうまく統合し、より強力な全体表現を獲得していることを示す。

**モデルおよびデータセットをまたぐ一般化。** これらの結果は、OpenAI CLIP [[#^ref-25|25]]、OpenCLIP [[#^ref-33|33]]、SigLIP [[#^ref-34|34]] を含む複数のCLIP変種、および OVEN [[#^ref-10|10]]、VisualNews [[#^ref-19|19]]、Google WIT [[#^ref-27|27]]、MSCOCO [[#^ref-18|18]] といった様々なデータセットにわたって一貫して成り立つ。いずれの場合も、モダリティギャップを除去することで融合品質が向上し、検索性能が改善される。

# Mixed Modality Search 

![](assets/fig04.png)

**Mixed modality search.** **(a) Dataset Construction:** 我々は、コーパスが異種でありマルチモーダル文書を含むベンチマークである **MixBench** を導入する。これは検索エンジンにとって最も現実的な設定を反映している。**(b) Results:** 4つのMixBenchサブセットと5つのCLIP変種において、GR-CLIPはモダリティギャップを除去することで元のCLIPモデルに対して大幅な改善をもたらし、計算コストを大きく抑えつつ最先端性能を達成する。

ここでは、§3と§4の知見を統合し、最も現実的なシナリオである mixed modality search へ分析を拡張する。すなわち、コーパス中の文書が純粋なテキスト、純粋な画像、あるいはその両方の組合せでありうる設定である（Figure [\[fig:setting3\]](#fig:setting3)a）。この設定は、検索システムが異種かつ可変的にマルチモーダルなコンテンツ全体に対して動作しなければならない、現実の検索エンジンの課題を反映している。

## MixBench: Dataset Construction 

この現実的な設定における研究を支援するため、我々は mixed modality search に特化して設計した新しいベンチマーク **MixBench** を導入する。MixBench は、4つの実世界マルチモーダルデータセット---**OVEN** [[#^ref-10|10]]、**MSCOCO** [[#^ref-18|18]]、**Google WIT** [[#^ref-27|27]]、**VisualNews** [[#^ref-19|19]]---から構築されており、これらは多様なドメインにまたがり、自然に対応づけられた画像・テキスト内容を含む。これらのデータセットをクエリ・文書検索形式へ変換する手順は§4で詳述する。MixBenchでは、文書は画像のみ、テキストのみ、または画像・テキスト対から構成されうる。分布の均衡を確保するため、文書タイプ（純画像、純テキスト、マルチモーダル）を1:1:1の比率でサンプリングする。

## Results

Figure [\[fig:setting3\]](#fig:setting3)b は、元のCLIP変種とギャップ除去後の対応モデル（GR-CLIP）の両方を用いた、4つのMixBenchサブセットでの結果を示す。

**GR-CLIPはモダリティギャップ除去後に元のCLIPを大幅に上回る。** 先の知見と整合的に、平均シフト較正によってモダリティギャップを閉じると、CLIP [[#^ref-25|25]]、OpenCLIP [[#^ref-33|33]]、SigLIP [[#^ref-34|34]] を含む、試験したすべてのモデルにおいてMixBench上で有意な性能向上が得られる。これらの改善は、OVEN [[#^ref-10|10]]、VisualNews [[#^ref-19|19]]、Google WIT [[#^ref-27|27]]、MSCOCO [[#^ref-18|18]] の4データセット全体に一般化する。平均すると、GR-CLIPは追加の計算コストをほとんど伴わずに、NDCG@10 を最大26ポイント向上させる。これらの改善は、§3および§4で示した、クロスモーダル整合とマルチモーダル融合の改善によってもたらされており、これらは mixed modality retrieval における性能にとって不可欠である。

**GR-CLIPは大幅に少ない計算量で最先端性能を達成する。** 特筆すべきことに、GR-CLIPは、計算資源を75$\times$少なく用いながらも、強力なベースラインであるVLM2Vecを上回る。ただし、論文で報告されている通り、VLM2Vecが学習されたMSCOCOは例外である。これらの結果は、mixed modality search において真に共有された埋め込み空間を構築することの重要性を強調している。この能力は効果的な検索システムに不可欠である一方、見過ごされがちである。

# Related Work

**単モダリティおよびクロスモーダル検索。** 単モダリティ検索（例えば、テキスト対テキスト、画像対画像）およびクロスモーダル検索（例えば、テキスト対画像、画像対テキスト）は、先行研究において広く研究されてきた [[#^ref-26|26]][[#^ref-13|13]][[#^ref-14|14]][[#^ref-15|15]][[#^ref-25|25]]。そして現在では、GoogleやBingのような大規模検索エンジンの多くを支えている。これらの設定における核心的課題は、クエリと文書の間で正確な類似度比較を可能にする、有効な表現空間を構築することである。これに対し、本研究では、クエリと文書の双方が複数モダリティにまたがりうる、より複雑な mixed modality retrieval 設定に焦点を当てる [[#^ref-29|29]]。この設定は十分に探究されていないが、非常に実用的である。そこでは、モダリティ境界をまたいで意味的類似性を有意に測定できる共有表現空間の設計という新たな課題が生じる。

**マルチモーダル表現学習。** マルチモーダル表現学習は、異なるモダリティの情報を一貫した埋め込み空間へ統合することを長らく目指してきた。初期の研究では、early fusion と late fusion の手法が探究されてきた [[#^ref-24|24]][[#^ref-28|28]][[#^ref-16|16]][[#^ref-22|22]][[#^ref-5|5]]。近年では、対照学習に基づいて画像・テキスト対の表現を整合させるマルチモーダル対照学習が強力な枠組みとして台頭している [[#^ref-9|9]][[#^ref-25|25]][[#^ref-34|34]][[#^ref-33|33]]。CLIP [[#^ref-25|25]] のようなモデルは、数百万の対になった例で学習され、モダリティ間で意味的に整合した埋め込みを学習する顕著な能力を示してきた。さらに最近では、生成的 vision-language model（VLMs）を検索に適用する研究への関心が高まっている [[#^ref-12|12]][[#^ref-7|7]]。これは、それらを埋め込みモデルとして再利用することによって実現される [[#^ref-2|2]][[#^ref-23|23]]。これらのモデルはより柔軟で、多様なマルチモーダル入力を扱う能力を持つが、しばしば大幅に多くの計算を要する。本研究では、CLIP [[#^ref-25|25]] と VLM2Vec [[#^ref-12|12]] の両パラダイムを mixed modality retrieval 設定の下で評価する。驚くべきことに、我々は、CLIP に適用した単純な較正法が、はるかに少ない計算量でVLM2Vecを上回りうることを見出す。

**マルチモーダル対照学習におけるモダリティギャップ。** 近年の研究 [[mind_the_gap_understanding_the_modality_gap_in_multi_modal_contrastive_representation_learning|17]][[#^ref-36|36]][[#^ref-35|35]] は、対照的マルチモーダル埋め込み空間に持続的なモダリティギャップが存在することを明らかにした。すなわち、対照学習が画像とテキストを整合させるよう設計されているにもかかわらず、画像埋め込みとテキスト埋め込みは分離してクラスタリングする傾向がある。このギャップは、モデル初期化と対照最適化の組合せに起因するとされている。理論的には、モダリティギャップは、画像およびテキストの両部分空間にほぼ直交する定数オフセットベクトルとして特徴づけられてきた [[#^ref-36|36]][[#^ref-35|35]]。この知見に基づき、我々は単純だが効果的な平均減算較正を採用する。これは、類似度を計算する前に埋め込みからモダリティ特有の平均を除去するものである。この軽量な事後処理はモダリティギャップを除去し、mixed modality search 設定において大きな性能向上をもたらす。

# Conclusion

本研究は、現実的である一方で十分に探究されていない mixed modality search の問題に取り組んだ。ここでは、クエリが、マルチモーダル文書を含む異種コーパスから意味的に関連するコンテンツを検索しなければならない。我々はこの設定におけるCLIPベースモデルの挙動を分析し、重要な制約を特定した。すなわち、埋め込み空間におけるモダリティギャップが、クロスモーダル整合とマルチモーダル融合の双方を妨げるのである。これに対処するため、我々はモダリティギャップを除去し、検索性能を大幅に改善する、単純でありながら効果的な手法である **GR-CLIP** を導入した。我々の結果は、信頼性が高く効率的な mixed modality search のためには、真に統一されたマルチモーダル表現が重要であることを示している。

# Acknowledgments 

本研究の一部は Hoffman-Yee Research Grants により支援された。S.Y. は Chan Zuckerberg Biohub --- San Francisco Investigator である。

# Limitations 

本研究は、モダリティギャップの除去により、GR-CLIP が多様なデータセット、モデル変種、モダリティにわたる mixed modality search 設定で大きな性能向上を達成できることを示したが、なおいくつかの限界が残されており、今後の研究に向けた有益な方向性を示している。第一に、我々は文書が画像モダリティとテキストモダリティの両方を含む現実的なシナリオを扱っているものの、各文書は1枚の画像と1つのテキスト断片に制限されている。Webページや科学論文のような、より複雑で画像とテキストが交錯する複数画像・複数テキスト文書へ評価を拡張すれば、より厳密かつ包括的な評価が可能になるだろう。第二に、GR-CLIP は、著しく少ない計算量で生成的埋め込みモデル VLM2Vec を上回るが、CLIP を基盤としているため、きめ細かなモダリティ相互作用をモデル化しない。そのため、生成的埋め込みモデルが捉えられるより深いクロスモーダル統合の機会を取り逃している可能性がある。したがって、VLM2Vec のような生成的埋め込みモデルにおけるモダリティギャップの原因を調査し、それを低減する手法を開発することは、より強力で統一的なマルチモーダル表現に向けた重要かつ未開拓な研究方向である。それでもなお、本研究は、現実的設定における mixed modality search の問題を定義し対処する上で重要な第一歩を踏み出しており、効果的な検索のために真に統一された埋め込み空間を構築することの重要性を強調し、この新興分野における将来の進展の基盤を築いている。

# Code Availability 

すべてのコードは匿名のGitHubリポジトリで公開されており、論文中の全実験を再現できる: <https://github.com/yuhui-zh15/MixedModalitySearch/>.

# Data Availability 

本研究で使用したすべてのデータセットは、この新興分野における今後の研究を促進するため、匿名でHugging Face上に公開されている: <https://huggingface.co/datasets/mixed-modality-search/MixBench2025>.

# Compute Resource 

すべての実験は、40GBのメモリを備えた単一のNVIDIA A100 GPUを用いて実施した。すべての実験は推論のみであり、必要とする計算資源は最小限である。

# Overview 

付録の概要を以下に示す。

- §8 は、モダリティおよび評価指標をまたぐ追加の一般化結果を示す。

- §9では方法の詳細を述べ、再現性のための擬似コードを含む。

- §10では使用したモデルの詳細を記述する。

- §11では、NDCGを含む評価指標を説明する。

- §12では使用したデータセットと、それに伴う前処理手順の概要を示す。

- §13では、MixBench上でCLIPとGR-CLIPを比較するケーススタディを含む。

# モダリティおよび評価指標をまたぐ一般化

本文では、NDCG@10を評価指標として用い、モダリティ間ギャップを解消することが画像-テキストデータにおける混合モダリティ検索性能を大幅に改善することを示した。ここでは、(1) 画像とテキストを超えるモダリティへの本手法の一般化、ならびに(2) 代替評価指標の下でも結論が頑健であることを示す追加結果を示す。

## モダリティをまたぐ一般化

本文の図[\[fig:setting1\]](#fig:setting1)eは、画像-テキストモダリティに関する結果を示している。図[\[fig:figone_add\]](#fig:figone_add)では、この分析を追加のモダリティ対へ拡張する。具体的には、video-text（MSVDデータセット上のViCLIP [[#^ref-31|31]]）、audio-text（Clotho [[#^ref-6|6]]データセット上のCLAP [[#^ref-32|32]]）、および追加のimage-text設定（Nights [[#^ref-8|8]]データセット上のOpenAI CLIP [[#^ref-25|25]]）に対する検索性能（NDCG@10）を報告する。いずれのケースにおいても、元のCLIPベースの結果では一貫してU字型曲線が観察されるが、モダリティ間ギャップを除去するためにGR-CLIPを適用すると、この曲線は大幅に平坦化する。この傾向は、図[\[fig:setting1\]](#fig:setting1)eの画像-テキストおよびスクリーンショット実験で観察された挙動と密接に一致しており、モダリティ間ギャップの影響と、多様なモダリティにわたる本手法の広範な適用可能性を強く支持するものである。

![](assets/fig05.png)

**モダリティをまたぐ一般化.** GR-CLIPは、モダリティ間ギャップに起因するU字型曲線を一貫して緩和し、性能を大幅に改善する。これにより、多様なモダリティ対に対する高い一般化可能性が示される。

## 指標をまたぐ一般化

本文では、NDCG@10を主要な評価指標として採用した。GR-CLIPの頑健性をさらに評価するため、NDCG@100およびRecall@1を含む追加指標へ分析を拡張する。表1は、3つすべての指標にわたるMixBench上の結果を報告しており、GR-CLIPで観測される改善が評価基準に依存せず一貫していることを示している。図[\[app:fig:ndcg100\]](#app:fig:ndcg100)および図[\[app:fig:recall1\]](#app:fig:recall1)は、それぞれNDCG@100とRecall@1を用いて§3および§4の分析をさらに拡張したものであり、同様に本研究の知見の一貫性を確認している。

  **Method**                                   **MSCOCO**              **OVEN**                **VisualNews**
  -------------------- ----------------------- ----------------------- ----------------------- -----------------------
  CLIP-B/16            0.478/0.505/0.443       0.388/0.426/0.292       0.354/0.398/0.209       0.563/0.604/0.498
  CLIP-L/14            0.505/0.516/0.454       0.426/0.490/0.329       0.389/0.431/0.253       0.596/0.656/0.525
  OpenCLIP-B/16        0.551/0.563/0.519       0.570/0.615/0.489       0.385/0.426/0.229       0.643/0.693/0.543
  OpenCLIP-L/14        0.566/0.585/0.536       0.605/0.662/0.540       0.387/0.445/0.265       0.653/0.733/0.567
  SigLIP-400m          0.546/0.566/0.523       0.327/0.374/0.260       0.372/0.428/0.271       0.385/0.475/0.366
  VLM2Vec(LLaVANext)   0.586/0.616/0.481       **0.769/0.798/0.645**   0.398/0.443/0.254       0.744/0.794/0.662
  VLM2Vec(Qwen)        0.632/0.660/0.519       0.753/0.778/0.633       0.412/0.467/0.244       0.734/0.784/0.653
  GR-CLIP-B/16         0.603/0.642/0.524       0.636/0.690/0.523       0.406/0.459/0.240       0.726/0.768/0.645
  GR-CLIP-L/14         0.648/0.678/0.555       0.656/0.708/0.547       0.465/0.523/0.296       0.754/0.770/0.661
  GR-OpenCLIP-B/16     0.636/0.666/0.572       0.668/0.751/0.589       0.434/0.490/0.253       0.758/0.783/0.664
  GR-OpenCLIP-L/14     0.678/0.704/0.604       0.699/0.784/0.629       0.467/0.525/0.282       **0.796/0.814/0.715**
  GR-SigLIP-400m       **0.692/0.722/0.608**   0.696/0.732/0.548       **0.532/0.581/0.328**   0.769/0.793/0.671

  : **MixBenchにおける全指標での詳細結果.** 各セルはNDCG@10、NDCG@100、Recall@1を報告する。最良結果は太字で示す。指標全体にわたる一貫した性能は、異なる評価基準に対する本手法の頑健性を示している。GR-CLIPがMSCOCOでVLM2Vecを下回るのは、VLM2VecがMSCOCOで学習されているためである。 

![](assets/fig06.png)

**主論文の図[\[fig:setting1\]](#fig:setting1)を、評価指標としてNDCG@100を用いて再現したもの。**

![](assets/fig07.png)

**主論文の図[\[fig:setting2\]](#fig:setting2)を、評価指標としてNDCG@100およびRecall@1を用いて再現したもの。**

# 方法の詳細

§2.3で導入したように、GR-CLIPは各モダリティのグローバル平均ベクトルを差し引くことでモダリティ間ギャップを緩和する。具体的には、クエリ平均$\bar{e}_q$、文書テキスト平均$\bar{e}^T$、文書画像平均$\bar{e}^I$の3つの平均ベクトルを計算する。

$$\bar{e}_q = \mathbb{E}_{q \sim \mathcal{Q}} [f^T(q)], \quad
\bar{e}^T = \mathbb{E}_{d^T \sim \mathcal{D}_{\text{text}}} [f^T(d^T)], \quad
\bar{e}^I = \mathbb{E}_{d^I \sim \mathcal{D}_{\text{image}}} [f^I(d^I)].$$

クエリはしばしば短く疑問的である一方、文書は通常より長く記述的であるため、構造的・意味的差異を考慮して、クエリ平均$\bar{e}_q$をテキスト文書平均$\bar{e}^T$と区別する。この区別は、アライメントの偏りを低減し、検索性能を向上させるうえで重要である。

データセット間での一般化を確保し、テストセットへの情報漏洩を防ぐため、各データセットのテストセットごとに別個の平均を推定するのではなく、複数データセットの訓練セットから統一的な平均ベクトルを計算する。この統一平均は、その後すべてのテストセットに対して一貫して適用される。

**クエリ平均（$\bar{e}_q$）:** MSCOCO、Google WIT、NFCorpus、VisualNewsの訓練分割から約10000件のテキストクエリをサンプリングする。これらを$f^T$でエンコードして平均し、グローバルなクエリ平均$\bar{e}_q$を得る。

**文書テキスト平均（$\bar{e}^T$）:** MSCOCO、OVEN、Google WIT、VisualNewsの訓練分割から約10000件の長文テキスト文書または記述的キャプションをサンプリングする。これらを$f^T$でエンコードして平均し、文書テキスト平均$\bar{e}^T$を得る。

**文書画像平均（$\bar{e}^I$）:** $\bar{e}^I$を計算するため、MSCOCO、OVEN、Google WIT、VisualNewsの訓練分割から10000枚の画像をサンプリングする。これらを$f^I$でエンコードして平均し、文書画像平均を得る。

**OVEN固有のクエリ平均（$\bar{e}_q^{\text{OVEN}}$）:** OVENにおけるクエリは特に短いため、OVENの訓練分割から2000件のクエリをサンプリングして、データセット固有のクエリ平均を構築する。

**その他のモダリティ平均:** MSVD（video-text）、Clotho（audio-text）、およびSciFactとNFCorpusにおけるスクリーンショット風文書（screenshot-text）など、画像-テキスト以外のデータセットについては、モダリティごとに2500件の訓練例を用いてモダリティ固有の平均を計算する。

GR-CLIPの完全なアルゴリズムを以下に要約する。

2

\
Calibration sets: $\mathcal{Q}'$, $\mathcal{D}'$\
Query set $\mathcal{Q} = \{q_1, \dots, q_n\}$ (text only)\
Document set $\mathcal{D} = \{d_1, \dots, d_m\}$ (text, image, or both for each)\
Pretrained encoders $f^T$, $f^I$, interpolation factor $\alpha \in [0,1]$

*// Step 1: Pre-compute global means from $\mathcal{Q}', \mathcal{D}'$* $\bar{e}_q \gets \mathbb{E}_{q \sim \mathcal{Q}'} [f^T(q)]$ $\bar{e}^T \gets \mathbb{E}_{d^T \sim \mathcal{D}'_{\text{text}}} [f^T(d^T)]$ $\bar{e}^I \gets \mathbb{E}_{d^I \sim \mathcal{D}'_{\text{image}}} [f^I(d^I)]$

*// Step 2: Encode query embeddings* $e_{q_i} \gets f^T(q_i) - \bar{e}_q$

*// Step 3: Encode document embeddings* $e_{d_j} \gets f^T(d_j) - \bar{e}^T$ $e_{d_j} \gets f^I(d_j) - \bar{e}^I$ $e_{d_j} \gets \alpha f^T(d_j^T) +(1{-}\alpha) f^I(d_j^I)$
$- [\alpha \bar{e}^T + (1{-}\alpha) \bar{e}^I]$

*// Step 4: Retrieval* $s(q_i,d_j) \gets \frac{e_{q_i} \cdot e_{d_j}}{\|e_{q_i}\| \cdot \|e_{d_j}\|}$ $\text{Ranks} \gets \text{argsort}(s, \text{descending})$ $\text{Ranks}$

# モデルの詳細

本節では、実験で使用した全モデルについて、正確なバージョンとチェックポイントへのリンクを提示する。CLIPベースのモデルとしては、**OpenAI CLIP** [[#^ref-25|25]]の2種、**OpenCLIP** [[#^ref-33|33]]の2種、ならびに**SigLIP-400M** [[#^ref-34|34]]を含める。

VLM2Vecフレームワークについては、2種を用いる。1つは**LLaVA-Next** [[#^ref-20|20]]に基づくもので、主論文で報告した結果のバックボーンである[[#^ref-12|12]]。もう1つは、公式リポジトリによればMMEB [[#^ref-12|12]]ベンチマークで最良性能を達成する、最新の公式公開版**Qwen-VL** [[#^ref-1|1]]に基づくものである。

さらに、画像-テキスト以外のモダリティについては、video-text検索タスクに**ViCLIP**[[#^ref-31|31]]、audio-text検索タスクに**CLAP**[[#^ref-32|32]]を用いる。

各モデルのチェックポイントリンクは以下のとおりである。

- **OpenAI CLIP-B/16**: <https://huggingface.co/openai/clip-vit-base-patch16>

- **OpenAI CLIP-L/14**: <https://huggingface.co/openai/clip-vit-large-patch14-336>

- **OpenCLIP-B/16**: <https://huggingface.co/laion/CLIP-ViT-B-16-laion2B-s34B-b88K>

- **OpenCLIP-L/14**: <https://huggingface.co/laion/CLIP-ViT-L-14-laion2B-s32B-b82K>

- **SigLIP-400m**: <https://huggingface.co/google/siglip-so400m-patch14-384>

- **VLM2Vec (LLaVA-Next)**: <https://huggingface.co/TIGER-Lab/VLM2Vec-LLaVa-Next>

- **VLM2Vec (Qwen-VL)**: <https://huggingface.co/TIGER-Lab/VLM2Vec-Qwen2VL-7B>

- **ViCLIP-L/14**: <https://huggingface.co/OpenGVLab/ViCLIP-L-14-hf>

- **CLAP**: <https://huggingface.co/laion/clap-htsat-fused>

# 評価指標の詳細

本文では、広く採用されているNDCG@10を評価指標として用いた。ここでは、この指標の詳細な計算過程を示す。

位置$K$までの検索結果ランキングリストが与えられたとき、NDCG@$K$は次式で計算される。

$$\text{NDCG@}K = \frac{1}{\text{IDCG@}K} \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$

ここで$\text{rel}_i$は順位$i$のアイテムの関連性スコアを表し、IDCG@$K$は理想的なDCG、すなわち上位$K$件に対して達成可能な最大のDCGであり、関連性の降順にアイテムを並べ替えることで計算される。

$$\text{IDCG@}K = \sum_{i=1}^{K} \frac{2^{\text{rel}_i^\star} - 1}{\log_2(i + 1)}$$

ここで$\text{rel}_i^\star$は、理想ランキングにおける$i$番目に高い関連性スコアである。

NDCG@10の値域は0から1であり、1は完全なランキングを表す。

# データセットの詳細

本節では、§3、4、5における検索実験を支えるために、各データセットがどのように処理されるかについて追加の詳細を示す。各データセットについて、元のデータ形式（*Before*）と、本フレームワークで用いた修正版（*After*）を区別する。また、主要な後処理手順も説明する。

**NFCorpus [[#^ref-3|3]], SciFact [[#^ref-30|30]]:**\
*Before:* 短いテキストクエリと、それに対応する関連長文テキスト文書の組。\
*After:* 短いテキストクエリは保持し、長文テキスト文書をOpenCVを用いてスクリーンショットとしてレンダリングする。これにより、クエリに応じて元のテキスト文書またはレンダリング済みスクリーンショットのいずれかを検索できる。

**Google WIT [[#^ref-27|27]]:**\
*Before:* 各サンプルは、ページタイトル、長いページ説明、参照画像、およびその画像に対する参照説明を含む。\
*After:* ページタイトルと画像参照説明を連結してクエリを形成する。ページ説明は長文テキスト文書として用い、関連画像は画像文書として利用する。

**OVEN [[#^ref-10|10]]:**\
*Before:* 各クエリは画像とテキストのペアから成り、検索対象もまた画像記述ペアである。\
*After:* 画像またはテキストのいずれか一方だけでクエリに独立に答えられるため、画像とキャプションの双方を有効な単独文書として扱う。クエリは変更しない。

**MSCOCO [[#^ref-18|18]]:**\
*Before:* 各画像は5つのキャプションと対応付けられている。\
*After:* 1つのキャプションをクエリとしてサンプルする。残りのキャプションは、サンプルしたキャプションの内容を保持したまま、GPT-4o により長文記述を構成するために用いる。この長文記述をテキスト文書とし、対応する画像を画像文書として用いる。

**VisualNews [[#^ref-19|19]]:**\
*Before:* 各画像は短いニュース風キャプションと対応付けられている。\
*After:* GPT-4o を用いて、画像と元の VisualNews データセットに含まれる記事を同時に分析する。視覚的内容と記事テキストの双方に基づき、GPT-4o は元のキャプションを拡張する詳細な記述段落を生成し、これをテキスト文書として用いる。画像は画像文書として用い、元のキャプションはクエリとして保持する。

**Clotho [[#^ref-6|6]]:**\
*Before:* 各音声クリップは、意味的に類似した複数のキャプションと対応付けられている。\
*After:* 1つのキャプションをクエリとして選択し、意味的に類似する別のキャプション（GPT-4o により選択）をテキスト文書として用いる。音声クリップ自体は音声文書として用いる。

**MSVD [[#^ref-4|4]]:**\
*Before:* 各動画は、意味的に類似した複数のキャプションと対応付けられている。\
*After:* 1つのキャプションをクエリとして用い、意味的に類似する別のキャプション（GPT-4o により選択）をテキスト文書として用いる。動画は動画文書として扱う。

**Nights [[#^ref-8|8]]:**\
*Before:* 各画像は視覚的に類似した別画像と対応付けられている。\
*After:* 1つの画像をクエリとして用いる。GPT-4o はこの画像を観察して簡潔なタイトルを生成し、これをテキスト文書として用いる。対となる画像は画像文書として用いる。

**VLM2Vec input format:** **VLM2Vec** [[#^ref-12|12]]では、埋め込み生成のための指示としてプロンプトが必要である。具体的には、各 *Query* に対して、多モダリティから成る異種コーパスから検索を行う setting 1 および 3 では、プロンプト `‘‘Retrieve a relevant item that represents: {Query}\n’’` を用いる。Setting 2 では、融合された画像-テキストペアから成る同種コーパスを対象に検索を行うため、`‘‘Retrieve an image-description pair that represents: {Query}\n’’` を用いる。Documents は元のデータセットで規定された形式に従う。

**CLIP input format:** **CLIP** ベースのモデル [[#^ref-25|25]][[#^ref-34|34]][[#^ref-33|33]][[#^ref-31|31]][[#^ref-32|32]] および **GR-CLIP** については、いかなる指示も適用しない。Queries と documents は、それぞれ対応する CLIP の text encoder および image encoder にそのまま変更なく入力する。

Table 2 は、検索設定、クエリとコーパスのモダリティ構成、ならびに評価例の総数を含む、各データセットの主要特性を要約したものである。

  **Dataset**                 **Queries**   **Documents**   **Setting No.**   **\# of Queries**   **\# of Documents**
  -------------------------- ------------- --------------- ----------------- ------------------- ---------------------
  Google WIT [[#^ref-27|27]]          T        T / I / I + T        1,2,3              1000                 4423
  OVEN [[#^ref-10|10]]                   T + I      T / I / I + T        1,2,3              1000                 1000
  MSCOCO [[#^ref-18|18]]                 T        T / I / I + T        1,2,3               984                  984
  VisualNews [[#^ref-19|19]]         T        T / I / I + T        1,2,3               981                  981
  SciFact [[#^ref-30|30]]               T            T / S              1                 300                 5183
  NFCorpus [[#^ref-3|3]]             T            T / S              1                 323                 3633
  MSVD [[#^ref-4|4]]                     T            T / V              1                 670                  670
  Clotho [[#^ref-6|6]]                 T            T / A              1                1046                 1046
  Nights [[#^ref-8|8]]                 I            I / T              1                1000                 1000

  : **実験で用いたデータセットの概要。** 各データセットについて、検索設定、クエリおよび文書に含まれるモダリティ（T = text, I = image, S = screenshot, V = video, A = audio）、ならびに評価に用いたクエリ-文書対の数を示す。

# Case Studies 

以下では、MixBench の各サブセットからの case study を示す。これは同時に我々のデータセットの可視化としても機能する。各例示クエリについて、ベースラインである OpenAI CLIP-L/14 と提案手法 GR-CLIP-L/14 の双方から得られた Top-5 の検索結果を示す。各検索文書には、そのモダリティ（[text]{style="color: Orange"}、[image]{style="color: Magenta"}、または [multimodal]{style="color: Green"}）、クエリに対する cosine similarity、ならびに **ground-truth** の関連項目であるかどうかを付記する。

これらの例示結果は、MixBench データセットの多様性と、混合モダリティ検索における GR-CLIP の有効性の双方を示している。クエリのモダリティに一致する文書を返しがちな元の CLIP モデルとは異なり、GR-CLIP はモダリティの差異をうまく架橋し、モダリティにかかわらずクエリの意味的意図をより正確に反映する結果を検索する。

## Google WIT [[#^ref-27|27]]

*[Query:]{style="color: blue"}* List of Jews in sports, Nate Ebner

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.5430, *Modality* = [text]{style="color: Orange"}

This is a list of individuals currently serving in the United States House of Representatives.\
*Rank No.2*, *Cosine Similarity* = 0.5355, *Modality* = [text]{style="color: Orange"}

This is a list of notable Austrians.\
*Rank No.3*, *Cosine Similarity* = 0.5227, *Modality* = [text]{style="color: Orange"}

This is a list of vehicles manufactured by the Buick Motor Division of General Motors.\
*Rank No.4*, *Cosine Similarity* = 0.5181, *Modality* = [text]{style="color: Orange"}

This is a list of notable alumni and faculty of Golden Gate University.\
*Rank No.5*, *Cosine Similarity* = 0.5101, *Modality* = [text]{style="color: Orange"}

Puthenchira is a village in Thrissur district in the state of Kerala, India.\

------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.3403, *Modality* = [Image]{style="color: Magenta"} (**Ground Truth**)

![](assets/fig08.png)

*Rank No.2*, *Cosine Similarity* = 0.1798, *Modality* = [text]{style="color: Orange"}

This is a list of notable Austrians.\
*Rank No.3*, *Cosine Similarity* = 0.1774, *Modality* = [text]{style="color: Orange"}

The Lebanon national football team, controlled by the Lebanese Football Association, have represented Lebanon in association football since their inception in 1933. The squad is governed by the Asian Football Confederation continentally, and FIFA worldwide. While Lebanon have yet to qualify for the FIFA World Cup, they have participated twice in the Asian Cup: in 2000, when they hosted the event, and in 2019, the first time through regular qualification. Lebanon's main venue is the Camille Chamoun Sports City Stadium in Beirut; however they also play in other locations such as the Saida International Stadium in Sidon. In 1934, Lebanon played their first match against the Romanian side CA Timișoara, but it was not ratified by FIFA. Lebanon played their first FIFA-recognised game in 1940 against Mandatory Palestine. During their 2014 qualification campaign for the World Cup, Lebanon reached the final qualifying round for the first time thanks to a 2--1 victory against South Korea at home in 2011, but failed to qualify for the 2014 FIFA World Cup finishing bottom of their group. At the 2019 Asian Cup, Lebanon were close to qualifying to the knock-out stages for the first time.\
*Rank No.4*, *Cosine Similarity* = 0.1723, *Modality* = [text]{style="color: Orange"}

This is a list of properties and historic districts in Winchester, Massachusetts, that are listed on the National Register of Historic Places. The locations of National Register properties and districts may be seen in an online map by clicking on \"Map of all coordinates.\" This National Park Service list is complete through NPS recent listings posted July 17, 2020.\
*Rank No.5*, *Cosine Similarity* = 0.1708, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig09.png)

This list is of that portion of the National Register of Historic Places designated in Essex County, Massachusetts. The locations of these properties and districts for which the latitude and longitude coordinates are included below, may be seen in a map. There are more than 450 designated properties in the county, including 25 that are further designated as National Historic Landmarks. The municipalities of Andover, Gloucester, Ipswich, Lawrence, Lynn, Methuen, and Salem are to be found on a separate list of the more than 200 identified here, except two properties are split between Methuen and Lawrence, and one between Lynn and Nahant; these entries appear on more than one list. This National Park Service list is complete through NPS recent listings posted August 14, 2020.

## MSCOCO [[#^ref-18|18]]

*[Query:]{style="color: blue"}* ひとりの女性が猫のいる部屋にいる。\
------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.5044, *Modality* = [text]{style="color: Orange"}

淡色の木製キャビネットと黒い御影石のカウンタートップを備えたキッチンである。4口コンロ付きの黒いストーブ、レンジ上部に設置された電子レンジ、黒い冷蔵庫が含まれている。床は暖かみのある木目調である。\
*Rank No.2*, *Cosine Similarity* = 0.4605, *Modality* = [text]{style="color: Orange"}

猫がトイレの閉じたふたの上に乗っており、やや不機嫌そうに見える。トイレは淡い色の壁のある浴室に置かれている。トイレの横にはかごまたは容器がある。猫の尾が見えており、警戒しているか、あるいは驚いているように見える。\
*Rank No.3*, *Cosine Similarity* = 0.4445, *Modality* = [text]{style="color: Orange"}

長いホットドッグが白い紙皿の上のバンズに挟まれており、その紙皿は木製のテーブルの上に置かれている。ホットドッグはバンズの両端からはみ出している。\
*Rank No.4*, *Cosine Similarity* = 0.4160, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig10.png)

暖かく居心地のよい居間はクリスマス装飾で彩られており、暖炉のそばには銀色のティンセルのクリスマスツリーがある。部屋のあちこちには包装された贈り物が赤いカーペットの上に散らばっている。マントルピースの上には祝祭的な装飾品や靴下が置かれ、ホリデーの雰囲気を添えている。クッション付きの快適なベージュ色のソファが、雑誌の置かれたコーヒーテーブルのそばにある。天井はきらめく金色の星で飾られ、ダーツボードのゲームを映すテレビが、生活感のある祝祭的な雰囲気を加えている。ランプの柔らかな照明が、部屋の招待的な空気をいっそう高めている。

*Rank No.5*, *Cosine Similarity* = 0.4126, *Modality* = [text]{style="color: Orange"}

新鮮なトマト、緑のオリーブ、薄くスライスしたタマネギをのせたおいしそうなイタリアンピザが、白い皿の上に盛り付けられている。ハーブと調味料が添えられ、料理に色彩豊かで風味豊かなアクセントを加えている。\
------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.3012, *Modality* = [multimodal]{style="color: ForestGreen"} (**Ground Truth**)

![](assets/fig11.png)

女性が台所に立っており、微笑みながら猫を抱いている。彼女は茶色のセーターと青いチェック柄のスカートを着用している。台所には木製のキャビネットがあり、カウンターの上には鉢植えとオレンジの入ったボウルが置かれている。片側には食器のあるシンクがあり、反対側には白い冷蔵庫がある。壁には時計が見え、カウンター上にはさまざまな物品があり、床には小さなラグが敷かれている。

*Rank No.2*, *Cosine Similarity* = 0.2924, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig12.png)

眼鏡をかけた黒いシャツの人物が、閉じたブラインドのある窓際に座り、ラジエーターに掛けられた紫の毛布の上にいる猫をブラッシングしている。猫は背を向けており、ブラシはマゼンタ色で、ブラシ毛の部分は灰色である。床は木製で、猫はくつろいでいるように見える。

*Rank No.3*, *Cosine Similarity* = 0.2780, *Modality* = [text]{style="color: Orange"}

猫が閉じた便器のふたの上に乗っており、やや動揺しているように見える。便器は淡い色の壁を持つ浴室に置かれている。便器の隣にはかごまたは容器がある。猫の尾が見えており、警戒している、あるいは驚いている可能性がある。\
*Rank No.4*, *Cosine Similarity* = 0.2745, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig13.png)

灰色のアームチェアと黒いアームチェアが部屋の中で互いに並んで配置されている。黒い椅子の隣のテーブルには小さなランプが置かれている。アームチェアの後ろから猫が半分見えており、場面に遊び心を添えている。椅子の前には木製のテーブルがあり、その上にリモコンが置かれている。

*Rank No.5*, *Cosine Similarity* = 0.2612, *Modality* = [image]{style="color: Magenta"}

![](assets/fig14.png)

## OVEN [[#^ref-10|10]]

*[Query:]{style="color: blue"}*

![](assets/fig15.png)

この建物の名称は何か。

\

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.5340, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig16.png)

**Clérigos Church.** Clérigos Church は、ポルトガルのポルト市にあるバロック様式の教会である。その高さ75メートルの鐘楼 Torre dos Clérigos は市内のさまざまな地点から見ることができ、同市を代表する象徴の一つである。歴史：この教会は、18世紀にポルトガル北部で多くの作品を残したイタリア人建築家・画家 Nicolau Nasoni によって、Clérigos（聖職者）兄弟団のために建設された。教会の建設は1732年に始まり1750年に完成したが、鐘楼および記念碑的な分節階段\...

\
*Rank No.2*, *Cosine Similarity* = 0.5321, *Modality* = [image]{style="color: Magenta"}

![](assets/fig17.png)

*Rank No.3*, *Cosine Similarity* = 0.5276, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig18.png)

**St. Peter's Basilica.** Vatican の Saint Peter の Papal Basilica、あるいは単に Saint Peter's Basilica は、Vatican City に所在するルネサンス様式の教会である。これは当初、ローマ皇帝 Constantine the Great により4世紀に建設された老朽化した Old St. Peter's Basilica に代わるものとして、Pope Nicholas V、続いて Pope Julius II によって計画された。現存する大聖堂の建設は1506年4月18日に始まり、1626年11月18日に完成した。主として Donato Bramante、Michelangelo、Carlo Maderno、Gian Lorenzo Bernini によって設計され\...

\
*Rank No.4*, *Cosine Similarity* = 0.5274, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig19.png)

**Coit Tower.** Coit Tower は、カリフォルニア州サンフランシスコの Telegraph Hill 地区にある高さ210フィートの塔であり、市街と湾を一望できる。都市美化のための Lillie Hitchcock Coit の遺贈を用いて1932年から1933年にかけて建設され、2008年に National Register of Historic Places に登録された。Arthur Brown, Jr. と Henry Howard によって設計された、塗装されていない鉄筋コンクリート製の塔には、25人の現地アーティストによるアメリカン・フレスコ壁画が施されている\...

\
*Rank No.5*, *Cosine Similarity* = 0.5252, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig20.png)

**Ilinden (Memorial).** Makedonium としても知られる Ilinden は、北マケドニアの Kruševo にある記念碑である。1974年8月2日に正式に公開され、反ファシスト会議の第二会期および1903年の Ilinden 蜂起を記念している。Jordan と Iskra Grabuloski によって設計され、1941--1944年の National Liberation Struggle の戦士たちを顕彰している。説明。この記念碑は12エーカーを占め、丸みを帯びた建築様式を特徴とする\...

------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.3153, *Modality* = [text]{style="color: Orange"} (**Ground Truth**)

Canadian National Vimy Memorial. Canadian National Vimy Memorial は、第一次世界大戦中に戦死した Canadian Expeditionary Force の隊員を追悼するためにフランスに設けられた戦争記念施設である。また、フランスで戦死した、または戦死したとみなされており、墓所が判明していない第一次世界大戦のカナダ兵の追悼の場でもある。この記念碑は、Battle of Arras の Battle of Vimy Ridge 初期攻勢において Canadian Corps が突撃した地の一部を含む、100（ha）の保存戦場公園の中心的存在である。\
*Rank No.2*, *Cosine Similarity* = 0.2795, *Modality* = [image]{style="color: Magenta"}

![](assets/fig21.png)

*Rank No.3*, *Cosine Similarity* = 0.2762, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig22.png)

Mary, Queen of the World Cathedral. Mary, Queen of the World Cathedral、正式には Mary, Queen of the World and St. James the Great Cathedral は、カナダのケベック州モントリオールにある小バシリカであり、モントリオールのローマ・カトリック大司教区の座所である。ケベック州では、Saint Joseph's Oratory（同じくモントリオール）およびケベック市東方の Basilica of Sainte-Anne-de-Beaupré に次いで3番目に大きな教会である。建物の長さは101 m（333 ft）、幅は46 m（150 ft）で、クーポラの最大高さは77 m（252 ft）、その直径は23 m（75 ft）である。

\
*Rank No.4*, *Cosine Similarity* = 0.2744, *Modality* = [image]{style="color: Magenta"}

![](assets/fig23.png)

*Rank No.5*, *Cosine Similarity* = 0.2590, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig24.png)

Sydney Town Hall. Sydney Town Hall は、オーストラリアのニューサウスウェールズ州の州都シドニーにある19世紀後半の歴史的建造物指定の市庁舎であり、Sydney の Lord Mayor の議場、評議会事務所、会議および催事の会場を擁している。Queen Victoria Building の向かい、St Andrew's Cathedral に隣接する Sydney central business district の 483 George Street に位置する。Town Hall 駅の上にあり、市内のショッピング地区と娯楽地区の間に立地するため、Town Hall の階段は人気の待ち合わせ場所となっている。John H. Wilson、Edward Bell、Albert Bond によって設計された。

## VisualNews [[#^ref-19|19]]

*[Query:]{style="color: blue"}* 元カリフォルニア州警官の Jay Cicinelli が、ホームレス男性殺害裁判で無罪評決を聞いた直後に頭を両手で抱える。

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.4364, *Modality* = [text]{style="color: Orange"}

この法廷スケッチでは、注目度の高い裁判の量刑段階において、その人物が描かれている厳粛な場面が展開されている。その人物には死刑が宣告され、司法手続における重要な局面を示している。緊張と重みを帯びた法廷は、手続の深刻さを反映している。このスケッチは、裁判所によって下された判断の雰囲気と重さを捉えている。\

*Rank No.2*, *Cosine Similarity* = 0.4186, *Modality* = [text]{style="color: Orange"}

画像には、アルゼンチンの1976--83年軍事独裁政権下でカトリック司教殺害に関与したとして終身刑を言い渡された元将軍が映っている。この裁判では、フランシスコ教皇が提供したバチカン文書館の書簡を含む文書が明らかにされ、司教が政権の虐待を告発していたことが示された。この将軍は、1976年に Enrique Angelelli 司教の殺害を命じた罪で有罪とされ、軍政時代の高位聖職者殺害に関わる元当局者に対する重要な有罪判決となった。\

*Rank No.3*, *Cosine Similarity* = 0.3994, *Modality* = [text]{style="color: Orange"}

2011年10月3日、感情的緊張に満ちた法廷で、Amanda Knox が殺人罪の有罪判決に対する控訴に勝訴したとの発表を受けて、Amanda Knox の父親が妻に抱きしめられている。支持者や家族が判決に反応し、安堵と歓喜が漂う。画像は、広く報道された劇的な法廷闘争の文脈の中で、家族的支援と祝福の痛切な瞬間を捉えている。\

*Rank No.4*, *Cosine Similarity* = 0.3718, *Modality* = [text]{style="color: Orange"}

Sudheendra Kulkarni は黒インクを浴びせられ、顔と頭が覆われた。この事件は公の場で発生し、画像に見られるようにメディアの注目と警察の出動を招いた。その後 Kulkarni はインクを除去するため病院に搬送された。この出来事は緊張を浮き彫りにし、広範な反応を引き起こしており、公的言説の不安定さを強調するものであった。\

*Rank No.5*, *Cosine Similarity* = 0.3698, *Modality* = [text]{style="color: Orange"}

Rev Sidney Davis は、9人の黒人礼拝者の命を奪った悲劇的な銃撃事件を受けて、Charleston の Second Presbyterian Church における地域祈祷会で弔問客を導いている。この集まりは、哀悼の参加者が手を取り合って祈る中で、暴力に直面した共同体の悲嘆と連帯を表している。この出来事は、Obama 大統領時代に強調された人種問題と銃規制をめぐる継続的な議論を浮き彫りにしている。沈痛な雰囲気は、アメリカにおける人種的緊張と銃暴力をめぐる課題と未解決問題を想起させる。

------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.4265, *Modality* = [image]{style="color: Magenta"} (**Ground truth**)

![](assets/fig25.png)

*Rank No.2*, *Cosine Similarity* = 0.3605, *Modality* = [text]{style="color: Orange"}

この法廷スケッチでは、注目度の高い裁判の量刑段階において、その人物が描かれている厳粛な場面が展開されている。その人物には死刑が宣告され、司法手続における重要な局面を示している。緊張と重みを帯びた法廷は、手続の深刻さを反映している。このスケッチは、裁判所によって下された判断の雰囲気と重さを捉えている。\

*Rank No.3*, *Cosine Similarity* = 0.3365, *Modality* = [text]{style="color: Orange"}

画像には、アルゼンチンの1976--83年軍事独裁政権下でカトリック司教殺害に関与したとして終身刑を言い渡された元将軍が映っている。この裁判では、フランシスコ教皇が提供したバチカン文書館の書簡を含む文書が明らかにされ、司教が政権の虐待を告発していたことが示された。この将軍は、1976年に Enrique Angelelli 司教の殺害を命じた罪で有罪とされ、軍政時代の高位聖職者殺害に関わる元当局者に対する重要な有罪判決となった。\

*Rank No.4*, *Cosine Similarity* = 0.3224, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig26.png)

国会議員らは、若者向け入院精神保健サービスへのアクセス不足について懸念を表明しており、Nikki Mattocks の事例のように、著しい遅延と不十分な支援に直面したケースを指摘している。重篤な精神健康上の問題に苦しみながらも、彼女は断片化されたケア体制に置かれ、その結果、救急外来への繰り返しの受診や遠方の精神科病棟への入院を余儀なくされた。この継続性の欠如と家族からの地理的な隔離は、彼女の状態をさらに悪化させた。議会報告書は、脆弱な若者へのさらなる被害を防ぐため、早期介入とより適切な資源配分の緊急性を強調している。

*Rank No.5*, *Cosine Similarity* = 0.2956, *Modality* = [text]{style="color: Orange"}

2011年10月3日、感情的な緊張に満ちた法廷で、Amanda Knox の父親は、Amanda が殺人罪の有罪判決に対する控訴で勝訴したとの発表の後、妻に抱きしめられている。支援者や家族が評決に反応する中、場内は安堵と喜びに満ちた雰囲気に包まれている。この画像は、世間の注目を集めた劇的な法廷闘争という広い文脈の中で、家族による支援と祝意の感動的な瞬間を捉えている。

## References

[1] J. Bai, S. Bai, S. Yang, S. Wang, S. Tan, P. Wang, J. Lin, C. Zhou, and J. Zhou. Qwen-vl: A versatile vision-language model for understanding, localization, text reading, and beyond. arXiv preprint arXiv:2308.12966, 2023. ^ref-1

[2] P. BehnamGhader, V. Adlakha, M. Mosbach, D. Bahdanau, N. Chapados, and S. Reddy. Llm2vec: Large language models are secretly powerful text encoders. arXiv preprint arXiv:2404.05961, 2024. ^ref-2

[3] V. Boteva, D. Gholipour, A. Sokolov, and S. Riezler. A full-text learning to rank dataset for medical information retrieval. 2016. ^ref-3

[4] D. Chen and W. Dolan. Collecting highly parallel data for paraphrase evaluation. In ACL, 2011. ^ref-4

[5] Y.-C. Chen, L. Li, L. Yu, A. El Kholy, F. Ahmed, Z. Gan, Y. Cheng, and J. Liu. Uniter: Universal image-text representation learning. In ECCV, 2020. ^ref-5

[6] K. Drossos, S. Lipping, and T. Virtanen. Clotho: An audio captioning dataset. In ICASSP, pages 736-740. IEEE, 2020. ^ref-6

[7] M. Faysse, H. Sibille, T. Wu, B. Omrani, G. Viaud, C. HUDELOT, and P. Colombo. Colpali: Efficient document retrieval with vision language models. In ICLR, 2025. ^ref-7

[8] S. Fu, N. Y. Tamir, S. Sundaram, L. Chai, R. Zhang, T. Dekel, and P. Isola. Dreamsim: Learning new dimensions of human visual similarity using synthetic data. In NeurIPS, 2023. ^ref-8

[9] R. Girdhar, A. El-Nouby, Z. Liu, M. Singh, K. V. Alwala, A. Joulin, and I. Misra. Imagebind: One embedding space to bind them all. In CVPR, 2023. ^ref-9

[10] H. Hu, Y. Luan, Y. Chen, U. Khandelwal, M. Joshi, K. Lee, K. Toutanova, and M.-W. Chang. Open-domain visual entity recognition: Towards recognizing millions of wikipedia entities. In ICCV, 2023. ^ref-10

[11] K. J\"arvelin and J. Kek\"al\"ainen. Cumulated gain-based evaluation of ir techniques. TOIS, 2002. ^ref-11

[12] Z. Jiang, R. Meng, X. Yang, S. Yavuz, Y. Zhou, and W. Chen. VLM2vec: Training vision-language models for massive multimodal embedding tasks. In ICLR, 2025. ^ref-12

[13] V. Karpukhin, B. Oguz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W.-t. Yih. Dense passage retrieval for open-domain question answering. In EMNLP, 2020. ^ref-13

[14] O. Khattab and M. Zaharia. Colbert: Efficient and effective passage search via contextualized late interaction over bert. In SIGIR, 2020. ^ref-14

[15] K.-H. Lee, X. Chen, G. Hua, H. Hu, and X. He. Stacked cross attention for image-text matching. In ECCV, 2018. ^ref-15

[16] L. H. Li, M. Yatskar, D. Yin, C.-J. Hsieh, and K.-W. Chang. Visualbert: A simple and performant baseline for vision and language. arXiv preprint arXiv:1908.03557, 2019. ^ref-16

[17] V. W. Liang, Y. Zhang, Y. Kwon, S. Yeung, and J. Y. Zou. Mind the gap: Understanding the modality gap in multi-modal contrastive representation learning. In NeurIPS, 2022. ^ref-17

[18] T.-Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Doll\'ar, and C. L. Zitnick. Microsoft coco: Common objects in context. In ECCV, 2014. ^ref-18

[19] F. Liu, Y. Wang, T. Wang, and V. Ordonez. Visual news: Benchmark and challenges in news image captioning. In NeurIPS, 2021. ^ref-19

[20] H. Liu, C. Li, Y. Li, B. Li, Y. Zhang, S. Shen, and Y. J. Lee. Llava-next: Improved reasoning, ocr, and world knowledge, January 2024. ^ref-20

[21] H. Liu, C. Li, Q. Wu, and Y. J. Lee. Visual instruction tuning. In NeurIPS, 2023. ^ref-21

[22] J. Lu, D. Batra, D. Parikh, and S. Lee. Vilbert: Pretraining task-agnostic visiolinguistic representations for vision-and-language tasks. In NeurIPS, 2019. ^ref-22

[23] N. Muennighoff, S. Hongjin, L. Wang, N. Yang, F. Wei, T. Yu, A. Singh, and D. Kiela. Generative representational instruction tuning. In ICLR 2024 Workshop, 2024. ^ref-23

[24] J. Ngiam, A. Khosla, M. Kim, J. Nam, H. Lee, A. Y. Ng, et al. Multimodal deep learning. In ICML, 2011. ^ref-24

[25] A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal, G. Sastry, A. Askell, P. Mishkin, J. Clark, G. Krueger, and I. Sutskever. Learning transferable visual models from natural language supervision. In ICML, 2021. ^ref-25

[26] S. Robertson, H. Zaragoza, et al. The probabilistic relevance framework: Bm25 and beyond. Foundations and Trends in Information Retrieval, 2009. ^ref-26

[27] K. Srinivasan, K. Raman, J. Chen, M. Bendersky, and M. Najork. Wit: Wikipedia-based image text dataset for multimodal multilingual machine learning. In SIGIR, 2021. ^ref-27

[28] N. Srivastava and R. R. Salakhutdinov. Multimodal learning with deep boltzmann machines. In NIPS, 2012. ^ref-28

[29] Voyage AI. voyage-multimodal-3: all-in-one embedding model for interleaved text, images, and screenshots. Blog post, Nov. 2024. ^ref-29

[30] D. Wadden, S. Lin, K. Lo, L. L. Wang, M. van Zuylen, A. Cohan, and H. Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP, 2020. ^ref-30

[31] Y. Wang, K. Li, Y. Li, Y. He, B. Huang, Z. Zhao, H. Zhang, J. Xu, Y. Liu, Z. Wang, et al. Internvideo: General video foundation models via generative and discriminative learning. arXiv preprint arXiv:2212.03191, 2022. ^ref-31

[32] Y. Wu*, K. Chen*, T. Zhang*, Y. Hui*, T. Berg-Kirkpatrick, and S. Dubnov. Large-scale contrastive language-audio pretraining with feature fusion and keyword-to-caption augmentation. In ICASSP, 2023. ^ref-32

[33] H. Xu, S. Xie, X. Tan, P.-Y. Huang, R. Howes, V. Sharma, S.-W. Li, G. Ghosh, L. Zettlemoyer, and C. Feichtenhofer. Demystifying CLIP data. In ICLR, 2024. ^ref-33

[34] X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer. Sigmoid loss for language image pre-training. In ICCV, 2023. ^ref-34

[35] Y. Zhang, J. Z. HaoChen, S.-C. Huang, K.-C. Wang, J. Zou, and S. Yeung. Diagnosing and rectifying vision models using language. In ICLR, 2023. ^ref-35

[36] Y. Zhang, E. Sui, and S. Yeung-Levy. Connect, collapse, corrupt: Learning cross-modal tasks with uni-modal data. In ICLR, 2024. ^ref-36
