# Mixed Modality Search のための Modality Gap の解消

Binxu Li ⋆ Yuhui Zhang ⋆,† Xiaohan Wang Weixin Liang  
Ludwig Schmidt Serena Yeung-Levy  
Stanford University

###### 要旨

Mixed modality search—すなわち、画像、テキスト、そしてマルチモーダル文書からなる異種コーパスを横断して情報を検索する問題—は、重要でありながら十分に探究されていない実世界応用である。本研究では、CLIP をはじめとする contrastive vision-language models が mixed modality search タスクにおいてどのように機能するかを調べる。分析の結果、これらのモデルには埋め込み空間に顕著な modality gap が存在し、画像埋め込みとテキスト埋め込みが別個のクラスターを形成するため、モダリティ内ランキングの偏りとモダリティ間融合の失敗を引き起こすことが明らかになった。この問題に対処するため、我々は GR-CLIP を提案する。これは CLIP の埋め込み空間における modality gap を除去する軽量な post-hoc calibration 手法である。mixed modality search のために特別に設計された最初のベンチマークである MixBench で評価したところ、GR-CLIP は CLIP に比べて NDCG@10 を最大 26 ポイント改善し、最新の vision-language generative embedding models を 4 ポイント上回りつつ、計算量は 75$\times$ 低い。

## 1 はじめに

デジタル世界の情報は、テキスト、画像、動画、音声、そしてそれらの様々な組み合わせといった複数のモダリティにまたがって存在する。従来の検索システムは主として、同質なコーパス内での検索、すなわち text-to-text や text-to-image retrieval に焦点を当ててきた ( {{CITE:26}} ; {{CITE:13}} ; {{CITE:15}} ; {{CITE:25}} ) が、実世界の応用では、異種モダリティを横断して関連コンテンツを検索・取得する能力がますます求められている（例: text-to-{text, image, or both} retrieval） {{CITE:29}} 。例えば、ユーザが "Mountain Fuji" を検索した場合、山を記述するテキスト文書、単独の画像、ならびに両モダリティを組み合わせたマルチモーダルなウェブページを見つけたいと期待するであろう（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) a）。

その実用的重要性にもかかわらず、mixed modality search の課題は依然として十分に探究されていない {{CITE:29}} 。中心的な課題は、モダリティをまたいで意味的に類似したコンテンツ—たとえば、画像と "Mountain Fuji" のテキスト記述—を近接した位置に写像できる統一埋め込み空間を構築することにある。これにより、クエリと文書のモダリティに依存せず、その意味的類似度を正確に測定できる。近年の multimodal contrastive learning、特に CLIP-based models（ {{CITE:25}} ; {{CITE:33}} ; {{CITE:34}} ）の進展は、大規模な画像・テキスト対データセットで学習することにより、テキスト埋め込みと画像埋め込みを整列させる有望な解決策を提供している。

本研究では、これらの contrastive models が現実的な mixed modality search シナリオでどの程度機能するかを検討する。具体的には、CLIP は vision と language の2つの分離された encoder から構成される {{CITE:25}} 。各コーパス項目について、画像のみ・テキストのみの文書はそれぞれ対応する encoder により埋め込む。画像とテキストの両方を含むマルチモーダル文書については、画像埋め込みとテキスト埋め込みの線形結合によってそれらを表現する（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) b）。埋め込みが得られた後、クエリ埋め込みと各コーパス項目の cosine similarity を計算して類似度検索を行い、関連度に基づく上位10件の結果の品質を測る NDCG@10 {{CITE:11}} などの標準的な retrieval metrics により性能を評価する。

我々の分析は、CLIP 系 contrastive models の根本的制約を明らかにする。すなわち、埋め込み空間において顕著な modality gap（ {{CITE:17}} ; {{CITE:35}} ; {{CITE:36}} ）を示し、その結果、mixed modality 設定での検索性能が大きく低下するのである。これらのモデルは image-text pair を整列させるよう学習されているにもかかわらず、画像埋め込みとテキスト埋め込みは別個のクラスターを形成し、埋め込み空間内で大きく離れている（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) c）。このクラスタリングは強い intra-modal ranking bias を生み出し（§ [3](https://arxiv.org/html/2507.19054v1#S3) ）、同一モダリティ間（例: image-to-image や text-to-text）の類似度が、モダリティ間（例: image-to-text）の類似度より大幅に高くなり、検索順位を歪める（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) d）。例えば、テキストクエリ "Mountain Fuji" が与えられたとき、Mountain Fuji を描写した画像が、"this is a great paper." のような無関係なテキスト断片よりも下位に順位付けされることがある。加えて、modality gap は inter-modal fusion を損なう（§ [4](https://arxiv.org/html/2507.19054v1#S4) ）: 画像埋め込みとテキスト埋め込みを線形補間で結合すると、特徴がしばしば最適とは言えない領域へ押しやられ、意味表現が弱まり、画像またはテキスト単独を用いる場合よりも性能が低下する。

Figure 1: mixed modality search の概要。(a) 問題設定: mixed modality search は、マルチモーダル文書を含む異種コーパスから関連情報を検索することを目的とする。これは、クエリと文書の双方を埋め込み、その後に類似度に基づく retrieval を行うことで実現される。(b) 埋め込み手法: 単モダリティ文書は CLIP のモダリティ特化 encoder を用いて埋め込まれ、マルチモーダル文書は画像特徴とテキスト特徴の重み付き融合によって埋め込まれる。(c) Modality Gap: CLIP の埋め込み空間には modality gap が存在し、各モダリティの埋め込みは別個のクラスターを形成し、モダリティ間で大きく分離している。(d) モダリティ間の cosine similarity: この modality gap のため、クエリと同じモダリティを共有する文書はより高い cosine similarity を持ちやすく、上位に順位付けされるため、系統的なランキング偏りが導入される。(e) MixBench における性能: mixed modality search タスクのために新たに作成した MixBench ベンチマーク上で、modality gap を解消する軽量な post-hoc calibration 手法 GR-CLIP は、性能を大幅に改善し、はるかに低い計算コストで最先端の VLM2Vec ( vlm2vec , ) ベースラインを上回る。

![](assets/fig01.png)

modality gap に起因するランキング偏りと融合失敗に対処するため、我々は GR-CLIP を導入する。これは CLIP の埋め込み空間における modality gap を除去する軽量な post-hoc calibration 手法である（GR は gap-removed を意味する）。先行研究 {{CITE:35}} ; {{CITE:36}} は、CLIP 類似モデルにおける modality gap が、画像埋め込み部分空間とテキスト埋め込み部分空間に直交する定数ベクトルで近似できることを示している。この理論に基づき、我々は全画像データと全テキストデータの平均埋め込みを計算し、その差分を用いて modality gap を推定し、検索を行う前にこのベクトルをすべての埋め込みから差し引く。この手法は、平均埋め込みを計算するためにデータセットを一度走査するだけでよく、計算オーバーヘッドは無視できる程度である。

4つのサブセット（Google-WIT ( {{CITE:27}} ) , MSCOCO ( {{CITE:18}} ) , OVEN ( {{CITE:10}} ) , VisualNews ( {{CITE:19}} ) ）からなる mixed modality search 用のベンチマーク MixBench において評価すると、GR-CLIP は元の CLIP models を一貫して上回り、NDCG@10 を最大 26 ポイント改善した。また、VLM2Vec {{CITE:12}} のような近年の vision-language generative embedding methods を 4 ポイント上回りつつ、計算コストを 75$\times$ 削減した。さらに、本手法が異なる CLIP variants（例: OpenAI CLIP ( {{CITE:25}} ) , OpenCLIP ( {{CITE:33}} ) , SigLIP ( {{CITE:34}} ) ）および異なるモダリティ（例: text-to-image, text-to-audio, text-to-video）にまたがって一般化することを示す。

要するに、我々は mixed modality search の問題を定式化し、これを研究した。これは、ユーザが多様なモダリティ種別を含む異種コーパスを検索する web search engine などの実世界シナリオを反映している。最先端の contrastive models は modality gap に起因するランキング偏りと融合失敗に悩まされることを示し、この問題に対処する軽量な post-hoc calibration 手法を提案した。我々の知見は、効果的な mixed modality search のためには、真に統一された埋め込み空間を構築することの重要性を浮き彫りにしている。

## 2 前提知識

本節では、mixed modality search タスクを定義し、その課題と課題に関連する3つの設定を導入し、さらに使用する手法と評価指標を述べる。

### 2.1 問題設定

Mixed modality search は、クエリと文書が text、image、audio、video など異なるモダリティの組合せから構成されうるときに、意味的に関連するコンテンツを検索することを目的とする。$\mathcal{M}$ をサポートされるモダリティの集合とする（例: $\mathcal{M}=\{\text{text},\text{image},\text{audio},\text{video}\}$）。クエリは $q$ で表し、そのモダリティ集合を $m_{q}\subseteq\mathcal{M}$ とする。検索コーパスは $\mathcal{C}=\{d_{i}\}_{i=1}^{N}$ と定義され、各文書 $d_{i}$ はモダリティ集合 $m_{i}\subseteq\mathcal{M}$ を伴う。目的は、クエリと文書のモダリティの分布にかかわらず、各文書について類似度スコア $s(q,d_{i})$ を計算し、意味的関連性に基づく順位付きリストを返すことである。

Mixed modality search は、従来の retrieval タスクとは2つの性質によって区別される。1) 異種コーパス: 文書ごとにモダリティ構成が異なる。すなわち、$m_{i}\neq m_{j}$ となる $d_{i},d_{j}\in\mathcal{C}$ が存在する。たとえば、ある文書はテキストのみ ($m_{i}=\{\text{text}\}$)、別の文書は画像のみ ($m_{j}=\{\text{image}\}$)、さらに別の文書はマルチモーダル ($m_{k}=\{\text{text},\text{image}\}$) である。b) マルチモーダル文書: 一部の文書は1つのエントリ内に複数のモダリティを含む、すなわち $|m_{i}|&gt;1$ である。これらのモダリティはしばしば補完的な情報を提供し、効果的な理解のためには融合が必要となる（例: 説明的なキャプションを伴う画像）。

### 2.2 設定

異種コーパスとマルチモーダル文書の組合せは、2つの中心的なモデリング課題を生む。1) cross-modal alignment: 似た概念の表現が異なるモダリティ間で比較可能であることを保証すること。たとえば、"Mount Fuji" のテキストと画像は表現空間内で近接した位置に埋め込まれるべきである。2) multimodal fusion: 文書内の複数モダリティを効果的に統合し、統一された意味的に有意味な表現を形成すること。たとえば、"Mount Fuji" のテキストと画像を統合して、概念のより豊かな表現を生成することである。これらの課題を体系的に調べるため、我々は次の3つの設定を定義する。

Ablated setting 1: 異種コーパスのみ (§ [3](https://arxiv.org/html/2507.19054v1#S3) )。各文書は単モダリティ ($|m_{i}|=1$) であるが、コーパスは複数モダリティにまたがる ($|\mathcal{M}|&gt;1$) 。例えば、Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) a の $d_{1}$ と $d_{2}$ に対応するように、同じ概念についてのテキストのみ・画像のみの記述を含みうる。この設定では cross-modal alignment のみを評価する。すなわち、モデルがモダリティをまたいで比較可能な表現を符号化できるかどうかを検証する。

Ablated setting 2: マルチモーダル文書のみ (§ [4](https://arxiv.org/html/2507.19054v1#S4) )。すべての文書が同一のモダリティ集合を含む ($m_{i}=\mathcal{M}$ かつ $|m_{i}|&gt;1$) 。例えば、各文書が画像と対応するキャプションの両方を含み、Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) a の $d_{3}$ に対応する。この設定は純粋に multimodal fusion に焦点を当てる。すなわち、モデルが複数モダリティを効果的に組み合わせられるかを評価する。

フル設定：mixed modality search (§ [5](https://arxiv.org/html/2507.19054v1#S5) )。文書は単一モダリティまたはマルチモダリティのいずれかであり（$|m_{i}|\geq 1$）、コーパスは異種混在である。たとえば、一部の文書はテキストのみ、他は画像のみ、さらに別のものはその組合せであり、Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) a における $d_{1}$、$d_{2}$、$d_{3}$ がすべて存在する場合に対応する。これは最も現実的かつ一般的な設定であり、ニュース記事、商品リスティング、科学データセットのような実世界のコーパスを反映している。これは両方の中心的課題を統合したものであり、本研究の主要な評価シナリオである。

### 2.3 Methods

与えられたクエリ $q$ と文書 $d_{i}$ に対し、埋め込みモデル $f$ を用いてそれらの埋め込み $e_{q}=f(q)$ および $e_{i}=f(d_{i})$ を計算し、コサイン類似度 $s(q,d_{i})=\frac{e_{q}\cdot e_{i}}{\|e_{q}\|\cdot\|e_{i}\|}$ により文書を順位付けする。以下の埋め込み手法を評価する。

CLIP (baseline) {{CITE:25}} . CLIP は、対応する画像-テキスト入力の整列を学習する対照的 vision-language model である。画像エンコーダ $f^{I}$ とテキストエンコーダ $f^{T}$ を用いて各モダリティを別々に符号化する。単一モダリティのテキスト文書または画像文書 $d_{i}$ および $d_{j}$ に対しては、モダリティ固有のエンコーダを用いて埋め込みを計算する：$e_{i}=f^{I}(d_{i})$ および $e_{j}=f^{T}(d_{j})$。画像入力とテキスト入力 $d_{k}^{I}$ および $d_{k}^{T}$ を持つマルチモダリティ文書 $d_{k}$ に対しては、重み付き補間を計算する：$e_{k}=\alpha\cdot f^{T}(d_{k}^{T})+(1-\alpha)\cdot f^{I}(d_{k}^{I})$。ここで $\alpha\in[0,1]$ は各モダリティの寄与を調整する。

VLM2Vec (baseline) {{CITE:12}} . VLM2Vec は、large vision-language models $f$（例：LLaVA ( {{CITE:21}} ) , Qwen-VL ( {{CITE:1}} ) ）を自己回帰的に文書埋め込みへ適応させる最先端の multimodal generative embedding 手法である。各文書 $d_{i}$ は、テキスト入力と画像入力を組み合わせた instruction-style prompt $p_{i}$（例："Generate the embedding for the document: [image tokens] [text tokens]" ）として整形され、その後自己回帰的に処理される。最終デコーダ層からのプール表現を埋め込み $e_{i}=f(p_{i})$ として用いる。この手法は、二つのモダリティの joint modeling と instruction tuning を通じて高レベルの意味的整合を捉える。

GR-CLIP (ours). CLIP の目的はモダリティの整列であるにもかかわらず、先行研究はその埋め込み空間に persistent modality gap が存在することを示している。すなわち、画像埋め込みとテキスト埋め込みは別個のクラスタを形成し、依然として離れている {{CITE:17}} 。対となる画像-テキスト埋め込み $e_{i}^{T}$ と $e_{i}^{I}$ が与えられたとき、その関係は $e_{i}^{T}-e_{i}^{I}\approx c_{\perp}$ とモデル化できる。ここで $c_{\perp}$ は共有埋め込み部分空間に直交する定数ベクトルであり、modality gap を表す {{CITE:36}} 。GR-CLIP（GR は gap-removed の意）は、モダリティ固有の平均を差し引くことでこの gap を除去する軽量な post-hoc calibration 手法である：$e_{i}^{\prime T}=e_{i}^{T}-\mathbb{E}_{i}[e_{i}^{T}],e_{i}^{\prime I}=e_{i}^{I}-\mathbb{E}_{i}[e_{i}^{I}]$。この zero-centering により modality gap は除去される {{CITE:36}} 。なぜなら、$e_{i}^{\prime T}-e_{i}^{\prime I}=(e_{i}^{T}-e_{i}^{I})-(\mathbb{E}_{i}[e_{i}^{T}]-\mathbb{E}_{i}[e_{i}^{I}])\approx c_{\perp}-c_{\perp}=0$ となり、推論コストをほとんど増やすことなく cross-modal alignment が改善されるからである。マルチモダリティ文書については、補正後の埋め込みに対して同じ補間を適用する。Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) b にこの過程を示す。実際には、この単純な calibration が CLIP の性能を大きく向上させ、計算量を大幅に抑えつつ VLM2Vec を上回ることを確認した。

### 2.4 Evaluation Metrics

検索性能の評価には NDCG@10 (Normalized Discounted Cumulative Gain {{CITE:11}} ) を用いる。これは上位10件の検索文書に対する関連性と順位の両方を反映する広く用いられる指標である。NDCG@10 の値が高いほど性能が良いことを示す。詳細は Appendix に記す。

## 3 Retrieval with Heterogeneous Corpus

Figure 2: Retrieval with a heterogeneous corpus. (a) Dataset Construction: We construct a heterogeneous corpus by randomly replacing text documents with either screenshot renderings of the text or paired images with probability $p$. Since the semantic content remains unchanged, a retrieval system with perfect cross-modal alignment should maintain the same performance regardless of $p$. (b) Initial Results &amp; Simulation: Surprisingly, CLIP exhibits a U-shaped performance curve as text is replaced with screenshots. We attribute this behavior to the modality gap in CLIP's embedding space. A simulation experiment that artificially penalizes cross-modal documents reproduces the same U-shaped trend, confirming our hypothesis. (c) Method - GR-CLIP: Building on prior work, we propose GR-CLIP , a simple post-hoc calibration that removes the modality gap via mean-centering of text and image embeddings. (d) Improved Results: GR-CLIP flattens the U-shaped curve and significantly improves retrieval accuracy, achieving comparable or better performance than the VLM2Vec baseline with far less compute. (e) Generalization Across Models, Datasets, and Modalities: To evaluate generalization, we test GR-CLIP across three CLIP variants, three additional datasets, and three other modalities (detailed in the Appendix). In all cases, the findings and improvements hold consistently.

![](assets/fig02.png)

§ [2](https://arxiv.org/html/2507.19054v1#S2) で論じたように、我々は mixed modality search の ablated setting から出発する。すなわち、単一モダリティ文書（例：テキストのみ、または画像のみ；Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) a を参照）から構成される異種混在コーパスである。この設定は、検索モデルが cross-modal alignment という課題に効果的に対処できるかを評価するものである。

### 3.1 Dataset Construction

この設定に従う既存データセットは存在しないため、本課題に特化した新たなデータセットを、合成スクリーンショットと画像置換という二つの相補的戦略を用いて構築する。

Screenshot replacement. テキストのみの標準的な検索データセット、すなわちクエリもコーパス文書もいずれもテキストであるデータセットから出発し、テキスト文書を画像ベースのスクリーンショットとして合成的にレンダリングする。具体的には、各テキスト文書 $d_{i}^{T}$ に対して、同一内容を含むスクリーンショット版 $d_{i}^{I}$ を生成し、確率 $p$ でそれに置き換える（Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) a）。この合成設定は意味内容を完全に保存するため、制御された実験に理想的である。完璧な cross-modal alignment を持つモデルであれば、テキスト文書とスクリーンショット文書の対を埋め込み空間で同様に表現できるため、$p$ の値が変化しても検索性能は変わらないはずである。この変換を NFCorpus ( {{CITE:3}} ) および SciFact ( {{CITE:30}} ) の二つのデータセットに適用する。

Real image replacement. 画像-キャプション対を含むデータセットでは、テキストキャプション $d_{i}^{T}$ を対応する画像 $d_{i}^{I}$ に確率 $p$ で置き換える。この設定はより現実的である一方、モダリティ間にわずかな意味差を導入する。それでも、基礎となる意味的整合があるため、置換比率 $p$ が異なっても検索性能は安定していると期待される。この手法を用いて、Google WIT ( {{CITE:27}} ) , MSCOCO ( {{CITE:18}} ) の二つのデータセットを構築する。

### 3.2 Initial Results &amp; Simulation

まず、意味保存が厳密に成り立つ合成スクリーンショット設定に注目する。理想的には、完全な cross-modal alignment を持つモデルであれば、スクリーンショットに置換された文書数にかかわらず一貫した検索性能を示すはずである。

Models exhibit a U-shaped performance curve when mixing texts and screenshots. 驚くべきことに、期待される平坦な傾向ではなく、U字型の性能曲線（Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) b）を観測した。スクリーンショットがより多くのテキスト文書を置き換えるにつれて（$p$ が増加するにつれて）、性能は最初に低下し、$p=0$（全テキスト）で 0.22 から、$p=0.99$（99% がスクリーンショット）で 0.02 まで落ちる。しかし、$p=1$（全てスクリーンショット）では性能が再び 0.36 に改善し、$p$ の関数として明確な U字型を形成する。興味深いことに、CLIP は text-to-image retrieval（$p=1$）の方が text-to-text retrieval（$p=0$）よりも高性能である。これは、明示的に単一モダリティ検索を最適化していない、cross-modal contrastive loss に基づく学習目的によるものと考えられる。

The U-shape arises from the modality gap. 我々はこの U 字型の性能を modality gap に帰着させる。第一に、modality gap は intra-modal similarity のバイアスを誘起する。CLIP は共有空間でテキスト埋め込みと画像埋め込みを整列させるが、テキストと画像のクラスタは依然として分離しており（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) c）、その結果、モダリティ内類似度スコアが体系的に高くなる（Figure [1](https://arxiv.org/html/2507.19054v1#S1.F1) d）。第二に、このバイアスが順位の歪みを引き起こす。スクリーンショットがより多くのテキスト項目を置換するにつれて、関連するスクリーンショットは cross-modal similarity が低いために不利になり、一方で無関係なテキスト文書は単に intra-modal な整列のためだけに上位に来る可能性がある。$p=0.99$ では、残存するわずかなテキスト文書が関連性にかかわらず順位を支配する。$p=1$ では全文書が画像となり、モダリティバイアスが消失するため性能が改善し、結果として U 字型曲線が形成される。

Push-down simulation confirms the hypothesis. この説明を検証するため、すべてのスクリーンショットに固定の類似度スコア 0 を与えることで、modality-induced ranking bias をシミュレートし、実質的にそれらを順位リストの最下位へ押し下げる。得られた性能曲線（Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) b）は実際の CLIP 曲線と非常に近く一致し、U 字型が modality gap に起因する順位歪みによって生じるという仮説を支持する。

### 3.3 GR-CLIP with Improved Results

modality gap が性能低下を引き起こすのであれば、これを緩和することで性能を改善できる。

Closing the modality gap via mean-shift calibration. 先行研究が modality gap を埋め込み空間における mean shift と特徴づけていることに従い {{CITE:36}} 、我々は GR-CLIP という軽量な post-hoc calibration 手法を提案する。テキストおよび画像モダリティの平均埋め込みを計算し、それぞれの表現から差し引くことで、共有空間において両モダリティを中心化する。これによりモダリティ間の分離が低減される（Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) d；導出は § [2](https://arxiv.org/html/2507.19054v1#S2) を参照）。

Flattened curves and improved performance after removing the modality gap. GR-CLIP を適用した後、検索性能は大幅に向上し、U 字型曲線は異なる $p$ の値にわたって平坦化される（Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) e）。GR-CLIP はまた、近年の generative embedding 手法である VLM2Vec {{CITE:12}} を上回る。VLM2Vec は同程度に平坦な性能を示すが、75$\times$ 多くの計算資源を要する。これらの結果は、modality gap の低減が mixed modality retrieval において CLIP ベースモデルを改善するうえで、効率的かつ有効であることを示している。

### 3.4 Generalization across Models, Datasets, and Modalities

我々の知見の一般性を評価するため、GR-CLIP を異なるモデル、データセット、モダリティにわたって評価する。1) モデル間：Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) f（上段）に示すように、U 字型曲線は OpenAI CLIP {{CITE:25}} 、OpenCLIP {{CITE:33}} 、SigLIP {{CITE:34}} の三つの CLIP 変種において観測される。GR-CLIP は一貫して曲線を平坦化し、性能を改善する。2) データセット間：Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) f（中段）に示すように、本研究の知見は、合成スクリーンショット設定（NFCorpus ( {{CITE:3}} ) および SciFact ( {{CITE:30}} ) ）を超えて、実世界データセット（Google WIT ( {{CITE:27}} ) および MSCOCO ( {{CITE:18}} ) ）にも拡張される。3) モダリティ間。我々は text-to-video および text-to-audio retrieval への一般化も検証する。結果は Appendix に示す。

## 4 マルチモーダル文書を用いた検索

図3：マルチモーダル文書を用いた検索。(a) データセット構築：各文書は画像とテキストの両方を含み、埋め込みはモダリティ固有の特徴を融合して得られる。融合係数 $\alpha$ を変化させ、モデルがマルチモーダル情報を統合する能力を評価する。(b) 結果：GR-CLIP は3つのモデル変種および4つのデータセットにおいて一貫して CLIP を上回っており、モダリティギャップが有効なマルチモーダル融合を妨げること、ならびにそれを除去することで検索性能が大幅に向上することを示している。

![](assets/fig03.png)

ここでは、§ [3](https://arxiv.org/html/2507.19054v1#S3) に対する補完的なアブレーションを考える。そこでは検索コーパスは同質であるが、各文書はマルチモーダル、すなわち画像とテキストの両方のモダリティを含む（図 [3](https://arxiv.org/html/2507.19054v1#S4.F3) a）。この設定は、画像とテキストがいずれか単独のモダリティよりも豊かな意味的手がかりを提供すべき状況において、モデルがマルチモーダル情報を融合する能力を評価するものである。

### 4.1 データセット構築

各文書が画像成分とテキスト成分の両方を含む、4つの実世界マルチモーダルデータセットを用いる。OVEN ( {{CITE:10}} ) は、クエリからマルチモーダル文書への形式を採用した既存の検索ベンチマークである。MSCOCO ( {{CITE:18}} ) および VisualNews {{CITE:19}} では、各画像に1つ以上の短いキャプションが付与されている。そこで、短いキャプションのうち1つをランダムにサンプルしてクエリとし、画像とともに短いキャプションを条件として GPT により長いキャプションを生成し、それを文書として用いる。Google WIT ( {{CITE:27}} ) では、各画像にタイトル、短いキャプション、長いキャプションが付随する。ここでは、タイトルと短いキャプションの連結をクエリとし、画像と長いキャプションの組を文書とする。これらのデータセットは、自然に対応付けられた画像・テキストデータを含む多様なドメインにまたがっている。各文書は相補的な視覚的・言語的信号を提供するため、モダリティ融合の評価に適している。

### 4.2 結果

モダリティ融合がモダリティギャップによってどのように影響を受けるかを分析するため、融合埋め込みにおける各モダリティの寄与を制御する融合重み $\alpha\in[0,1]$ を変化させる。すなわち、$e_{i}=\alpha\cdot e_{i}^{T}+(1-\alpha)\cdot e_{i}^{I}$ である。

モダリティギャップは有効な融合を妨げる。図 [3](https://arxiv.org/html/2507.19054v1#S4.F3) b の青い曲線に示すように、元の CLIP 埋め込みでは、性能は通常いずれかの単一モダリティの端点（$\alpha=0$ または $\alpha=1$）で最大となり、中間の $\alpha$ における融合はこれらの単一モダリティベースラインを上回れない。これは、モダリティギャップがモダリティ間の有効な統合を妨げていることを示唆する。線形補間はしばしば融合特徴を埋め込み空間内の最適でない領域へ押し込み、意味的品質を低下させ、その結果、画像のみあるいはテキストのみを用いる場合よりも性能が悪化する。

モダリティギャップの解消後、融合は大幅に改善する。§ [3](https://arxiv.org/html/2507.19054v1#S3) で述べた平均シフト較正によりモダリティギャップを除去すると、融合は著しく有効になる。図 [3](https://arxiv.org/html/2507.19054v1#S4.F3) b の橙色の曲線に示すように、性能は中間の $\alpha$ で最大となり、両方の単一モダリティベースラインを上回る。これは、ギャップ除去済みモデルである GR-CLIP が、画像とテキストから得られる相補的情報を適切に統合し、より強力な全体表現を生成することを示している。

モデルおよびデータセットをまたぐ一般化。これらの知見は、OpenAI CLIP {{CITE:25}} 、OpenCLIP {{CITE:33}} 、SigLIP {{CITE:34}} を含む複数の CLIP 変種、および OVEN {{CITE:10}} 、VisualNews {{CITE:19}} 、Google WIT {{CITE:27}} 、MSCOCO {{CITE:18}} といった多様なデータセットにおいて一貫して成り立つ。いずれの場合も、モダリティギャップを除去することで融合品質が向上し、その結果として検索性能が改善される。

## 5 混合モダリティ検索

図4：混合モダリティ検索。(a) データセット構築：検索エンジンにとって最も現実的な設定を反映するため、コーパスが異質であり、マルチモーダル文書を含むベンチマーク MixBench を導入する。(b) 結果：4つの MixBench サブセットおよび5つの CLIP 変種において、GR-CLIP はモダリティギャップを除去することで元の CLIP モデルを大幅に上回り、計算コストを大きく抑えつつ最先端性能を達成する。

![](assets/fig04.png)

ここでは、§ [3](https://arxiv.org/html/2507.19054v1#S3) と § [4](https://arxiv.org/html/2507.19054v1#S4) の知見を統合し、さらに最も現実的なシナリオ、すなわち混合モダリティ検索へと分析を拡張する。ここでは、コーパス中の文書は純粋なテキスト、純粋な画像、あるいはその両方の組合せのいずれでもありうる（図 [4](https://arxiv.org/html/2507.19054v1#S5.F4) a）。この設定は、検索システムが異質で、可変的にマルチモーダルなコンテンツ全体を対象として動作しなければならない実世界の検索エンジンの課題を反映している。

### 5.1 MixBench：データセット構築

この現実的な設定における研究を支援するため、混合モダリティ検索専用に設計した新しいベンチマーク MixBench を導入する。MixBench は、4つの実世界マルチモーダルデータセット、すなわち OVEN ( {{CITE:10}} ) 、MSCOCO ( {{CITE:18}} ) 、Google WIT ( {{CITE:27}} ) 、VisualNews ( {{CITE:19}} ) から構築されており、これらは多様なドメインにまたがり、自然に対応付けられた画像・テキストコンテンツを含む。これらのデータセットをクエリ・文書検索形式へ変換する手順は § [4](https://arxiv.org/html/2507.19054v1#S4) に詳述する。MixBench では、文書は画像のみ、テキストのみ、あるいは画像・テキストのペアから構成されうる。バランスの取れた分布を確保するため、文書タイプ（純画像、純テキスト、マルチモーダル）を 1:1:1 の比率でサンプリングする。

### 5.2 結果

図 [4](https://arxiv.org/html/2507.19054v1#S5.F4) b は、元の CLIP 変種およびギャップ除去済み対応モデル（GR-CLIP）を用いた、4つの MixBench サブセットでの結果を示す。

GR-CLIP は、モダリティギャップを解消した後、元の CLIP に比べて大幅な改善を示す。先の知見と整合的に、平均シフト較正によってモダリティギャップを解消すると、CLIP {{CITE:25}} 、OpenCLIP {{CITE:33}} 、SigLIP {{CITE:34}} を含む、評価したすべてのモデルにおいて MixBench の性能が大きく向上する。これらの改善は、OVEN {{CITE:10}} 、VisualNews {{CITE:19}} 、Google WIT {{CITE:27}} 、MSCOCO {{CITE:18}} の4データセット全体に一般化される。平均すると、GR-CLIP は追加計算コストをほとんど伴わずに、NDCG@10 を最大 26 パーセントポイント向上させる。これらの利得は、§ [3](https://arxiv.org/html/2507.19054v1#S3) および § [4](https://arxiv.org/html/2507.19054v1#S4) で示した、クロスモーダル整合性とマルチモーダル融合の改善に起因しており、これらは混合モダリティ検索の性能にとって極めて重要である。

GR-CLIP は、計算量を大幅に抑えつつ最先端性能を達成する。特筆すべきことに、GR-CLIP は、75$\times$ も少ない計算資源しか用いていないにもかかわらず、有力な VLM2Vec ベースラインを上回る。唯一の例外は MSCOCO であり、論文で報告されているように、VLM2Vec はこれで訓練されている。これらの結果は、混合モダリティ検索のために真に共有された埋め込み空間を構築することの重要性を強調している。この能力は有効な検索システムにとって不可欠であるが、しばしば見落とされている。

## 6 関連研究

単一モダリティ検索およびクロスモーダル検索。単一モダリティ検索（例えば、テキスト対テキスト、画像対画像）およびクロスモーダル検索（例えば、テキスト対画像、画像対テキスト）は、先行研究で広く研究されてきた（ {{CITE:26}} ; {{CITE:13}} ; {{CITE:14}} ; {{CITE:15}} ; {{CITE:25}} ）ものであり、現在では Google や Bing といった多くの大規模検索エンジンを支えている。これらの設定における核心的課題は、クエリと文書の間の類似度を正確に比較できる有効な表現空間を構築することである。これに対し、本研究は、クエリと文書の双方が複数のモダリティにまたがりうる、より複雑な混合モダリティ検索設定に焦点を当てる {{CITE:29}} 。この設定は十分に未解明である一方で、非常に実用的である。そこでは、モダリティ境界をまたいで意味的類似性を意味のある形で測定できる共有表現空間を設計するという新たな課題が生じる。

マルチモーダル表現学習。マルチモーダル表現学習は、異なるモダリティからの情報を一貫した埋め込み空間へ統合することを長らく目指してきた。初期の研究では early fusion および late fusion 技術が検討された {{CITE:24}} ; {{CITE:28}} ; {{CITE:16}} ; {{CITE:22}} ; {{CITE:5}} 。近年では、マルチモーダル対照学習が強力な枠組みとして登場し、対照目的関数を通じて対応する画像・テキスト表現を整列させている（ {{CITE:9}} ; {{CITE:25}} ; {{CITE:34}} ; {{CITE:33}} ）。CLIP {{CITE:25}} のように、数百万の対応例で学習されたモデルは、モダリティ間で意味的に整合した埋め込みを学習する顕著な能力を示してきた。さらに近年では、生成的 vision-language models (VLMs) を検索へ適用する試みが注目を集めており {{CITE:12}} ; {{CITE:7}} 、それらを埋め込みモデルとして再利用することが進められている {{CITE:2}} ; {{CITE:23}} 。これらのモデルはより柔軟で、多様なマルチモーダル入力を扱う能力に優れるが、しばしば大幅に多くの計算を要する。本研究では、CLIP {{CITE:25}} と VLM2Vec {{CITE:12}} の両パラダイムを、混合モダリティ検索設定の下で評価する。驚くべきことに、CLIP に適用した単純な較正手法が、はるかに少ない計算量にもかかわらず VLM2Vec を上回りうることを見出した。

マルチモーダル対照学習におけるモダリティギャップ。近年の研究（ {{CITE:17}} ; {{CITE:36}} ; {{CITE:35}} ）は、対照的マルチモーダル埋め込み空間に持続的なモダリティギャップが存在することを明らかにした。すなわち、対照学習がそれらを整列させるよう設計されているにもかかわらず、画像埋め込みとテキスト埋め込みは別々にクラスターを形成しがちである。このギャップは、モデル初期化と対照最適化の組合せに起因するとされる。理論的には、モダリティギャップは、画像およびテキストの両部分空間にほぼ直交する定数オフセットベクトルとして特徴付けられている {{CITE:36}} ; {{CITE:35}} 。この知見に基づき、本研究では単純でありながら有効な mean-reduction 較正を採用する。これは、類似度を計算する前に埋め込みからモダリティ固有の平均を除去するものである。この軽量な事後処理によりモダリティギャップが除去され、混合モダリティ検索設定において大幅な性能向上が得られる。

## 7 結論

本研究は、実用的であるにもかかわらず十分に未解明であった混合モダリティ検索の問題を扱った。これは、クエリがマルチモーダル文書を含む異質なコーパスから意味的に関連するコンテンツを検索しなければならない設定である。我々はこの設定における CLIP ベースモデルの挙動を分析し、重要な制約を特定した。すなわち、埋め込み空間におけるモダリティギャップが、クロスモーダル整合性とマルチモーダル融合の双方を妨げているという点である。これに対処するため、モダリティギャップを除去し検索性能を大幅に向上させる、単純でありながら有効な手法 GR-CLIP を導入した。本研究の結果は、信頼性が高く効率的な混合モダリティ検索のためには、真に統一されたマルチモーダル表現が重要であることを示している。

## 謝辞

本研究の一部は Hoffman-Yee Research Grants の支援を受けた。S.Y. は Chan Zuckerberg Biohub - San Francisco の Investigator である。

## References

{{BIBSTART:1}}- [1] J. Bai, S. Bai, S. Yang, S. Wang, S. Tan, P. Wang, J. Lin, C. Zhou, and J. Zhou. Qwen-vl: A versatile vision-language model for understanding, localization, text reading, and beyond. arXiv preprint arXiv:2308.12966 , 2023.
{{BIBSTART:2}}- [2] P. BehnamGhader, V. Adlakha, M. Mosbach, D. Bahdanau, N. Chapados, and S. Reddy. Llm2vec: Large language models are secretly powerful text encoders. arXiv preprint arXiv:2404.05961 , 2024.
{{BIBSTART:3}}- [3] V. Boteva, D. Gholipour, A. Sokolov, and S. Riezler. A full-text learning to rank dataset for medical information retrieval. 2016.
{{BIBSTART:4}}- [4] D. Chen and W. Dolan. Collecting highly parallel data for paraphrase evaluation. In ACL , 2011.
{{BIBSTART:5}}- [5] Y.-C. Chen, L. Li, L. Yu, A. El Kholy, F. Ahmed, Z. Gan, Y. Cheng, and J. Liu. Uniter: Universal image-text representation learning. In ECCV , 2020.
{{BIBSTART:6}}- [6] K. Drossos, S. Lipping, and T. Virtanen. Clotho: An audio captioning dataset. In ICASSP , pages 736-740. IEEE, 2020.
{{BIBSTART:7}}- [7] M. Faysse, H. Sibille, T. Wu, B. Omrani, G. Viaud, C. HUDELOT, and P. Colombo. Colpali: Efficient document retrieval with vision language models. In ICLR , 2025.
{{BIBSTART:8}}- [8] S. Fu, N. Y. Tamir, S. Sundaram, L. Chai, R. Zhang, T. Dekel, and P. Isola. Dreamsim: Learning new dimensions of human visual similarity using synthetic data. In NeurIPS , 2023.
{{BIBSTART:9}}- [9] R. Girdhar, A. El-Nouby, Z. Liu, M. Singh, K. V. Alwala, A. Joulin, and I. Misra. Imagebind: One embedding space to bind them all. In CVPR , 2023.
{{BIBSTART:10}}- [10] H. Hu, Y. Luan, Y. Chen, U. Khandelwal, M. Joshi, K. Lee, K. Toutanova, and M.-W. Chang. Open-domain visual entity recognition: Towards recognizing millions of wikipedia entities. In ICCV , 2023.
{{BIBSTART:11}}- [11] K. Järvelin and J. Kekäläinen. Cumulated gain-based evaluation of ir techniques. TOIS , 2002.
{{BIBSTART:12}}- [12] Z. Jiang, R. Meng, X. Yang, S. Yavuz, Y. Zhou, and W. Chen. VLM2vec: Training vision-language models for massive multimodal embedding tasks. In ICLR , 2025.
{{BIBSTART:13}}- [13] V. Karpukhin, B. Oguz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W.-t. Yih. Dense passage retrieval for open-domain question answering. In EMNLP , 2020.
{{BIBSTART:14}}- [14] O. Khattab and M. Zaharia. Colbert: Efficient and effective passage search via contextualized late interaction over bert. In SIGIR , 2020.
{{BIBSTART:15}}- [15] K.-H. Lee, X. Chen, G. Hua, H. Hu, and X. He. Stacked cross attention for image-text matching. In ECCV , 2018.
{{BIBSTART:16}}- [16] L. H. Li, M. Yatskar, D. Yin, C.-J. Hsieh, and K.-W. Chang. Visualbert: A simple and performant baseline for vision and language. arXiv preprint arXiv:1908.03557 , 2019.
{{BIBSTART:17}}- [17] V. W. Liang, Y. Zhang, Y. Kwon, S. Yeung, and J. Y. Zou. Mind the gap: Understanding the modality gap in multi-modal contrastive representation learning. In NeurIPS , 2022.
{{BIBSTART:18}}- [18] T.-Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Dollár, and C. L. Zitnick. Microsoft coco: Common objects in context. In ECCV , 2014.
{{BIBSTART:19}}- [19] F. Liu, Y. Wang, T. Wang, and V. Ordonez. Visual news: Benchmark and challenges in news image captioning. In NeurIPS , 2021.
{{BIBSTART:20}}- [20] H. Liu, C. Li, Y. Li, B. Li, Y. Zhang, S. Shen, and Y. J. Lee. Llava-next: Improved reasoning, ocr, and world knowledge, January 2024.
{{BIBSTART:21}}- [21] H. Liu, C. Li, Q. Wu, and Y. J. Lee. Visual instruction tuning. In NeurIPS , 2023.
{{BIBSTART:22}}- [22] J. Lu, D. Batra, D. Parikh, and S. Lee. Vilbert: Pretraining task-agnostic visiolinguistic representations for vision-and-language tasks. In NeurIPS , 2019.
{{BIBSTART:23}}- [23] N. Muennighoff, S. Hongjin, L. Wang, N. Yang, F. Wei, T. Yu, A. Singh, and D. Kiela. Generative representational instruction tuning. In ICLR 2024 Workshop , 2024.
{{BIBSTART:24}}- [24] J. Ngiam, A. Khosla, M. Kim, J. Nam, H. Lee, A. Y. Ng, et al. Multimodal deep learning. In ICML , 2011.
{{BIBSTART:25}}- [25] A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal, G. Sastry, A. Askell, P. Mishkin, J. Clark, G. Krueger, and I. Sutskever. Learning transferable visual models from natural language supervision. In ICML , 2021.
{{BIBSTART:26}}- [26] S. Robertson, H. Zaragoza, et al. The probabilistic relevance framework: Bm25 and beyond. Foundations and Trends® in Information Retrieval , 2009.
{{BIBSTART:27}}- [27] K. Srinivasan, K. Raman, J. Chen, M. Bendersky, and M. Najork. Wit: Wikipedia-based image text dataset for multimodal multilingual machine learning. In SIGIR , 2021.
{{BIBSTART:28}}- [28] N. Srivastava and R. R. Salakhutdinov. Multimodal learning with deep boltzmann machines. In NIPS , 2012.
{{BIBSTART:29}}- [29] Voyage AI. voyage-multimodal-3: all-in-one embedding model for interleaved text, images, and screenshots. Blog post, Nov. 2024.
{{BIBSTART:30}}- [30] D. Wadden, S. Lin, K. Lo, L. L. Wang, M. van Zuylen, A. Cohan, and H. Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP , 2020.
{{BIBSTART:31}}- [31] Y. Wang, K. Li, Y. Li, Y. He, B. Huang, Z. Zhao, H. Zhang, J. Xu, Y. Liu, Z. Wang, et al. Internvideo: General video foundation models via generative and discriminative learning. arXiv preprint arXiv:2212.03191 , 2022.
{{BIBSTART:32}}- [32] Y. Wu*, K. Chen*, T. Zhang*, Y. Hui*, T. Berg-Kirkpatrick, and S. Dubnov. Large-scale contrastive language-audio pretraining with feature fusion and keyword-to-caption augmentation. In ICASSP , 2023.
{{BIBSTART:33}}- [33] H. Xu, S. Xie, X. Tan, P.-Y. Huang, R. Howes, V. Sharma, S.-W. Li, G. Ghosh, L. Zettlemoyer, and C. Feichtenhofer. Demystifying CLIP data. In ICLR , 2024.
{{BIBSTART:34}}- [34] X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer. Sigmoid loss for language image pre-training. In ICCV , 2023.
{{BIBSTART:35}}- [35] Y. Zhang, J. Z. HaoChen, S.-C. Huang, K.-C. Wang, J. Zou, and S. Yeung. Diagnosing and rectifying vision models using language. In ICLR , 2023.
{{BIBSTART:36}}- [36] Y. Zhang, E. Sui, and S. Yeung-Levy. Connect, collapse, corrupt: Learning cross-modal tasks with uni-modal data. In ICLR , 2024.

## Limitations

While our work demonstrates that removing the modality gap enables GR-CLIP to achieve substantial performance gains in the mixed modality search setting across diverse datasets, model variants, and modalities, several limitations remain, highlighting valuable directions for future research. First, although we consider a realistic scenario in which documents include both image and text modalities, each document is restricted to a single image and a single text segment. Extending the evaluation to more complex, interleaved multi-image and multi-text documents-such as web pages or scientific articles-could provide a more rigorous and comprehensive assessment. Second, although GR-CLIP outperforms the generative embedding model VLM2Vec while requiring significantly less computation, it builds on CLIP, which does not model fine-grained modality interaction, and may miss opportunities for deeper cross-modal integration that generative embedding models can capture. Given this, investigating the causes of the modality gap in generative embedding models such as VLM2Vec and developing methods to reduce it presents an important and underexplored research direction toward more powerful and unified multimodal representations. Nonetheless, our work takes an important first step in defining and addressing the problem of mixed modality search in realistic settings, highlighting the importance of constructing truly unified embedding spaces for effective retrieval and laying a foundation for future advances in this emerging area.

## Code Availability

All code is available at an anonymous GitHub repository, which reproduces all experiments in the paper: [https://github.com/yuhui-zh15/MixedModalitySearch/](https://github.com/yuhui-zh15/MixedModalitySearch/) .

## Data Availability

All datasets used in this study are hosted anonymously on Hugging Face to facilitate future research in this emerging area: [https://huggingface.co/datasets/mixed-modality-search/MixBench2025](https://huggingface.co/datasets/mixed-modality-search/MixBench2025) .

## Compute Resource

All experiments were conducted using a single NVIDIA A100 GPU with 40GB of memory. All experiments are inference-only and require minimal computational resources.

## Overview

We provide an overview of the Appendix below:

- • § [A](https://arxiv.org/html/2507.19054v1#A1) presents additional generalization results across modalities and evaluation metrics.
- • § [B](https://arxiv.org/html/2507.19054v1#A2) details the methods and includes pseudo-code for reproducibility.
- • § [C](https://arxiv.org/html/2507.19054v1#A3) describes the details of the models used.
- • § [D](https://arxiv.org/html/2507.19054v1#A4) explains the evaluation metrics, including NDCG.
- • § [E](https://arxiv.org/html/2507.19054v1#A5) outlines the datasets used and the associated preprocessing steps.
- • § [F](https://arxiv.org/html/2507.19054v1#A6) includes case studies comparing CLIP and GR-CLIP on MixBench.

## Appendix A Generalization across Modalities and Metrics

In the main paper, we show that closing the modality gap significantly improves mixed modality search performance for image-text data, using NDCG@10 as the evaluation metric. Here, we provide additional results to demonstrate: (1) the generalization of our method to modalities beyond image and text, and (2) the robustness of our conclusions under alternative evaluation metrics.

### A.1 Generalization across Modalities

Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) e in the main paper presents results for the image-text modality. In Figure [5](https://arxiv.org/html/2507.19054v1#A1.F5) , we extend this analysis to additional modality pairs. Specifically, we report retrieval performance (NDCG@10) for video-text (ViCLIP ( [viclip ,](https://arxiv.org/html/2507.19054v1#bib.bib31) ) on the MSVD dataset), audio-text (CLAP ( [clasp ,](https://arxiv.org/html/2507.19054v1#bib.bib32) ) on the Clotho ( [clotho ,](https://arxiv.org/html/2507.19054v1#bib.bib6) ) dataset), and an additional image-text setting (OpenAI CLIP ( [clip ,](https://arxiv.org/html/2507.19054v1#bib.bib25) ) on the Nights ( [nights ,](https://arxiv.org/html/2507.19054v1#bib.bib8) ) dataset). Across all cases, we observe a consistent U-shaped curve in the original CLIP-based results, which becomes significantly flatter after applying GR-CLIP to remove the modality gap. This trend closely mirrors the behavior observed in the image-text and screenshot experiments in Figure [2](https://arxiv.org/html/2507.19054v1#S3.F2) e, providing strong evidence of the modality gap's impact and the broad applicability of our method across diverse modalities.

Figure 5: Generalization across modalities. GR-CLIP consistently mitigates the U-shaped curve caused by the modality gap and significantly improves performance, demonstrating strong generalizability across diverse modality pairs.

![](assets/fig05.png)

### A.2 Generalization across Metrics

In the main paper, we adopt NDCG@10 as the primary evaluation metric. To further assess the robustness of GR-CLIP, we extend our analysis to additional metrics, including NDCG@100 and Recall@1. Table [1](https://arxiv.org/html/2507.19054v1#A1.T1) reports results on MixBench across all three metrics, demonstrating that the improvements observed with GR-CLIP are consistent regardless of the evaluation criterion. Figure [6](https://arxiv.org/html/2507.19054v1#A1.F6) and Figure [7](https://arxiv.org/html/2507.19054v1#A1.F7) further extend the analysis in § [3](https://arxiv.org/html/2507.19054v1#S3) and § [4](https://arxiv.org/html/2507.19054v1#S4) using NDCG@100 and Recall@1, respectively, and similarly confirm the consistency of our findings.

Figure 6: Reproduction of Figure 2 in the main paper using NDCG@100 as the evaluation metric.

![](assets/fig06.png)

Figure 7: Reproduction of Figure 3 in the main paper using NDCG@100 and Recall@1 as evaluation metrics.

![](assets/fig07.png)

## Appendix B Details of Methods

As introduced in § [2.3](https://arxiv.org/html/2507.19054v1#S2.SS3) , GR-CLIP mitigates the modality gap by subtracting global mean vectors for each modality. Specifically, we compute three mean vectors: the query mean $\bar{e}_{q}$, the document text mean $\bar{e}^{T}$, and the document image mean $\bar{e}^{I}$:

|    | $$\bar{e}_{q}=\mathbb{E}_{q\sim\mathcal{Q}}[f^{T}(q)],\quad\bar{e}^{T}=\mathbb{E}_{d^{T}\sim\mathcal{D}_{\text{text}}}[f^{T}(d^{T})],\quad\bar{e}^{I}=\mathbb{E}_{d^{I}\sim\mathcal{D}_{\text{image}}}[f^{I}(d^{I})].$$   |    | (1)   |
|----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----|-------|

We distinguish the query mean $\bar{e}_{q}$ from the text document mean $\bar{e}^{T}$ to account for structural and semantic differences: queries are often short and interrogative, whereas documents are typically longer and descriptive. This distinction is crucial for reducing alignment bias and improving retrieval performance.

To ensure generalization across datasets and prevent test-set leakage, we compute unified mean vectors from the training sets of multiple datasets, rather than estimating separate means for each dataset using their respective test sets. These unified means are then applied consistently across all test sets.

Query mean ($\bar{e}_{q}$): We sample approximately 10000 text queries from the training splits of MSCOCO, Google WIT, NFCorpus, and VisualNews. These are encoded using $f^{T}$ and averaged to produce the global query mean $\bar{e}_{q}$.

Document text mean ($\bar{e}^{T}$): We sample approximately 10000 long-form text documents or descriptive captions from the training splits of MSCOCO, OVEN, Google WIT, and VisualNews. These are encoded using $f^{T}$ and averaged to obtain the document text mean $\bar{e}^{T}$.

Document image mean ($\bar{e}^{I}$): To compute $\bar{e}^{I}$, we sample 10000 images from the training splits of MSCOCO, OVEN, Google WIT, and VisualNews. These are encoded using $f^{I}$ and averaged to produce the document image mean.

OVEN-Specific Query Mean ($\bar{e}_{q}^{\text{OVEN}}$): Since queries in OVEN are particularly short, we construct a dataset-specific query mean by sampling 2000 queries from the OVEN training split.

Other Modality Means: For non-image-text datasets-such as MSVD (video-text), Clotho (audio-text), and screenshot-style documents (screenshot-text) in SciFact and NFCorpus-we compute modality-specific means using 2500 training examples per modality.

We summarize the full GR-CLIP algorithm as follows:

## Appendix C Details of Models

In this section, we provide the exact versions and checkpoint links for all models used in our experiments. For CLIP-based models, we include two variants of OpenAI CLIP ( [clip ,](https://arxiv.org/html/2507.19054v1#bib.bib25) ) , two variants of OpenCLIP ( [openclip ,](https://arxiv.org/html/2507.19054v1#bib.bib33) ) , and SigLIP-400M ( [siglip ,](https://arxiv.org/html/2507.19054v1#bib.bib34) ) .

For the VLM2Vec framework, we use two variants: one based on LLaVA-Next ( [liu2024llavanext ,](https://arxiv.org/html/2507.19054v1#bib.bib20) ) , which serves as the backbone for the results reported in the main paper ( [vlm2vec ,](https://arxiv.org/html/2507.19054v1#bib.bib12) ) ; and another based on the latest officially released Qwen-VL ( [qwen ,](https://arxiv.org/html/2507.19054v1#bib.bib1) ) , which achieves the best performance on the MMEB ( [vlm2vec ,](https://arxiv.org/html/2507.19054v1#bib.bib12) ) benchmark according to its official repository.

Additionally, for non-image-text modalities, we use ViCLIP ( [viclip ,](https://arxiv.org/html/2507.19054v1#bib.bib31) ) for video-text retrieval and CLAP ( [clasp ,](https://arxiv.org/html/2507.19054v1#bib.bib32) ) for audio-text retrieval tasks.

All model checkpoint links are listed below:

- • OpenAI CLIP-B/16 : [https://huggingface.co/openai/clip-vit-base-patch16](https://huggingface.co/openai/clip-vit-base-patch16)
- • OpenAI CLIP-L/14 : [https://huggingface.co/openai/clip-vit-large-patch14-336](https://huggingface.co/openai/clip-vit-large-patch14-336)
- • OpenCLIP-B/16 : [https://huggingface.co/laion/CLIP-ViT-B-16-laion2B-s34B-b88K](https://huggingface.co/laion/CLIP-ViT-B-16-laion2B-s34B-b88K)
- • OpenCLIP-L/14 : [https://huggingface.co/laion/CLIP-ViT-L-14-laion2B-s32B-b82K](https://huggingface.co/laion/CLIP-ViT-L-14-laion2B-s32B-b82K)
- • SigLIP-400m : [https://huggingface.co/google/siglip-so400m-patch14-384](https://huggingface.co/google/siglip-so400m-patch14-384)
- • VLM2Vec (LLaVA-Next) : [https://huggingface.co/TIGER-Lab/VLM2Vec-LLaVa-Next](https://huggingface.co/TIGER-Lab/VLM2Vec-LLaVa-Next)
- • VLM2Vec (Qwen-VL) : [https://huggingface.co/TIGER-Lab/VLM2Vec-Qwen2VL-7B](https://huggingface.co/TIGER-Lab/VLM2Vec-Qwen2VL-7B)
- • ViCLIP-L/14 : [https://huggingface.co/OpenGVLab/ViCLIP-L-14-hf](https://huggingface.co/OpenGVLab/ViCLIP-L-14-hf)
- • CLAP : [https://huggingface.co/laion/clap-htsat-fused](https://huggingface.co/laion/clap-htsat-fused)

## Appendix D Details of Evaluation Metrics

In the main paper, we use the widely adopted NDCG@10 as the evaluation metric. Here, we provide the detailed computation process for this metric.

Given a ranked list of retrieved items up to position $K$, NDCG@$K$ is computed as:

|    | $$\text{NDCG@}K=\frac{1}{\text{IDCG@}K}\sum_{i=1}^{K}\frac{2^{\text{rel}_{i}}-1}{\log_{2}(i+1)}$$   |    | (2)   |
|----|-----------------------------------------------------------------------------------------------------|----|-------|

where $\text{rel}_{i}$ denotes the relevance score of the item at rank $i$, and IDCG@$K$ is the ideal DCG-that is, the maximum possible DCG for the top $K$ items-computed by sorting the items by relevance in descending order:

|    | $$\text{IDCG@}K=\sum_{i=1}^{K}\frac{2^{\text{rel}_{i}^{\star}}-1}{\log_{2}(i+1)}$$   |    | (3)   |
|----|--------------------------------------------------------------------------------------|----|-------|

where $\text{rel}_{i}^{\star}$ is the $i$-th highest relevance score in the ideal ranking.

NDCG@10 ranges from 0 to 1, with 1 indicating a perfect ranking.

## Appendix E Details of Datasets

In this section, we provide additional details on how each dataset is processed to support our retrieval experiments in § [3](https://arxiv.org/html/2507.19054v1#S3) , [4](https://arxiv.org/html/2507.19054v1#S4) , and [5](https://arxiv.org/html/2507.19054v1#S5) . For each dataset, we distinguish between the original data format ( Before ) and the modified version used in our framework ( After ). We also describe the key post-processing steps.

NFCorpus ( [nfcorpus ,](https://arxiv.org/html/2507.19054v1#bib.bib3) ) , SciFact ( [scifact ,](https://arxiv.org/html/2507.19054v1#bib.bib30) ) :
Before: A short text query paired with a relevant long text document.
After: We retain the short text query and render the long text document into a screenshot using OpenCV. This allows retrieval of either the original text document or its rendered screenshot given the query.

Google WIT ( [googlewit ,](https://arxiv.org/html/2507.19054v1#bib.bib27) ) :
Before: Each sample includes a page title, a long page description, a reference image, and a reference description for the image.
After: We concatenate the page title and image reference description to form the query. The page description is used as the long text document, and the associated image serves as the image document.

OVEN ( [oven ,](https://arxiv.org/html/2507.19054v1#bib.bib10) ) :
Before: Each query consists of an image-text pair, and the retrieval target is also an image-description pair.
After: Since either the image or text component can independently answer the query, we treat both the image and caption as valid standalone documents. The query remains unchanged.

MSCOCO ( [mscoco ,](https://arxiv.org/html/2507.19054v1#bib.bib18) ) :
Before: Each image is paired with five captions.
After: One caption is sampled as the query. The remaining captions are used to construct a long-form description via GPT-4o, with the content of the sampled caption preserved. This long description becomes the text document, and the associated image serves as the image document.

VisualNews ( [visualnews ,](https://arxiv.org/html/2507.19054v1#bib.bib19) ) :
Before: Each image is paired with a short news-style caption.
After: We use GPT-4o to jointly analyze the image and its associated article from the original VisualNews dataset. Based on both the visual content and article text, GPT-4o generates a detailed descriptive paragraph that expands upon the original caption, which we use as the text document. The image serves as the image document, and the original caption is retained as the query.

Clotho ( [clotho ,](https://arxiv.org/html/2507.19054v1#bib.bib6) ) :
Before: Each audio clip is paired with several semantically similar captions.
After: One caption is selected as the query, and another semantically similar caption (chosen by GPT-4o) is used as the text document. The audio clip itself is used as the audio document.

MSVD ( [msvd ,](https://arxiv.org/html/2507.19054v1#bib.bib4) ) :
Before: Each video is paired with several semantically similar captions.
After: One caption is used as the query, and another semantically similar caption (chosen by GPT-4o) serves as the text document. The video is treated as the video document.

Nights ( [nights ,](https://arxiv.org/html/2507.19054v1#bib.bib8) ) :
Before: Each image is paired with a visually similar image.
After: One image is used as the query. GPT-4o observes this image and generates a concise title, which we use as the text document. The paired image serves as the image document.

VLM2Vec input format: For VLM2Vec ( [vlm2vec ,](https://arxiv.org/html/2507.19054v1#bib.bib12) ) , prompts are required to serve as instructions for generating embeddings. Specifically, for each Query , we use the prompt ''Retrieve a relevant item that represents: {Query}\n'' in settings 1 and 3, which involve retrieval from a heterogeneous corpus composed of multiple modalities. In Setting 2, where retrieval is over a homogeneous corpus of fused image-text pairs, we use ''Retrieve an image-description pair that represents: {Query}\n'' . Documents follow the format specified in the original datasets.

CLIP input format: For CLIP -based models ( [clip ,](https://arxiv.org/html/2507.19054v1#bib.bib25) ; [siglip ,](https://arxiv.org/html/2507.19054v1#bib.bib34) ; [openclip ,](https://arxiv.org/html/2507.19054v1#bib.bib33) ; [viclip ,](https://arxiv.org/html/2507.19054v1#bib.bib31) ; [clasp ,](https://arxiv.org/html/2507.19054v1#bib.bib32) ) and GR-CLIP , we do not apply any instructions. Queries and documents are directly passed to the respective CLIP text and image encoders without modification.

Table [2](https://arxiv.org/html/2507.19054v1#A5.T2) summarizes the key characteristics of each dataset, including the retrieval setting, the modality composition of queries and corpora, and the total number of evaluation examples.

## Appendix F Case Studies

Below, we present case studies from each subset of MixBench, which also serve as visualizations of our dataset. For each example query, we display the Top-5 retrieved results from both the baseline OpenAI CLIP-L/14 and our proposed GR-CLIP-L/14 model. Each retrieved document is annotated with its modality ( text , image , or multimodal ), its cosine similarity to the query, and whether it is a ground-truth relevant item.

These example results illustrate both the diversity of the MixBench datasets and the effectiveness of GR-CLIP in mixed modality search. Unlike the original CLIP model, which tends to retrieve documents matching the query's modality, GR-CLIP successfully bridges the modality gap, retrieving results that more accurately reflect the semantic intent of the query-regardless of modality.

### [F.1 Google WIT ( googlewit , )](https://arxiv.org/html/2507.19054v1#bib.bib27)

Query: List of Jews in sports, Nate Ebner

CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.5430, Modality = text

This is a list of individuals currently serving in the United States House of Representatives.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.5355, Modality = text

This is a list of notable Austrians.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.5227, Modality = text

This is a list of vehicles manufactured by the Buick Motor Division of General Motors.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.5181, Modality = text

This is a list of notable alumni and faculty of Golden Gate University.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.5101, Modality = text

Puthenchira is a village in Thrissur district in the state of Kerala, India.
GR-CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.3403, Modality = Image ( Ground Truth )

[Uncaptioned image]

![](assets/fig08.png)

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.1798, Modality = text

This is a list of notable Austrians.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.1774, Modality = text

The Lebanon national football team, controlled by the Lebanese Football Association, have represented Lebanon in association football since their inception in 1933. The squad is governed by the Asian Football Confederation continentally, and FIFA worldwide. While Lebanon have yet to qualify for the FIFA World Cup, they have participated twice in the Asian Cup: in 2000, when they hosted the event, and in 2019, the first time through regular qualification. Lebanon's main venue is the Camille Chamoun Sports City Stadium in Beirut; however they also play in other locations such as the Saida International Stadium in Sidon. In 1934, Lebanon played their first match against the Romanian side CA Timi \textcommabelow soara, but it was not ratified by FIFA. Lebanon played their first FIFA-recognised game in 1940 against Mandatory Palestine. During their 2014 qualification campaign for the World Cup, Lebanon reached the final qualifying round for the first time thanks to a 2-1 victory against South Korea at home in 2011, but failed to qualify for the 2014 FIFA World Cup finishing bottom of their group. At the 2019 Asian Cup, Lebanon were close to qualifying to the knock-out stages for the first time.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.1723, Modality = text

This is a list of properties and historic districts in Winchester, Massachusetts, that are listed on the National Register of Historic Places. The locations of National Register properties and districts may be seen in an online map by clicking on "Map of all coordinates." This National Park Service list is complete through NPS recent listings posted July 17, 2020.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.1708, Modality = multimodal

[Uncaptioned image]

![](assets/fig09.png)

This list is of that portion of the National Register of Historic Places designated in Essex County, Massachusetts. The locations of these properties and districts for which the latitude and longitude coordinates are included below, may be seen in a map. There are more than 450 designated properties in the county, including 25 that are further designated as National Historic Landmarks. The municipalities of Andover, Gloucester, Ipswich, Lawrence, Lynn, Methuen, and Salem are to be found on a separate list of the more than 200 identified here, except two properties are split between Methuen and Lawrence, and one between Lynn and Nahant; these entries appear on more than one list. This National Park Service list is complete through NPS recent listings posted August 14, 2020.

### [F.2 MSCOCO ( mscoco , )](https://arxiv.org/html/2507.19054v1#bib.bib18)

Query: A woman in a room with a cat.
CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.5044, Modality = text

A kitchen featuring light wood cabinets and a black granite countertop. It includes a black stove with four burners, an over-the-range microwave, and a black refrigerator. The flooring is a warm wooden tone.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.4605, Modality = text

A cat is perched on the closed lid of a toilet, appearing somewhat perturbed. The toilet is located in a bathroom with a light-colored wall. Next to the toilet, there is a basket or container. The cat's tail is visible, and it seems to be alert or possibly startled.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.4445, Modality = text

A long hot dog is placed in a bun on a white paper plate, which sits on a wooden table. The hot dog extends beyond the ends of the bun.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.4160, Modality = multimodal

[Uncaptioned image]

![](assets/fig10.png)

The warm and cozy living room is adorned with Christmas decorations, featuring a silver tinsel Christmas tree by the fireplace. The room is filled with a variety of gift-wrapped presents scattered around on the red carpet. On the mantelpiece, festive ornaments and stockings add to the holiday spirit. A comfortable beige sofa with cushions sits alongside a coffee table with magazines. The ceiling is decorated with shimmering golden stars, and a television displaying a dartboard game adds to the lived-in, festive atmosphere. The soft lighting from lamps enhances the room's inviting ambiance.

\hdashrule

[0pt]0.5pt2pt 2pt

Rank No.5 , Cosine Similarity = 0.4126, Modality = text

A delicious Italian pizza is presented on a white plate, topped with slices of fresh tomatoes, green olives, and thinly sliced onions. The pizza is garnished with herbs and seasonings, adding a colorful and flavorful touch to the dish.
GR-CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.3012, Modality = multimodal ( Ground Truth )

[Uncaptioned image]

![](assets/fig11.png)

A woman is standing in a kitchen, smiling and holding a cat. She is wearing a brown sweater and a blue plaid skirt. The kitchen has wooden cabinets and a countertop with a potted plant and a bowl of oranges. There is a sink with dishes on one side and a white refrigerator on the other. A clock is visible on the wall, and there are various items on the counter and a small rug on the floor.

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.2924, Modality = multimodal

[Uncaptioned image]

![](assets/fig12.png)

A person wearing glasses and a black shirt is sitting by a window with closed blinds, brushing a cat that is sitting on a purple blanket draped over a radiator. The cat is facing away, and the brush is Magenta with a grey bristle area. The floor is wooden, and the cat seems relaxed.

\hdashrule

[0pt]0.5pt2pt 2pt

Rank No.3 , Cosine Similarity = 0.2780, Modality = text

A cat is perched on the closed lid of a toilet, appearing somewhat perturbed. The toilet is located in a bathroom with a light-colored wall. Next to the toilet, there is a basket or container. The cat's tail is visible, and it seems to be alert or possibly startled.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.2745, Modality = multimodal

[Uncaptioned image]

![](assets/fig13.png)

A gray armchair and a black armchair are positioned next to each other in a room. A small lamp is placed on a table next to the black chair. Partially visible from behind the armchair is a cat peeking out, adding a playful touch to the setting. In front of the chairs, there is a wooden table with a remote control on it.

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.2612, Modality = image

[Uncaptioned image]

![](assets/fig14.png)

### [F.3 OVEN ( oven , )](https://arxiv.org/html/2507.19054v1#bib.bib10)

Query: What is the name of this building?
CLIP Top-5 Results

[Uncaptioned image]

![](assets/fig15.png)

Rank No.1 , Cosine Similarity = 0.5340, Modality = multimodal

[Uncaptioned image]

![](assets/fig16.png)

Clérigos Church. The Clérigos Church is a Baroque church in the city of Porto, in Portugal. Its 75-meter-tall bell tower, the Torre dos Clérigos, can be seen from various points of the city and is one of its most characteristic symbols. History: The church was built for the Brotherhood of the Clérigos (Clergy) by Nicolau Nasoni, an Italian architect and painter who left an extensive body of work in the north of Portugal during the 18th century. Construction of the church began in 1732 and was finished in 1750, while the bell tower and the monumental divided stairway...

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.5321, Modality = image

[Uncaptioned image]

![](assets/fig17.png)

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.5276, Modality = multimodal

[Uncaptioned image]

![](assets/fig18.png)

St. Peter's Basilica. The Papal Basilica of Saint Peter in the Vatican, or simply Saint Peter's Basilica, is a church built in the Renaissance style located in Vatican City. It was initially planned by Pope Nicholas V and then Pope Julius II to replace the aging Old St. Peter's Basilica, which was built in the fourth century by Roman emperor Constantine the Great. Construction of the present basilica began on 18 April 1506 and was completed on 18 November 1626. Designed principally by Donato Bramante, Michelangelo, Carlo Maderno, and Gian Lorenzo Bernini...

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.5274, Modality = multimodal

[Uncaptioned image]

![](assets/fig19.png)

Coit Tower. Coit Tower is a 210-ft tower in the Telegraph Hill neighborhood of San Francisco, California, offering panoramic views over the city and the bay. Built between 1932 and 1933 using Lillie Hitchcock Coit's bequest to beautify the city, it was added to the National Register of Historic Places in 2008. The unpainted reinforced concrete tower, designed by Arthur Brown, Jr. and Henry Howard, features American fresco mural paintings by 25 different onsite artists...

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.5252, Modality = multimodal

[Uncaptioned image]

![](assets/fig20.png)

Ilinden (Memorial). Also known as Makedonium, Ilinden is a monument in Kruševo, North Macedonia. Officially opened on August 2, 1974, it commemorates the Second Session of the Anti-fascist Assembly and the 1903 Ilinden uprising. Designed by Jordan and Iskra Grabuloski, it honors fighters in the National Liberation Struggle from 1941-1944. Description. The monument covers 12 acres and features a rounded architectural style...

GR-CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.3153, Modality = text ( Ground Truth )

Canadian National Vimy Memorial. The Canadian National Vimy Memorial is a war memorial site in France dedicated to the memory of Canadian Expeditionary Force members killed during the First World War. It also serves as the place of commemoration for Canadian soldiers of the First World War killed or presumed dead in France who have no known grave. The monument is the centrepiece of a 100 (ha) preserved battlefield park that encompasses a portion of the ground over which the Canadian Corps made their assault during the initial Battle of Vimy Ridge offensive of the Battle of Arras.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.2795, Modality = image

[Uncaptioned image]

![](assets/fig21.png)

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.2762, Modality = multimodal

[Uncaptioned image]

![](assets/fig22.png)

Mary, Queen of the World Cathedral. Mary, Queen of the World Cathedral or in full Mary, Queen of the World and St. James the Great Cathedral is a minor basilica in Montreal, Quebec, Canada, and the seat of the Roman Catholic archdiocese of Montreal. It is the third largest church in Quebec after Saint Joseph's Oratory (also in Montreal) and the Basilica of Sainte-Anne-de-Beaupré east of Quebec City. The building is 101 m (333 ft) in length, 46 m (150 ft) in width, and a maximum height of 77 m (252 ft) at the cupola, the diameter of which is 23 m (75 ft).

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.2744, Modality = image

[Uncaptioned image]

![](assets/fig23.png)

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.2590, Modality = multimodal

[Uncaptioned image]

![](assets/fig24.png)

Sydney Town Hall. The Sydney Town Hall is a late 19th-century heritage-listed town hall building in the city of Sydney, the capital city of New South Wales, Australia, housing the chambers of the Lord Mayor of Sydney, council offices, and venues for meetings and functions. It is located at 483 George Street, in the Sydney central business district opposite the Queen Victoria Building and alongside St Andrew's Cathedral. Sited above the Town Hall station and between the city shopping and entertainment precincts, the steps of the Town Hall are a popular meeting place. It was designed by John H. Wilson, Edward Bell, Albert Bond.

### [F.4 VisualNews ( visualnews , )](https://arxiv.org/html/2507.19054v1#bib.bib19)

Query: Former California officer Jay Cicinelli puts his head in his hands immediately after hearing the not guilty verdict in murder trial of a homeless man.

CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.4364, Modality = text

In this courtroom sketch, a solemn scene unfolds as the individual is depicted during the sentencing phase of a high-profile trial. The person was sentenced to death, marking a significant moment in the judicial process. The courtroom, filled with tension and gravity, reflects the serious nature of the proceedings. The sketch captures the atmosphere and the weight of the decision rendered by the court.
\hdashrule [0pt]0.5pt2pt 2pt

Rank No.2 , Cosine Similarity = 0.4186, Modality = text

The image shows a former general, who has been sentenced to life in prison for his role in the murder of a Catholic bishop during Argentina's 1976-83 military dictatorship. The trial revealed documents, including letters from the Vatican archives provided by Pope Francis, which showed the bishop's denunciation of the regime's abuses. The general was found guilty of ordering the murder of Bishop Enrique Angelelli in 1976, marking a significant conviction of a junta-era official for the killing of a high-ranking cleric.
\hdashrule [0pt]0.5pt2pt 2pt

Rank No.3 , Cosine Similarity = 0.3994, Modality = text

On October 3, 2011, in a courtroom filled with emotional tension, Amanda Knox's father is embraced by his wife following the announcement that Amanda had won her appeal against her murder conviction. The atmosphere is charged with relief and joy as supporters and family members react to the verdict. The image captures a poignant moment of familial support and celebration amidst the wider context of a highly publicized and dramatic legal battle.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.3718, Modality = text

Sudheendra Kulkarni was attacked with black ink, leaving his face and head covered. This incident occurred in public, attracting media attention and police presence, as seen in the image. Kulkarni was subsequently taken to a hospital to have the ink removed. The event highlighted tensions and provoked widespread reactions, underscoring the volatile nature of public discourse.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.3698, Modality = text

The Rev Sidney Davis leads mourners in a community prayer service at Second Presbyterian Church in Charleston, following the tragic shooting that claimed the lives of nine black worshipers. This gathering reflects the communal grief and solidarity in the face of violence, as mourners join hands in prayer. The event underscores ongoing discussions about race and gun control, issues highlighted during President Obama's presidency. The somber atmosphere is a reminder of the challenges and unresolved issues surrounding racial tensions and gun violence in America.

GR-CLIP Top-5 Results

Rank No.1 , Cosine Similarity = 0.4265, Modality = image ( Ground truth )

[Uncaptioned image]

![](assets/fig25.png)

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.2 , Cosine Similarity = 0.3605, Modality = text

In this courtroom sketch, a solemn scene unfolds as the individual is depicted during the sentencing phase of a high-profile trial. The person was sentenced to death, marking a significant moment in the judicial process. The courtroom, filled with tension and gravity, reflects the serious nature of the proceedings. The sketch captures the atmosphere and the weight of the decision rendered by the court.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.3 , Cosine Similarity = 0.3365, Modality = text

The image shows a former general, who has been sentenced to life in prison for his role in the murder of a Catholic bishop during Argentina's 1976-83 military dictatorship. The trial revealed documents, including letters from the Vatican archives provided by Pope Francis, which showed the bishop's denunciation of the regime's abuses. The general was found guilty of ordering the murder of Bishop Enrique Angelelli in 1976, marking a significant conviction of a junta-era official for the killing of a high-ranking cleric.
\hdashrule [0pt]0.5pt2pt 2pt Rank No.4 , Cosine Similarity = 0.3224, Modality = multimodal

[Uncaptioned image]

![](assets/fig26.png)

MPs are raising concerns about the lack of access to inpatient mental health services for young people, highlighting cases like Nikki Mattocks, who faced significant delays and inadequate support. Despite her struggles with severe mental health issues, she experienced a fragmented care system, resulting in repeated emergency visits and admissions to distant psychiatric units. This lack of continuity and proximity to family exacerbated her condition. The parliamentary report underscores the urgent need for early intervention and better resource allocation to prevent further harm to vulnerable youths.

\hdashrule

[0pt]0.5pt2pt 2pt Rank No.5 , Cosine Similarity = 0.2956, Modality = text

On October 3, 2011, in a courtroom filled with emotional tension, Amanda Knox's father is embraced by his wife following the announcement that Amanda had won her appeal against her murder conviction. The atmosphere is charged with relief and joy as supporters and family members react to the verdict. The image captures a poignant moment of familial support and celebration amidst the wider context of a highly publicized and dramatic legal battle.