# Introduction

デジタル世界における情報は、テキスト、画像、動画、音声、そしてそれらのさまざまな組み合わせという複数のモダリティにまたがって存在する。従来の検索システムは主として、同種のコーパス内での検索、すなわち text-to-text や text-to-image retrieval に焦点を当ててきたが {{CITE:26}}{{CITE:13}}{{CITE:15}}{{CITE:25}}、現実世界の応用では、異種モダリティ間で関連コンテンツを検索・取得する能力、すなわち text-to-{text, image, or both} retrieval がますます求められている {{CITE:29}}。たとえば、ユーザが「Mountain Fuji」を検索した場合、山を説明するテキスト文書、独立した画像、ならびに両モダリティを組み合わせたマルチモーダルなウェブページを見つけることを期待するであろう（Figure [\[fig:pull\]](#fig:pull)a）。

その実用的重要性にもかかわらず、**mixed modality search** の課題は依然として十分に探究されていない {{CITE:29}}。中心的な課題は、異なるモダリティにまたがる意味的に類似したコンテンツ――たとえば、画像と「Mountain Fuji」のテキスト説明――を近接した位置に写像できる統一埋め込み空間を構築することにある。これにより、クエリと文書のモダリティに依存せず、意味的類似性を正確に測定できる。近年のマルチモーダル対照学習の進展、とりわけ CLIP ベースのモデル {{CITE:25}}{{CITE:33}}{{CITE:34}} は、大規模な画像・テキスト対ペアデータセットで学習することによりテキストと画像の埋め込みを整列させる有望な解決策を提供している。

本研究では、これらの対照モデルが現実的な mixed modality search シナリオにおいてどの程度機能するかを検討する。具体的には、CLIP は視覚と言語のための二つの別個のエンコーダから構成される {{CITE:25}}。各コーパス項目について、画像のみの文書とテキストのみの文書はそれぞれ対応するエンコーダで埋め込む。画像とテキストの両方を含むマルチモーダル文書については、画像埋め込みとテキスト埋め込みの線形結合によってそれらを表現する（Figure [\[fig:pull\]](#fig:pull)b）。埋め込みが得られた後は、クエリ埋め込みと各コーパス項目とのコサイン類似度を計算して類似性検索を行い、関連性に基づく上位10件の順位付けの質を測る NDCG@10 などの標準的な検索指標 {{CITE:11}} を用いて性能を評価する。

我々の分析は、CLIP スタイルの対照モデルの根本的な限界を明らかにする。すなわち、埋め込み空間において顕著な **modality gap** {{CITE:17}}{{CITE:35}}{{CITE:36}} を示し、その結果 mixed modality 設定での検索性能が大きく低下する。これらのモデルは画像とテキストの対を整列させるよう訓練されるものの、画像埋め込みとテキスト埋め込みは別々のクラスターを形成し、埋め込み空間内で大きく離れたままである（Figure [\[fig:pull\]](#fig:pull)c）。このクラスタリングは強い *intra-modal ranking bias*（§3）を引き起こす。すなわち、同一モダリティ間の項目（たとえば image-to-image や text-to-text）の類似度が、異なるモダリティ間（たとえば image-to-text）よりもはるかに高くなり、検索順位に系統的な偏りが生じる（Figure [\[fig:pull\]](#fig:pull)d）。たとえば、「Mountain Fuji」というテキストクエリが与えられたとき、Mountain Fuji を描写する画像が、「this is a great paper.」のような無関係なテキスト断片よりも下位に順位付けされることがある。さらに、modality gap は *inter-modal fusion*（§4）も損なう。すなわち、画像埋め込みとテキスト埋め込みを線形補間で結合すると、特徴が最適でない領域へ押しやられ、意味情報が弱まり、画像のみあるいはテキストのみを用いる場合よりも性能が悪化することがある。

![](assets/fig01.png)

**mixed modality search の概要.** **(a) 問題設定:** mixed modality search は、マルチモーダル文書を含む異種コーパスから関連情報を検索することを目的とする。これは、クエリと文書の双方を埋め込み、その後に類似度に基づく検索を行うことで実現される。**(b) 埋め込み手法:** 単一モダリティ文書は CLIP のモダリティ固有エンコーダで埋め込まれ、マルチモーダル文書は画像特徴とテキスト特徴の重み付き融合によって埋め込まれる。**(c) Modality Gap:** CLIP の埋め込み空間には modality gap が見られ、埋め込みは各モダリティごとに異なるクラスターを形成し、モダリティ間で大きく分離したままである。**(d) モダリティ間のコサイン類似度:** この modality gap により、クエリと同じモダリティを共有する文書はコサイン類似度スコアが高くなりやすく、より上位に順位付けされるため、系統的な順位バイアスが導入される。**(e) MixBench における性能:** mixed modality search のために新たに作成した MixBench ベンチマークにおいて、modality gap を解消する軽量な後処理キャリブレーション手法である GR-CLIP は、性能を大幅に改善し、計算コストを大きく抑えつつ、最先端の VLM2Vec  {{CITE:12}} ベースラインを上回る。

modality gap に起因する順位バイアスと融合失敗に対処するため、我々は **GR-CLIP** を導入する。これは、CLIP の埋め込み空間から modality gap を除去する軽量な後処理キャリブレーション手法である（GR は gap-removed を意味する）。先行研究 {{CITE:35}}{{CITE:36}} は、CLIP 系モデルにおける modality gap は、画像およびテキスト埋め込み部分空間に直交する定数ベクトルによって近似できることを示している。この理論に基づき、我々はすべての画像データとテキストデータの平均埋め込みを計算し、その差を用いて modality gap を推定し、検索を行う前にこのベクトルをすべての埋め込みから差し引く。この手法は、平均埋め込みを計算するためにデータセット全体を一度走査するだけでよく、計算オーバーヘッドは無視できるほど小さい。

**MixBench** で評価した結果、すなわち mixed modality search のために明示的に設計された 4 つのサブセット（Google-WIT {{CITE:27}}, MSCOCO {{CITE:18}}, OVEN {{CITE:10}}, VisualNews {{CITE:19}}）からなるベンチマークにおいて、GR-CLIP は一貫して元の CLIP モデルを上回り、NDCG@10 において最大 26 パーセントポイントの改善を達成した。また、VLM2Vec {{CITE:12}} のような近年の vision-language generative embedding 手法を 4 パーセントポイント上回りつつ、計算コストを 75$\times$ 削減した。さらに、我々の手法は異なる CLIP 変種（たとえば OpenAI CLIP {{CITE:25}}, OpenCLIP {{CITE:33}}, SigLIP {{CITE:34}}）および異なるモダリティ（たとえば text-to-image, text-to-audio, text-to-video）にまたがって一般化することを示す。

要するに、本研究は、ユーザが多様なモダリティ型を含む異種コーパスを検索するウェブ検索エンジンのような現実的シナリオを反映する **mixed modality search** の問題を定式化し、その性質を検討した。我々は、最先端の対照モデルが modality gap に起因して順位バイアスと融合失敗に苦しむことを示し、この問題に対処する軽量な後処理キャリブレーション手法を提案した。本研究の知見は、効果的な mixed modality search を実現するためには、真に統一された埋め込み空間を構築することの重要性を浮き彫りにする。

# Preliminaries 

本節では、mixed modality search のタスクを定義し、その課題と課題に関連する三つの設定を導入し、さらに用いる手法と評価指標を記述する。

## Problem Formulation

Mixed modality search は、クエリと文書がテキスト、画像、音声、動画など異なるモダリティの組合せから構成され得るときに、意味的に関連するコンテンツを検索することを目的とする。$\mathcal{M}$ をサポートされるモダリティの集合とする（たとえば、$\mathcal{M} = \{\text{text}, \text{image}, \text{audio}, \text{video}\}$）。クエリは $q$ で表し、そのモダリティ集合を $m_q \subseteq \mathcal{M}$ とする。検索コーパスは $\mathcal{C} = \{d_i\}_{i=1}^N$ と定義され、各文書 $d_i$ はモダリティ集合 $m_i \subseteq \mathcal{M}$ に関連付けられる。目的は、モダリティがクエリと文書の間でどのように分布しているかに依存せず、各文書に対する類似度スコア $s(q, d_i)$ を計算し、意味的関連性に基づく順位付きリストを返すことである。

二つの性質が mixed modality search を従来の検索タスクと区別する。**1) heterogeneous corpus:** 文書ごとにモダリティ構成が異なる、すなわち $d_i, d_j \in \mathcal{C}$ であって $m_i \ne m_j$ となるものが存在する。たとえば、一つの文書はテキストのみ（$m_i = \{\text{text}\}$）、別の文書は画像のみ（$m_j = \{\text{image}\}$）、さらに別の文書はマルチモーダル（$m_k = \{\text{text}, \text{image}\}$）であり得る。**b) multimodal documents:** 一部の文書は単一エントリ内に複数モダリティを含み、すなわち $|m_i| > 1$ である。これらのモダリティはしばしば相補的な情報を提供し、効果的な理解のためには融合が必要となる（たとえば、画像と説明的キャプションの対）。

## Settings

異種コーパスとマルチモーダル文書の組合せは、二つの中心的なモデリング課題を導入する。**1) cross-modal alignment:** 「Mount Fuji」のテキストと画像のような類似概念の表現が、異なるモダリティ間で比較可能となるようにすることである。すなわち、これらが表現空間内の近接した位置に埋め込まれる必要がある。**2) multimodal fusion:** 文書内の複数モダリティを効果的に結合し、統一された意味的に有意な表現を形成することである。たとえば、「Mount Fuji」のテキストと画像を統合して、より豊かな概念表現を生成することが挙げられる。これらの課題を体系的に検討するため、我々は三つの設定を定義する。

**Ablated setting 1: only heterogeneous corpus (§3).** 各文書は単一モダリティであるが（$|m_i| = 1$）、コーパスは複数モダリティにまたがる（$|\mathcal{M}| > 1$）。たとえば、Figure [\[fig:pull\]](#fig:pull)a の $d_1$ と $d_2$ に対応するように、同一概念に関するテキストのみと画像のみの記述を含み得る。これは cross-modal alignment のみを検証する設定であり、モデルがモダリティ間で比較可能な表現を符号化できるかどうかを問う。

**Ablated setting 2: only multimodal documents (§4).** すべての文書が同じモダリティ集合を含む（$m_i = \mathcal{M}$ かつ $|m_i| > 1$）。たとえば、各文書が画像と対応するキャプションの両方を含み、Figure [\[fig:pull\]](#fig:pull)a の $d_3$ に対応する。この設定は純粋に multimodal fusion に焦点を当て、モデルが複数モダリティを効果的に結合できるかを評価する。

**Full setting: mixed modality search (§5).** 文書は単一モダリティまたはマルチモーダルのいずれかであり得（$|m_i| \ge 1$）、コーパスは異種である。たとえば、ある文書はテキストのみ、別の文書は画像のみ、さらに別の文書はそれらの組合せであり、Figure [\[fig:pull\]](#fig:pull)a において $d_1$, $d_2$, $d_3$ がすべて存在する場合に相当する。これは最も現実的で一般的な設定であり、ニュース記事、商品リスト、科学データセットのような実世界のコーパスを反映する。これは両方の中心課題を統合し、我々の主要評価シナリオとなる。

## Methods 

クエリ $q$ と文書 $d_i$ が与えられたとき、我々は埋め込みモデル $f$ を用いてそれらの埋め込み $e_q = f(q)$ と $e_i = f(d_i)$ を計算し、コサイン類似度 $s(q, d_i) = \frac{e_q \cdot e_i}{\|e_q\| \cdot \|e_i\|}$ により文書を順位付けする。以下の埋め込み手法を評価する。

**CLIP (baseline) {{CITE:25}}.** CLIP は、対になった画像・テキスト入力を整列させるよう訓練された対照的 vision-language model である。画像エンコーダ $f^I$ とテキストエンコーダ $f^T$ を用いて、各モダリティを別々に符号化する。単一モダリティのテキスト文書または画像文書 $d_i$ と $d_j$ については、モダリティ固有のエンコーダを用いて埋め込みを計算する：$e_i = f^I(d_i)$ および $e_j = f^T(d_j)$。画像入力 $d_k^I$ とテキスト入力 $d_k^T$ を含むマルチモーダル文書 $d_k$ については、重み付き補間を計算する：$e_k = \alpha \cdot f^T(d_k^T) + (1 - \alpha) \cdot f^I(d_k^I)$、ここで $\alpha \in [0, 1]$ は各モダリティの寄与を調整する。

**VLM2Vec (baseline) {{CITE:12}}.** VLM2Vec は、LLaVA {{CITE:21}} や Qwen-VL {{CITE:1}} などの大規模視覚言語モデル $f$ を適応させ、自己回帰的手法により文書埋め込みを生成する最先端のマルチモーダル生成埋め込み手法である。各文書 $d_i$ は、テキスト入力と画像入力を組み合わせた instruction-style prompt $p_i$（例: *"Generate the embedding for the document: \[image tokens\] \[text tokens\]"*）として整形され、その後自己回帰的に処理される。最終デコーダ層の pooled representation を埋め込み $e_i = f(p_i)$ として用いる。本手法は、2つのモダリティを共同でモデル化し instruction tuning を行うことで、高次の意味的整合を捉える。

**GR-CLIP (ours).** CLIP はモダリティの整合を目的とするにもかかわらず、先行研究はその埋め込み空間に持続的なモダリティギャップが存在することを示している。すなわち、画像埋め込みとテキスト埋め込みは別々のクラスターを形成し、互いに距離を保ったままである {{CITE:17}}。対応する画像・テキスト埋め込み $e_i^T$ と $e_i^I$ の関係は、共有埋め込み部分空間に直交する定数ベクトル $c_\perp$ を用いて $e_i^T - e_i^I \approx c_\perp$ とモデル化でき、これはモダリティギャップを表す {{CITE:36}}。GR-CLIP（GR は gap-removed の略）は、このギャップをモダリティ固有の平均を差し引くことで除去する軽量な事後較正手法である: $e_i^{\prime T} = e_i^T - \mathbb{E}_i[e_i^T], e_i^{\prime I} = e_i^I - \mathbb{E}_i[e_i^I]$。このゼロ中心化によりモダリティギャップが消失し {{CITE:36}}、$e_i^{\prime T} - e_i^{\prime I} = (e_i^T - e_i^I) - (\mathbb{E}_i[e_i^T] - \mathbb{E}_i[e_i^I]) \approx c_\perp - c_\perp = 0$ となるため、推論コストをほぼ増やすことなくクロスモーダル整合が改善される。マルチモーダル文書に対しては、較正後の埋め込み上で同じ補間を適用する。図 [\[fig:setting1\]](#fig:setting1)b はこの過程を示している。実際に、この単純な較正が CLIP の性能を大きく向上させ、計算量を大幅に抑えつつ VLM2Vec をも上回ることを確認した。

## Evaluation Metrics

Retrieval 性能は、上位10件の検索文書の関連性と順位の双方を反映する広く用いられている指標である **NDCG@10**（Normalized Discounted Cumulative Gain {{CITE:11}}）を用いて評価する。NDCG@10 の値が高いほど性能が良いことを意味する。詳細は Appendix に示す。

# Retrieval with Heterogeneous Corpus 

![](assets/fig02.png)

**異種コーパスにおける retrieval.** **(a) Dataset Construction:** 確率 $p$ で、テキスト文書をそのテキストのスクリーンショット表現、または対になる画像にランダム置換することにより、異種コーパスを構築する。意味内容は不変であるため、完全なクロスモーダル整合を持つ retrieval system であれば、$p$ に依存せず同一の性能を維持すべきである。 **(b) Initial Results & Simulation:** 驚くべきことに、CLIP はテキストがスクリーンショットに置換されるにつれて U 字型の性能曲線を示す。この挙動は、CLIP の埋め込み空間におけるモダリティギャップに起因すると考える。クロスモーダル文書に人工的なペナルティを課すシミュレーション実験も同じ U 字型の傾向を再現し、この仮説を裏づける。 **(c) Method --- GR-CLIP:** 先行研究に基づき、テキスト埋め込みと画像埋め込みの平均中心化によりモダリティギャップを除去する単純な事後較正 **GR-CLIP** を提案する。 **(d) Improved Results:** GR-CLIP は U 字型曲線を平坦化し、retrieval 精度を大幅に改善して、はるかに少ない計算量で VLM2Vec baseline と同等以上の性能を達成する。 **(e) Generalization Across Models, Datasets, and Modalities:** 汎化性を評価するため、3種類の CLIP 変種、追加の3データセット、さらに3種類の他モダリティ（詳細は Appendix）にわたって GR-CLIP を検証する。いずれの場合も、知見と改善は一貫して成り立つ。

§2 で議論したように、まずは混合モダリティ検索という ablated setting から始める。これは、単一モダリティ文書（すなわちテキストのみ、あるいは画像のみ。図 [\[fig:setting1\]](#fig:setting1)a を参照）から成る異種コーパスである。この設定は、retrieval model がクロスモーダル整合の課題を効果的に処理できるかを評価するものである。

## Dataset Construction 

この設定に一致する既存データセットは存在しないため、我々はこのタスクに適した新規データセットを、合成スクリーンショットと画像置換という相補的な2つの戦略を用いて構築する。

**Screenshot replacement.** クエリとコーパス文書の双方がテキストである標準的なテキスト専用 retrieval データセットから出発し、テキスト文書を画像ベースのスクリーンショットとして合成的に描画する。具体的には、各テキスト文書 $d_i^T$ について、同一内容を含むスクリーンショット版 $d_i^I$ を生成し、確率 $p$ でそれに置換する（図 [\[fig:setting1\]](#fig:setting1)a）。この合成設定は意味内容を厳密に保存するため、制御された実験に理想的である。完全なクロスモーダル整合を持つモデルであれば、テキスト文書とスクリーンショット文書を埋め込み空間で類似に表現でき、したがって $p$ の変化にかかわらず retrieval 性能は不変であるべきである。この変換を NFCorpus {{CITE:3}} と SciFact {{CITE:30}} の2データセットに適用する。

**Real image replacement.** 画像・キャプション対を含むデータセットについては、確率 $p$ でテキストキャプション $d_i^T$ を対応する画像 $d_i^I$ に置換する。この設定はより現実的である一方、モダリティ間にわずかな意味差を導入する。それでも、基盤にある意味的整合を考えれば、retrieval 性能は置換比率 $p$ の違いに対して安定に保たれると期待される。この手法を用いて Google WIT {{CITE:27}} と MSCOCO {{CITE:18}} の2データセットを構築する。

## Initial Results & Simulation

まず、意味保存が厳密であるため、合成スクリーンショットを用いる設定に焦点を当てる。理想的には、完全なクロスモーダル整合を持つモデルであれば、スクリーンショットに置換された文書数にかかわらず、一貫した retrieval 性能を示すはずである。

**Models exhibit a U-shaped performance curve when mixing texts and screenshots.** 驚くべきことに、期待された平坦な傾向ではなく、U 字型の性能曲線（図 [\[fig:setting1\]](#fig:setting1)b）を観測した。スクリーンショットがテキスト文書をより多く置換するにつれて（$p$ が増加するにつれて）、性能は最初に低下する――$p=0$（全てテキスト）での 0.22 から、$p=0.99$（99% がスクリーンショット）での 0.02 までである。しかし、$p=1$（全てスクリーンショット）では性能が再び 0.36 に改善し、$p$ の関数として明確な U 字型を形成する。興味深いことに、CLIP は text-to-text retrieval（$p=0$）よりも text-to-image retrieval（$p=1$）で良い性能を示す。これは、おそらく訓練目的が cross-modal contrastive loss であり、unimodal retrieval に対する明示的最適化を含まないためである。

**The U-shape arises from the modality gap.** この U 字型性能をモダリティギャップに起因すると考える。第一に、モダリティギャップは intra-modal similarity のバイアスを生む。CLIP はテキスト埋め込みと画像埋め込みを共有空間で整合させるものの、テキストと画像のクラスターは依然として分離している（図 [\[fig:pull\]](#fig:pull)c）。その結果、intra-modal similarity スコアが体系的に高くなる（図 [\[fig:pull\]](#fig:pull)d）。第二に、このバイアスがランキングの歪みを引き起こす。スクリーンショットがより多くのテキスト項目を置換するにつれ、関連するスクリーンショットは低いクロスモーダル類似度のために不利になり、無関係なテキスト文書は単に intra-modal 整合性が高いという理由だけで上位に来る可能性がある。$p=0.99$ では、残存する少数のテキスト文書が関連性にかかわらずランキングを支配する。$p=1$ では全文書が画像となり、モダリティバイアスが消失するため性能が改善し――その結果として U 字型曲線が生じる。

**Push-down simulation confirms the hypothesis.** この説明を検証するため、全スクリーンショットに固定の類似度スコア 0 を割り当て、実質的にランキングリストの最下位へ押し下げることで、モダリティに起因するランキングバイアスをシミュレートした。その結果得られた性能曲線（図 [\[fig:setting1\]](#fig:setting1)b）は実際の CLIP 曲線と非常に近く、一致しており、U 字型はモダリティギャップに起因するランキング歪みによって生じるという仮説を裏づける。

## GR-CLIP with Improved Results

モダリティギャップが性能低下を引き起こすのであれば、このギャップを緩和して性能を改善すべきである。

**Closing the modality gap via mean-shift calibration.** モダリティギャップを埋め込み空間における平均シフトとして特徴づけた先行研究 {{CITE:36}} に従い、我々は軽量な事後較正手法 GR-CLIP を提案する。テキストモダリティと画像モダリティの平均埋め込みを計算し、それぞれの表現から差し引くことで、共有空間において両モダリティを中心化する。これによりモダリティ間の分離が低減される（図 [\[fig:setting1\]](#fig:setting1)d；導出は §2 を参照）。

**Flattened curves and improved performance after removing the modality gap.** GR-CLIP を適用した後、retrieval 性能は大きく改善し、U 字型曲線は異なる $p$ 値にわたって平坦化する（図 [\[fig:setting1\]](#fig:setting1)e）。GR-CLIP はまた、VLM2Vec {{CITE:12}} を上回る。VLM2Vec は同様に平坦な性能を達成する近年の生成埋め込み手法であるが、75$\times$ 多い計算資源を要する。これらの結果は、モダリティギャップの低減が、混合モダリティ retrieval 設定において CLIP ベースのモデルを改善するうえで、効率的かつ有効であることを示している。

## Generalization across Models, Datasets, and Modalities

我々の知見の一般性を評価するため、GR-CLIP を異なるモデル、データセット、モダリティにわたって検証する。**1) Across models:** 図 [\[fig:setting1\]](#fig:setting1)f（最上段）に示すように、U 字型曲線は OpenAI CLIP {{CITE:25}}、OpenCLIP {{CITE:33}}、SigLIP {{CITE:34}} の3つの CLIP 変種で観測される。GR-CLIP は一貫して曲線を平坦化し、性能を改善する。**2) Across datasets:** 図 [\[fig:setting1\]](#fig:setting1)f（2段目）に示すように、本研究の知見は合成スクリーンショット設定（NFCorpus {{CITE:3}} と SciFact {{CITE:30}}）を超えて、現実世界のデータセット（Google WIT {{CITE:27}} と MSCOCO {{CITE:18}}）にも拡張される。**3) Across modalities.** また、text-to-video および text-to-audio retrieval への一般化も検証する。結果は Appendix に示す。

# Retrieval with Multimodal Documents 

![](assets/fig03.png)

**マルチモーダル文書における retrieval.** **(a) Dataset Construction:** 各文書は画像とテキストの両方を含み、埋め込みはモダリティ固有特徴を融合して得る。モデルがマルチモーダル情報を統合する能力を評価するため、融合係数 $\alpha$ を変化させる。 **(b) Results:** GR-CLIP は3つのモデル変種および4つのデータセットにわたり一貫して CLIP を上回り、モダリティギャップがマルチモーダル融合を妨げること、そしてそれを除去することが retrieval 性能を大きく向上させることを示している。

ここでは §3 の補完的な ablation を考える。この場合、retrieval コーパスは homogeneous であるが、各文書は画像とテキストの両方のモダリティを含むマルチモーダル文書である（図 [\[fig:setting2\]](#fig:setting2)a）。この設定は、画像とテキストを併用することでどちらか一方のみより豊かな意味的手がかりが得られる状況において、モデルがマルチモーダル情報を融合する能力を評価するものである。

## Dataset Construction

我々は、各文書が画像成分とテキスト成分の両方を含む、4つの実世界マルチモーダルデータセットを用いる。**OVEN** {{CITE:10}} は、クエリからマルチモーダル文書への形式を採用した既存の検索ベンチマークである。**MSCOCO** {{CITE:18}} および **VisualNews** {{CITE:19}} では、各画像に1つ以上の短いキャプションが対応付けられている。そこで、短いキャプションのうち1つをクエリとしてランダムにサンプルし、画像と短いキャプションを条件としてGPTにより長いキャプションを生成して文書を構成する。**Google WIT** {{CITE:27}} では、各画像にタイトル、短いキャプション、長いキャプションが付与されている。ここでは、タイトルと短いキャプションの連結をクエリとし、画像と長いキャプションを結合したものを文書として用いる。これらのデータセットは、多様なドメインにまたがる自然に対応付けられた画像・テキストデータを含む。各文書は相補的な視覚的・言語的シグナルを提供するため、モダリティ融合の評価に適している。

## Results

モダリティギャップがモダリティ融合に与える影響を分析するため、融合埋め込みに対する各モダリティの寄与を制御する融合重み $\alpha \in [0, 1]$ を変化させる。すなわち、$e_i = \alpha \cdot e_i^T + (1 - \alpha) \cdot e_i^I$ である。

**モダリティギャップは有効な融合を妨げる。** Figure [\[fig:setting2\]](#fig:setting2)b の青い曲線に示すように、元のCLIP埋め込みでは、性能は通常、単一モダリティの両端（$\alpha = 0$ または $\alpha = 1$）のいずれかで最大となり、中間の $\alpha$ による融合はこれらの単一モダリティベースラインを上回れない。これは、モダリティギャップがモダリティ間の有効な統合を妨げていることを示唆する。すなわち、線形補間はしばしば融合特徴を埋め込み空間内の準最適領域へ押しやり、意味的品質を劣化させ、その結果、画像のみまたはテキストのみを用いる場合よりも性能が悪化する。

**モダリティギャップを解消すると融合は大幅に改善する。** モダリティギャップが除去されると（§3で述べた平均シフト校正による）、融合は大幅に有効になる。Figure [\[fig:setting2\]](#fig:setting2)b の橙色の曲線に示すように、性能は中間の $\alpha$ で最大となり、両方の単一モダリティベースラインを上回る。これは、ギャップ除去モデルであるGR-CLIPが、画像とテキストからの相補的情報を適切に統合し、より強力な全体表現を獲得していることを示している。

**モデルおよびデータセットをまたいだ一般化。** これらの知見は、OpenAI CLIP {{CITE:25}}、OpenCLIP {{CITE:33}}、SigLIP {{CITE:34}} を含む複数のCLIP系モデルにわたり、また OVEN {{CITE:10}}、VisualNews {{CITE:19}}、Google WIT {{CITE:27}}、MSCOCO {{CITE:18}} といった多様なデータセットにわたって一貫して成り立つ。いずれの場合も、モダリティギャップを除去することで融合品質が改善し、それにより検索性能が向上する。

# Mixed Modality Search 

![](assets/fig04.png)

**Mixed modality search.** **(a) Dataset Construction:** 我々は、コーパスが異種でありマルチモーダル文書を含むベンチマーク **MixBench** を導入する。これは、検索エンジンにとって最も現実的な設定を反映したものである。**(b) Results:** 4つのMixBenchサブセットと5つのCLIP系モデル全体において、GR-CLIPはモダリティギャップを除去することで元のCLIPモデルに対して大幅な改善を達成し、計算コストを大幅に抑えつつ最先端性能を実現する。

ここでは、§3と§4の知見を統合し、最も現実的なシナリオへと分析を拡張する。すなわち、コーパス内の文書が純粋なテキスト、純粋な画像、あるいはその両方の組み合わせであり得る mixed modality search である（Figure [\[fig:setting3\]](#fig:setting3)a）。この設定は、検索システムが異種かつ可変的にマルチモーダルなコンテンツを対象に動作しなければならない、実世界の検索エンジンの課題を反映している。

## MixBench: Dataset Construction 

この現実的設定における研究を支えるため、我々は mixed modality search 専用に設計された新たなベンチマーク **MixBench** を導入する。MixBench は、4つの実世界マルチモーダルデータセット---**OVEN** {{CITE:10}}、**MSCOCO** {{CITE:18}}、**Google WIT** {{CITE:27}}、**VisualNews** {{CITE:19}}---から構築されており、これらは多様なドメインにまたがり、自然に整合した画像・テキスト内容を含む。これらのデータセットをクエリ・文書検索形式へ変換する手順は §4 に詳述する。MixBench では、文書は画像のみ、テキストのみ、または画像・テキスト対から構成され得る。バランスの取れた分布を保証するため、文書タイプ（純画像、純テキスト、マルチモーダル）を 1:1:1 の比率でサンプリングする。

## Results

Figure [\[fig:setting3\]](#fig:setting3)b は、元のCLIP系モデルおよびギャップ除去版（GR-CLIP）を用いた、4つのMixBenchサブセットにおける結果を示す。

**GR-CLIPはモダリティギャップを解消した後、元のCLIPに対して大幅な改善を示す。** 先の知見と一貫して、平均シフト校正によってモダリティギャップを除去すると、CLIP {{CITE:25}}、OpenCLIP {{CITE:33}}、SigLIP {{CITE:34}} を含む全ての評価モデルにおいて、MixBenchで有意な性能向上が得られる。これらの改善は、OVEN {{CITE:10}}、VisualNews {{CITE:19}}、Google WIT {{CITE:27}}、MSCOCO {{CITE:18}} という4つのデータセット全体に一般化される。平均すると、GR-CLIPは NDCG@10 において最大26ポイントの向上を達成し、追加の計算コストはほぼ無視できる。これらの向上は、§3および§4で示した、クロスモーダル整合とマルチモーダル融合の改善によって駆動されており、これは mixed modality retrieval における性能にとって極めて重要である。

**GR-CLIPは大幅に低い計算量で最先端性能を達成する。** 注目すべきことに、GR-CLIPは、75$\times$ 少ない計算資源しか用いずに、強力なベースラインであるVLM2Vecを上回る。唯一の例外はMSCOCOであり、これは論文中で報告されている通りVLM2Vecが学習済みのデータセットである。これらの結果は、mixed modality search のために真に共有された埋め込み空間を構築することの重要性を強調する。これは有効な検索システムにとって本質的である一方、しばしば見落とされがちな能力である。

# Related Work

**単一モダリティおよびクロスモーダル検索。** 単一モダリティ検索（例: text-to-text, image-to-image）およびクロスモーダル検索（例: text-to-image, image-to-text）は、先行研究において広く研究されてきた {{CITE:26}}{{CITE:13}}{{CITE:14}}{{CITE:15}}{{CITE:25}}。そして現在では、Google や Bing など多くの大規模検索エンジンを支えている。これらの設定における中心的課題は、クエリと文書の間で正確な類似度比較を可能にする有効な表現空間を構築することである。これに対し我々は、クエリと文書の双方が複数モダリティにまたがり得る、より複雑な mixed modality retrieval 設定に焦点を当てる {{CITE:29}}。この設定は十分に探究されていないが、極めて実用的である。そこでは、モダリティ境界をまたいで意味的類似度を有意味に測定できる共有表現空間を設計するという新たな課題が生じる。

**マルチモーダル表現学習。** マルチモーダル表現学習は長らく、異なるモダリティの情報を一貫した埋め込み空間へ統合することを目指しており、初期の研究では early fusion と late fusion の技術が検討されてきた {{CITE:24}}{{CITE:28}}{{CITE:16}}{{CITE:22}}{{CITE:5}}。近年では、マルチモーダル対照学習が強力な枠組みとして現れ、対照目的関数を通じて対応する画像・テキスト表現を整列させている {{CITE:9}}{{CITE:25}}{{CITE:34}}{{CITE:33}}。CLIP {{CITE:25}} のような、数百万組の対応例で学習されたモデルは、モダリティ間で意味的に整列した埋め込みを学習する卓越した能力を示している。さらに最近では、生成的 vision-language models（VLMs）を検索へ適用することへの関心が高まっており {{CITE:12}}{{CITE:7}}、それらを埋め込みモデルとして再利用する試みが進んでいる {{CITE:2}}{{CITE:23}}。これらのモデルはより柔軟で多様なマルチモーダル入力を扱える一方、しばしばより大きな計算量を要する。本研究では、CLIP {{CITE:25}} と VLM2Vec {{CITE:12}} という二つのパラダイムを mixed modality retrieval 設定の下で評価する。驚くべきことに、我々は、CLIPに適用した単純な校正手法が、はるかに少ない計算量にもかかわらずVLM2Vecを上回り得ることを見出した。

**マルチモーダル対照学習におけるモダリティギャップ。** 近年の研究 {{CITE:17}}{{CITE:36}}{{CITE:35}} は、対照的マルチモーダル埋め込み空間において持続的なモダリティギャップが存在することを明らかにした。すなわち、対照学習がそれらを整列させるよう設計されているにもかかわらず、画像埋め込みとテキスト埋め込みは別々にクラスタ化する傾向がある。このギャップは、モデル初期化と対照最適化の組み合わせに起因するとされている。理論的には、モダリティギャップは、画像およびテキストの部分空間の双方にほぼ直交する定数オフセットベクトルとして特徴付けられている {{CITE:36}}{{CITE:35}}。この知見に基づき、我々は単純だが有効な mean-reduction calibration を採用する。これは、類似度を計算する前に埋め込みからモダリティ固有の平均を除去するものである。この軽量な後処理手法はモダリティギャップを除去し、mixed modality search 設定において大幅な性能向上をもたらす。

# Conclusion

本研究は、現実的でありながら十分に探究されていない mixed modality search の問題に取り組んだ。ここでは、クエリが、マルチモーダル文書を含む異種コーパスから意味的に関連するコンテンツを検索しなければならない。我々はこの設定におけるCLIPベースモデルの挙動を分析し、重要な制約を特定した。すなわち、埋め込み空間におけるモダリティギャップが、クロスモーダル整合とマルチモーダル融合の双方を妨げているのである。これに対処するため、我々はモダリティギャップを除去し、検索性能を大幅に向上させる単純かつ有効な手法 **GR-CLIP** を導入した。我々の知見は、信頼性が高く効率的な mixed modality search のためには、真に統一されたマルチモーダル表現が重要であることを示している。

# Acknowledgments 

本研究は Hoffman-Yee Research Grants により一部支援された。S.Y. は Chan Zuckerberg Biohub --- San Francisco Investigator である。

# Limitations 

本研究は、モダリティギャップを除去することで、GR-CLIP が多様なデータセット、モデル変種、およびモダリティにわたる mixed modality search 設定において大幅な性能向上を達成できることを示したが、なおいくつかの限界が残されており、これは将来研究の有望な方向性を示している。第一に、画像とテキストの両モダリティを含む現実的シナリオを考慮しているものの、各文書は1枚の画像と1つのテキストセグメントに制限されている。Webページや科学論文のような、より複雑で画像とテキストが交錯した複数画像・複数テキスト文書へ評価を拡張すれば、より厳密で包括的な評価が可能となるであろう。第二に、GR-CLIP は生成的埋め込みモデル VLM2Vec を、はるかに少ない計算量で上回るものの、CLIP を基盤としており、きめ細かなモダリティ相互作用をモデル化しない。そのため、生成的埋め込みモデルが捉え得るより深いクロスモーダル統合の機会を取り逃がす可能性がある。これを踏まえると、VLM2Vec のような生成的埋め込みモデルにおけるモダリティギャップの原因を調査し、それを低減する方法を開発することは、より強力で統一的なマルチモーダル表現に向けた重要かつ未開拓の研究方向である。それにもかかわらず、本研究は、現実的設定における mixed modality search の問題を定義し、それに対処する重要な第一歩を踏み出しており、効果的な検索のために真に統一された埋め込み空間を構築することの重要性を示し、この新興分野における将来の進展の基盤を築くものである。

# Code Availability 

全てのコードは匿名のGitHubリポジトリで公開されており、本論文の全実験を再現できる: <https://github.com/yuhui-zh15/MixedModalitySearch/>.

# Data Availability 

本研究で使用した全データセットは、この新興分野における今後の研究を促進するため、匿名でHugging Face上にホストされている: <https://huggingface.co/datasets/mixed-modality-search/MixBench2025>。

# Compute Resource 

全実験は、40GBのメモリを持つ単一のNVIDIA A100 GPUを用いて実施した。全実験は推論のみであり、必要な計算資源は最小限である。

# Overview 

以下にAppendixの概要を示す。

- §8 では、モダリティおよび評価指標をまたぐ追加の一般化結果を示す。

- §9では、方法の詳細を述べ、再現性のための擬似コードを含める。

- §10では、使用したモデルの詳細を説明する。

- §11では、NDCGを含む評価指標を説明する。

- §12では、使用したデータセットと関連する前処理手順を概説する。

- §13では、MixBenchにおけるCLIPとGR-CLIPの比較ケーススタディを含める。

# モダリティおよび指標をまたぐ一般化

本論文では、評価指標としてNDCG@10を用い、モダリティ間ギャップを解消することが画像-テキストデータにおける混合モダリティ検索性能を大幅に改善することを示した。ここでは、追加結果として、(1) 画像とテキスト以外のモダリティへの本手法の一般化可能性、および (2) 代替評価指標の下での結論の頑健性を示す。

## モダリティをまたぐ一般化

本論文の図[\[fig:setting1\]](#fig:setting1)eは、画像-テキストモダリティに対する結果を示している。図[\[fig:figone_add\]](#fig:figone_add)では、この分析を追加のモダリティ対へ拡張する。具体的には、video-text（MSVDデータセット上のViCLIP {{CITE:31}}）、audio-text（Clotho {{CITE:6}}データセット上のCLAP {{CITE:32}}）、および追加のimage-text設定（Nights {{CITE:8}}データセット上のOpenAI CLIP {{CITE:25}}）に対する検索性能（NDCG@10）を報告する。すべての場合において、元のCLIPベースの結果には一貫してU字型曲線が観察されるが、GR-CLIPを適用してモダリティ間ギャップを除去すると、この曲線は著しく平坦化する。この傾向は、図[\[fig:setting1\]](#fig:setting1)eにおける画像-テキストおよびスクリーンショット実験で観察された挙動と非常によく一致しており、モダリティ間ギャップの影響と、多様なモダリティにわたる本手法の広範な適用可能性を強く裏付けるものである。

![](assets/fig05.png)

**モダリティをまたぐ一般化。** GR-CLIPは、モダリティ間ギャップに起因するU字型曲線を一貫して緩和し、性能を大幅に改善する。これにより、多様なモダリティ対に対する高い一般化可能性が示される。

## 指標をまたぐ一般化

本論文では、主要な評価指標としてNDCG@10を採用した。GR-CLIPの頑健性をさらに評価するため、NDCG@100およびRecall@1を含む追加指標へ分析を拡張する。表1は、3つの指標すべてにわたるMixBenchでの結果を示しており、GR-CLIPによって観測される改善が、評価基準に依存せず一貫していることを示している。図[\[app:fig:ndcg100\]](#app:fig:ndcg100)および図[\[app:fig:recall1\]](#app:fig:recall1)は、それぞれNDCG@100およびRecall@1を用いて§3および§4の分析をさらに拡張したものであり、同様に我々の結果の一貫性を確認している。

| **Method** |  | **MSCOCO** | **OVEN** | **VisualNews** |
|:---|:---|:---|:---|:---|
| CLIP-B/16 | 0.478/0.505/0.443 | 0.388/0.426/0.292 | 0.354/0.398/0.209 | 0.563/0.604/0.498 |
| CLIP-L/14 | 0.505/0.516/0.454 | 0.426/0.490/0.329 | 0.389/0.431/0.253 | 0.596/0.656/0.525 |
| OpenCLIP-B/16 | 0.551/0.563/0.519 | 0.570/0.615/0.489 | 0.385/0.426/0.229 | 0.643/0.693/0.543 |
| OpenCLIP-L/14 | 0.566/0.585/0.536 | 0.605/0.662/0.540 | 0.387/0.445/0.265 | 0.653/0.733/0.567 |
| SigLIP-400m | 0.546/0.566/0.523 | 0.327/0.374/0.260 | 0.372/0.428/0.271 | 0.385/0.475/0.366 |
| VLM2Vec(LLaVANext) | 0.586/0.616/0.481 | **0.769/0.798/0.645** | 0.398/0.443/0.254 | 0.744/0.794/0.662 |
| VLM2Vec(Qwen) | 0.632/0.660/0.519 | 0.753/0.778/0.633 | 0.412/0.467/0.244 | 0.734/0.784/0.653 |
| GR-CLIP-B/16 | 0.603/0.642/0.524 | 0.636/0.690/0.523 | 0.406/0.459/0.240 | 0.726/0.768/0.645 |
| GR-CLIP-L/14 | 0.648/0.678/0.555 | 0.656/0.708/0.547 | 0.465/0.523/0.296 | 0.754/0.770/0.661 |
| GR-OpenCLIP-B/16 | 0.636/0.666/0.572 | 0.668/0.751/0.589 | 0.434/0.490/0.253 | 0.758/0.783/0.664 |
| GR-OpenCLIP-L/14 | 0.678/0.704/0.604 | 0.699/0.784/0.629 | 0.467/0.525/0.282 | **0.796/0.814/0.715** |
| GR-SigLIP-400m | **0.692/0.722/0.608** | 0.696/0.732/0.548 | **0.532/0.581/0.328** | 0.769/0.793/0.671 |
****MixBenchにおける全指標の詳細結果。** 各セルはNDCG@10、NDCG@100、Recall@1を報告する。最良結果は太字で示している。指標をまたぐ一貫した性能は、我々の手法が異なる評価基準に対して頑健であることを示す。GR-CLIPがMSCOCO上でVLM2Vecを下回るのは、VLM2VecがMSCOCOで学習されているためである。 **

![](assets/fig06.png)

**NDCG@100を評価指標として用いた、本論文の図[\[fig:setting1\]](#fig:setting1)の再現。**

![](assets/fig07.png)

**NDCG@100およびRecall@1を評価指標として用いた、本論文の図[\[fig:setting2\]](#fig:setting2)の再現。**

# 方法の詳細

§2.3で導入したように、GR-CLIPは各モダリティのグローバル平均ベクトルを減算することでモダリティ間ギャップを緩和する。具体的には、クエリ平均$\bar{e}_q$、文書テキスト平均$\bar{e}^T$、文書画像平均$\bar{e}^I$の3つの平均ベクトルを計算する：

$$\bar{e}_q = \mathbb{E}_{q \sim \mathcal{Q}} [f^T(q)], \quad
\bar{e}^T = \mathbb{E}_{d^T \sim \mathcal{D}_{\text{text}}} [f^T(d^T)], \quad
\bar{e}^I = \mathbb{E}_{d^I \sim \mathcal{D}_{\text{image}}} [f^I(d^I)].$$

我々は、構造的・意味的差異を考慮するため、クエリ平均$\bar{e}_q$とテキスト文書平均$\bar{e}^T$を区別する。クエリはしばしば短く疑問文的である一方、文書は通常より長く記述的である。この区別は、アライメントバイアスを低減し、検索性能を向上させるうえで重要である。

データセット横断での一般化を保証し、テストセットの情報漏洩を防ぐために、我々は各データセットのテストセットを用いて個別に平均を推定するのではなく、複数データセットの訓練セットから統一平均ベクトルを計算する。これらの統一平均は、その後すべてのテストセットに一貫して適用する。

**クエリ平均（$\bar{e}_q$）:** MSCOCO、Google WIT、NFCorpus、VisualNewsの訓練分割から、約10000個のテキストクエリをサンプルする。これらを$f^T$で符号化し、平均化することでグローバルなクエリ平均$\bar{e}_q$を得る。

**文書テキスト平均（$\bar{e}^T$）:** MSCOCO、OVEN、Google WIT、VisualNewsの訓練分割から、約10000個の長文テキスト文書または記述的キャプションをサンプルする。これらを$f^T$で符号化し、平均化することで文書テキスト平均$\bar{e}^T$を得る。

**文書画像平均（$\bar{e}^I$）:** $\bar{e}^I$を計算するために、MSCOCO、OVEN、Google WIT、VisualNewsの訓練分割から10000枚の画像をサンプルする。これらを$f^I$で符号化し、平均化することで文書画像平均を得る。

**OVEN固有のクエリ平均（$\bar{e}_q^{\text{OVEN}}$）:** OVENのクエリは特に短いため、OVENの訓練分割から2000個のクエリをサンプルして、データセット固有のクエリ平均を構成する。

**その他のモダリティ平均:** MSVD（video-text）、Clotho（audio-text）、およびSciFactとNFCorpusにおけるスクリーンショット形式の文書（screenshot-text）などの非画像-テキストデータセットについては、モダリティごとに2500個の訓練例を用いてモダリティ固有の平均を計算する。

完全な**GR-CLIP**アルゴリズムを以下に要約する：

2

\
キャリブレーション集合：$\mathcal{Q}'$、$\mathcal{D}'$\
クエリ集合 $\mathcal{Q} = \{q_1, \dots, q_n\}$（テキストのみ）\
文書集合 $\mathcal{D} = \{d_1, \dots, d_m\}$（各文書はテキスト、画像、またはその両方）\
事前学習済みエンコーダ $f^T$, $f^I$, 補間係数 $\alpha \in [0,1]$

*// Step 1: $\mathcal{Q}', \mathcal{D}'$ からグローバル平均を事前計算する* $\bar{e}_q \gets \mathbb{E}_{q \sim \mathcal{Q}'} [f^T(q)]$ $\bar{e}^T \gets \mathbb{E}_{d^T \sim \mathcal{D}'_{\text{text}}} [f^T(d^T)]$ $\bar{e}^I \gets \mathbb{E}_{d^I \sim \mathcal{D}'_{\text{image}}} [f^I(d^I)]$

*// Step 2: クエリ埋め込みを符号化する* $e_{q_i} \gets f^T(q_i) - \bar{e}_q$

*// Step 3: 文書埋め込みを符号化する* $e_{d_j} \gets f^T(d_j) - \bar{e}^T$ $e_{d_j} \gets f^I(d_j) - \bar{e}^I$ $e_{d_j} \gets \alpha f^T(d_j^T) +(1{-}\alpha) f^I(d_j^I)$ $- [\alpha \bar{e}^T + (1{-}\alpha) \bar{e}^I]$

*// Step 4: 検索* $s(q_i,d_j) \gets \frac{e_{q_i} \cdot e_{d_j}}{\|e_{q_i}\| \cdot \|e_{d_j}\|}$ $\text{Ranks} \gets \text{argsort}(s, \text{descending})$ $\text{Ranks}$

# モデルの詳細

本節では、実験で使用したすべてのモデルについて、正確なバージョンとチェックポイントへのリンクを示す。CLIPベースのモデルについては、**OpenAI CLIP** {{CITE:25}}の2種類、**OpenCLIP** {{CITE:33}}の2種類、および**SigLIP-400M** {{CITE:34}}を含める。

VLM2Vecフレームワークについては、2種類を用いる。1つは**LLaVA-Next** {{CITE:20}}に基づくものであり、これは本論文で報告した結果のバックボーンとして用いられている {{CITE:12}}。もう1つは最新の公式リリースである**Qwen-VL** {{CITE:1}}に基づくものであり、公式リポジトリによればMMEB {{CITE:12}}ベンチマークで最高性能を達成する。

さらに、非画像-テキストモダリティについては、video-text検索タスクに**ViCLIP**{{CITE:31}}を、audio-text検索タスクに**CLAP**{{CITE:32}}を用いる。

すべてのモデルのチェックポイントリンクを以下に示す。

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

本論文では、広く採用されているNDCG@10を評価指標として用いる。ここでは、この指標の詳細な計算過程を示す。

位置$K$までの検索結果のランキングリストが与えられたとき、NDCG@$K$は次式で計算される：

$$\text{NDCG@}K = \frac{1}{\text{IDCG@}K} \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$

ここで$\text{rel}_i$は順位$i$にあるアイテムの関連度スコアを表し、IDCG@$K$は理想的なDCG、すなわち上位$K$件について可能な最大のDCGであり、アイテムを関連度の降順に並べ替えて計算される：

$$\text{IDCG@}K = \sum_{i=1}^{K} \frac{2^{\text{rel}_i^\star} - 1}{\log_2(i + 1)}$$

ここで$\text{rel}_i^\star$は、理想ランキングにおける$i$番目に高い関連度スコアである。

NDCG@10の値域は0から1であり、1は完全なランキングを意味する。

# データセットの詳細

本節では、§3、4、および5における検索実験を支えるために、各データセットがどのように処理されるかについて追加の詳細を示す。各データセットについて、元のデータ形式（*Before*）と、本フレームワークで用いた修正版（*After*）を区別する。また、主要な後処理手順についても述べる。

**NFCorpus {{CITE:3}}, SciFact {{CITE:30}}:**\
*Before:* 短いテキストクエリと、関連する長文テキスト文書の組。\
*After:* 短いテキストクエリは保持し、長文テキスト文書はOpenCVを用いてスクリーンショットとしてレンダリングする。これにより、クエリに対して元のテキスト文書またはそのレンダリング済みスクリーンショットのいずれかを検索対象とできる。

**Google WIT {{CITE:27}}:**\
*Before:* 各サンプルは、ページタイトル、長いページ説明、参照画像、および画像の参照説明を含む。\
*After:* ページタイトルと画像参照説明を連結してクエリを形成する。ページ説明は長文テキスト文書として用い、関連する画像は画像文書として用いる。

**OVEN {{CITE:10}}:**\
*Before:* 各クエリは画像-テキスト対から成り、検索対象も画像-説明対である。\
*After:* 画像成分またはテキスト成分のいずれかが単独でクエリに回答しうるため、画像とキャプションの両方を有効な独立文書として扱う。クエリは変更しない。

**MSCOCO {{CITE:18}}:**\
*以前:* 各画像は5つのキャプションと対応している。\
*以後:* 1つのキャプションをクエリとしてサンプリングする。残りのキャプションは、サンプリングしたキャプションの内容を保持したまま、GPT-4o により長文記述を構成するために用いる。この長文記述をテキスト文書とし、対応する画像を画像文書とする。

**VisualNews {{CITE:19}}:**\
*以前:* 各画像は短いニュース風キャプションと対応している。\
*以後:* 元の VisualNews データセットに含まれる画像と、それに対応する記事を GPT-4o により共同で解析する。視覚的内容と記事本文の双方に基づき、GPT-4o は元のキャプションを拡張した詳細な説明段落を生成し、これをテキスト文書として用いる。画像を画像文書とし、元のキャプションをクエリとして保持する。

**Clotho {{CITE:6}}:**\
*以前:* 各音声クリップは、意味的に類似した複数のキャプションと対応している。\
*以後:* 1つのキャプションをクエリとして選択し、別の意味的に類似したキャプション（GPT-4o が選択したもの）をテキスト文書として用いる。音声クリップ自体を音声文書として用いる。

**MSVD {{CITE:4}}:**\
*以前:* 各動画は、意味的に類似した複数のキャプションと対応している。\
*以後:* 1つのキャプションをクエリとして用い、別の意味的に類似したキャプション（GPT-4o が選択したもの）をテキスト文書として用いる。動画を動画文書として扱う。

**Nights {{CITE:8}}:**\
*以前:* 各画像は視覚的に類似した画像と対応している。\
*以後:* 1つの画像をクエリとして用いる。GPT-4o がこの画像を観察して簡潔なタイトルを生成し、これをテキスト文書として用いる。対応する画像を画像文書とする。

**VLM2Vec input format:** **VLM2Vec** {{CITE:12}} では、埋め込み生成の指示としてプロンプトを必要とする。具体的には、各 *Query* に対して、複数モダリティからなる異種コーパスから検索を行う setting 1 および 3 では、`‘‘Retrieve a relevant item that represents: {Query}\n’’` を用いる。Setting 2 のように、検索対象が image-text ペアからなる同種コーパスである場合には、`‘‘Retrieve an image-description pair that represents: {Query}\n’’` を用いる。Documents は元のデータセットで指定された形式に従う。

**CLIP input format:** **CLIP** ベースのモデル {{CITE:25}}{{CITE:34}}{{CITE:33}}{{CITE:31}}{{CITE:32}} および **GR-CLIP** については、指示文を適用しない。Queries と documents は、変更を加えずにそれぞれの CLIP text encoder および image encoder に直接入力する。

Table 2 は、各データセットの主要な特徴、すなわち retrieval setting、queries と corpora のモダリティ構成、および評価例の総数を要約したものである。

| **Dataset** | **Queries** | **Documents** | **Setting No.** | **\# of Queries** | **\# of Documents** |
|:---|:--:|:--:|:--:|:--:|:--:|
| Google WIT {{CITE:27}} | T | T / I / I + T | 1,2,3 | 1000 | 4423 |
| OVEN {{CITE:10}} | T + I | T / I / I + T | 1,2,3 | 1000 | 1000 |
| MSCOCO {{CITE:18}} | T | T / I / I + T | 1,2,3 | 984 | 984 |
| VisualNews {{CITE:19}} | T | T / I / I + T | 1,2,3 | 981 | 981 |
| SciFact {{CITE:30}} | T | T / S | 1 | 300 | 5183 |
| NFCorpus {{CITE:3}} | T | T / S | 1 | 323 | 3633 |
| MSVD {{CITE:4}} | T | T / V | 1 | 670 | 670 |
| Clotho {{CITE:6}} | T | T / A | 1 | 1046 | 1046 |
| Nights {{CITE:8}} | I | I / T | 1 | 1000 | 1000 |

**本実験で用いたデータセットの概要。** 各データセットについて、retrieval setting、クエリと文書に含まれるモダリティ（T = text, I = image, S = screenshot, V = video, A = audio）、および評価に用いた query-document ペア数を示す。 **

# Case Studies 

以下では、MixBench の各サブセットに関する case study を示す。これは同時に、本データセットの可視化としても機能する。各例のクエリについて、ベースラインである OpenAI CLIP-L/14 と提案手法 GR-CLIP-L/14 の双方における Top-5 の検索結果を示す。各検索文書には、そのモダリティ（[text]{style="color: Orange"}, [image]{style="color: Magenta"}, または [multimodal]{style="color: Green"}）、クエリに対する cosine similarity、ならびに **ground-truth** の関連項目であるか否かを付記する。

これらの例示結果は、MixBench データセットの多様性と、mixed modality search における GR-CLIP の有効性の双方を示している。クエリのモダリティに一致する文書を取得しがちな元来の CLIP モデルとは異なり、GR-CLIP はモダリティ間の隔たりを効果的に橋渡しし、モダリティに依存せず、クエリの意味的意図をより正確に反映する結果を取得する。

## Google WIT {{CITE:27}}

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

レバノン代表サッカーチームは、レバノンサッカー協会によって統括され、1933年の結成以来、アソシエーション・フットボールにおいてレバノンを代表してきた。チームは大陸レベルではアジアサッカー連盟、世界的にはFIFAの管轄下にある。レバノンは FIFA ワールドカップ出場権をまだ獲得していないが、アジアカップには2度出場している。すなわち、開催国であった2000年大会と、予選を通過して初めて出場した2019年大会である。レバノンの主要会場はベイルートの Camille Chamoun Sports City Stadium であるが、Sidon の Saida International Stadium など他の会場でも試合を行う。1934年、レバノンはルーマニアの CA Timișoara と初戦を戦ったが、これは FIFA により公認されなかった。レバノンが FIFA 公認の試合を行ったのは、1940年に Mandatory Palestine と対戦したのが最初である。2014年ワールドカップ予選では、2011年にホームで South Korea に 2--1 で勝利したことにより、レバノンは初めて最終予選ラウンドに進出したが、グループ最下位に終わり、2014 FIFA World Cup 出場はならなかった。2019 Asian Cup では、レバノンは初めてノックアウトステージ進出にあと一歩まで迫った。\
*Rank No.4*, *Cosine Similarity* = 0.1723, *Modality* = [text]{style="color: Orange"}

This is a list of properties and historic districts in Winchester, Massachusetts, that are listed on the National Register of Historic Places. The locations of National Register properties and districts may be seen in an online map by clicking on \"Map of all coordinates.\" This National Park Service list is complete through NPS recent listings posted July 17, 2020.\
*Rank No.5*, *Cosine Similarity* = 0.1708, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig09.png)

This list is of that portion of the National Register of Historic Places designated in Essex County, Massachusetts. The locations of these properties and districts for which the latitude and longitude coordinates are included below, may be seen in a map. There are more than 450 designated properties in the county, including 25 that are further designated as National Historic Landmarks. The municipalities of Andover, Gloucester, Ipswich, Lawrence, Lynn, Methuen, and Salem are to be found on a separate list of the more than 200 identified here, except two properties are split between Methuen and Lawrence, and one between Lynn and Nahant; these entries appear on more than one list. This National Park Service list is complete through NPS recent listings posted August 14, 2020.

## MSCOCO {{CITE:18}}

*[Query:]{style="color: blue"}* A woman in a room with a cat.\

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.5044, *Modality* = [text]{style="color: Orange"}

木目調の明るいキャビネットと黒い御影石のカウンタートップを備えたキッチンである。4口コンロ付きの黒いストーブ、上部に設置された電子レンジ、黒い冷蔵庫が含まれている。床は温かみのある木の色調である。\
*Rank No.2*, *Cosine Similarity* = 0.4605, *Modality* = [text]{style="color: Orange"}

猫が閉じた便器の蓋の上に乗っており、やや不快そうに見える。便器は淡い色の壁のある浴室にある。便器のそばにはかごまたは容器がある。猫の尾が見えており、警戒しているか、あるいは驚いているように見える。\
*Rank No.3*, *Cosine Similarity* = 0.4445, *Modality* = [text]{style="color: Orange"}

長いホットドッグが、木製のテーブルの上に置かれた白い紙皿の上のバンズに載っている。ホットドッグはバンズの両端からはみ出している。\
*Rank No.4*, *Cosine Similarity* = 0.4160, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig10.png)

温かく居心地のよいリビングルームにはクリスマス装飾が施され、暖炉のそばには銀色のティンセルで飾られたクリスマスツリーがある。部屋には、赤いカーペットの上に散らばったラッピング済みの贈り物が多数置かれている。マントルピースには、祝祭感を添えるオーナメントや靴下が飾られている。クッションの置かれた快適なベージュのソファが、雑誌の載ったコーヒーテーブルのそばにある。天井はきらめく金色の星で飾られ、ダーツボードのゲームを映したテレビが、生活感のある祝祭的な雰囲気を加えている。ランプからの柔らかな照明が、部屋の居心地のよい雰囲気を高めている。

*Rank No.5*, *Cosine Similarity* = 0.4126, *Modality* = [text]{style="color: Orange"}

新鮮なトマトのスライス、緑のオリーブ、薄切りの玉ねぎをのせたおいしそうなイタリアンピザが、白い皿に盛られている。ハーブと調味料が添えられ、料理に彩りと風味豊かなアクセントを加えている。\
------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.3012, *Modality* = [multimodal]{style="color: ForestGreen"} (**Ground Truth**)

![](assets/fig11.png)

女性がキッチンに立ち、微笑みながら猫を抱いている。彼女は茶色のセーターと青いチェック柄のスカートを着ている。キッチンには木製のキャビネットと、鉢植えの植物とオレンジの入ったボウルが置かれたカウンターがある。片側には食器のあるシンクがあり、反対側には白い冷蔵庫がある。壁には時計が見え、カウンターの上にはさまざまな物があり、床には小さなラグが敷かれている。

*Rank No.2*, *Cosine Similarity* = 0.2924, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig12.png)

眼鏡をかけ、黒いシャツを着た人物が、閉じたブラインドのある窓際で、ラジエーターの上に敷かれた紫の毛布の上に座る猫をブラッシングしている。猫は背を向けており、ブラシは Magenta 色で、毛の部分は灰色である。床は木製であり、猫は落ち着いているように見える。

*Rank No.3*, *Cosine Similarity* = 0.2780, *Modality* = [text]{style="color: Orange"}

閉じた便器のふたの上に猫が乗っており、やや動揺しているように見える。便器は、淡い色の壁のある浴室内に置かれている。便器のそばには、かごまたは容器がある。猫の尾が見えており、警戒している、あるいは驚いている可能性がある。\
*Rank No.4*, *Cosine Similarity* = 0.2745, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig13.png)

灰色のアームチェアと黒いアームチェアが、室内で並んで配置されている。黒い椅子のそばのテーブルには小さなランプが置かれている。アームチェアの背後からは猫が顔をのぞかせており、場面に遊び心を添えている。椅子の前には木製のテーブルがあり、その上にリモコンが置かれている。

*Rank No.5*, *Cosine Similarity* = 0.2612, *Modality* = [image]{style="color: Magenta"}

![](assets/fig14.png)

## OVEN {{CITE:10}}

*[Query:]{style="color: blue"}*

![](assets/fig15.png)

この建物の名称は何か？

\

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.5340, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig16.png)

**Clérigos Church.** Clérigos Church は、ポルトガルのポルト市にあるバロック様式の教会である。75メートルの鐘楼 Torre dos Clérigos は市内のさまざまな地点から見ることができ、市を代表する最も特徴的な象徴の一つである。歴史：この教会は、18世紀にポルトガル北部で広範な業績を残したイタリア人建築家・画家 Nicolau Nasoni により、聖職者同信会（Brotherhood of the Clérigos）のために建設された。教会の建設は1732年に始まり1750年に完成し、鐘楼と壮大な分岐階段\...

\
*Rank No.2*, *Cosine Similarity* = 0.5321, *Modality* = [image]{style="color: Magenta"}

![](assets/fig17.png)

*Rank No.3*, *Cosine Similarity* = 0.5276, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig18.png)

**St. Peter's Basilica.** Vatican にある Papal Basilica of Saint Peter、すなわち単に St. Peter's Basilica は、ルネサンス様式で建てられた教会である。これは、4世紀にローマ皇帝 Constantine the Great によって建てられた古い St. Peter's Basilica に代わるものとして、当初 Pope Nicholas V、続いて Pope Julius II によって計画された。現在の大聖堂の建設は1506年4月18日に始まり、1626年11月18日に完成した。主として Donato Bramante、Michelangelo、Carlo Maderno、Gian Lorenzo Bernini により設計され\...

\
*Rank No.4*, *Cosine Similarity* = 0.5274, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig19.png)

**Coit Tower.** Coit Tower は、カリフォルニア州サンフランシスコの Telegraph Hill 地区にある210フィートの塔であり、市街と湾を一望できる。Lillie Hitchcock Coit の遺贈を用いて1932年から1933年にかけて建設され、2008年に National Register of Historic Places に追加された。Arthur Brown, Jr. と Henry Howard によって設計された、この塗装されていない鉄筋コンクリートの塔には、25人の現地アーティストによるアメリカン・フレスコ壁画が施されている\...

\
*Rank No.5*, *Cosine Similarity* = 0.5252, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig20.png)

**Ilinden (Memorial).** Makedonium としても知られる Ilinden は、北マケドニアの Kruševo にある記念碑である。1974年8月2日に正式に開館し、反ファシスト人民解放会議第二会期と1903年の Ilinden 蜂起を記念している。Jordan and Iskra Grabuloski によって設計され、1941--1944年の National Liberation Struggle の戦士を顕彰している。Description. この記念碑は12エーカーの敷地を占め、丸みを帯びた建築様式を特徴とする\...

------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.3153, *Modality* = [text]{style="color: Orange"} (**Ground Truth**)

Canadian National Vimy Memorial. Canadian National Vimy Memorial は、第一次世界大戦中に戦死した Canadian Expeditionary Force の隊員を追悼するためにフランスに設けられた戦争記念施設である。また、フランスで戦死した、あるいは戦死したものとみなされる、墓所不明の第一次世界大戦カナダ兵士の慰霊の場でもある。この記念碑は、Arras の戦いにおける Vimy Ridge 攻勢の初期段階で Canadian Corps が突撃した地の一部を含む、100 (ha) の保存された戦場公園の中心的存在である。\
*Rank No.2*, *Cosine Similarity* = 0.2795, *Modality* = [image]{style="color: Magenta"}

![](assets/fig21.png)

*Rank No.3*, *Cosine Similarity* = 0.2762, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig22.png)

Mary, Queen of the World Cathedral. Mary, Queen of the World Cathedral、正式には Mary, Queen of the World and St. James the Great Cathedral は、カナダ・ケベック州モントリオールにある小バシリカであり、Montreal のローマ・カトリック大司教区の司教座聖堂である。これは、Saint Joseph's Oratory（同じくモントリオールに所在）および Quebec City の東にある Basilica of Sainte-Anne-de-Beaupré に次いで、ケベック州で3番目に大きな教会である。建物の長さは101 m (333 ft)、幅は46 m (150 ft) であり、ドーム部での最大高さは77 m (252 ft)、その直径は23 m (75 ft) である。

\
*Rank No.4*, *Cosine Similarity* = 0.2744, *Modality* = [image]{style="color: Magenta"}

![](assets/fig23.png)

*Rank No.5*, *Cosine Similarity* = 0.2590, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig24.png)

Sydney Town Hall. Sydney Town Hall は、オーストラリアの New South Wales 州の州都 Sydney にある19世紀後半の歴史的建造物に指定された市庁舎であり、Sydney のロード・メイヤーの議場、市議会事務所、会議・催事の会場を収容している。483 George Street に位置し、Sydney 中央業務地区において Queen Victoria Building の向かい、St Andrew's Cathedral に隣接している。Town Hall station の上に位置し、市内の商業・娯楽地区の間にあることから、Town Hall の階段は人気の集合場所となっている。John H. Wilson、Edward Bell、Albert Bond により設計された。

## VisualNews {{CITE:19}}

*[Query:]{style="color: blue"}* 住宅を失った男性の殺人裁判で無罪評決を聞いた直後、元カリフォルニア州警察官 Jay Cicinelli が両手で頭を抱えている。

------------------------------------------------------------------------

**CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.4364, *Modality* = [text]{style="color: Orange"}

この法廷スケッチでは、著名な裁判の判決段階において、その人物が描かれ、厳粛な場面が展開している。その人物は死刑を宣告され、司法手続きにおける重要な局面を示している。緊張と厳粛さに満ちた法廷は、手続きの重大さを反映している。このスケッチは、裁判所によって下された決定の雰囲気と重みを捉えている。\

*Rank No.2*, *Cosine Similarity* = 0.4186, *Modality* = [text]{style="color: Orange"}

この画像は、アルゼンチンの1976--83年軍事独裁政権下でのカトリック司教殺害に関与したとして終身刑を宣告された元将軍を示している。裁判では、Pope Francis が提供した Vatican archives の書簡を含む文書が明らかにされ、それにより司教が政権の虐待を告発していたことが示された。この将軍は、1976年に Bishop Enrique Angelelli を殺害するよう命じた罪で有罪とされ、軍政期の高官が高位聖職者殺害で有罪判決を受けた重要な事例となった。\

*Rank No.3*, *Cosine Similarity* = 0.3994, *Modality* = [text]{style="color: Orange"}

2011年10月3日、感情の張り詰めた法廷で、Amanda Knox が殺人罪の有罪判決に対する控訴で勝訴したとの発表を受け、Amanda Knox の父親が妻に抱きしめられている。支持者や家族が判決に反応し、安堵と喜びに満ちた雰囲気が広がっている。この画像は、広く報道された劇的な法廷闘争のなかで、家族の支えと祝福の重要な瞬間を捉えている。\

*Rank No.4*, *Cosine Similarity* = 0.3718, *Modality* = [text]{style="color: Orange"}

Sudheendra Kulkarni は黒インクを浴びせられ、顔と頭が覆われた。この事件は公共の場で発生し、画像に見られるようにメディアの注目と警察の উপস্থিতを引き寄せた。Kulkarni はその後、インクを除去するために病院へ搬送された。この出来事は緊張を浮き彫りにし、広範な反応を引き起こすとともに、公共言説の不安定な性質を強調した。\

*Rank No.5*, *Cosine Similarity* = 0.3698, *Modality* = [text]{style="color: Orange"}

Rev Sidney Davis は、チャールストンの Second Presbyterian Church で行われた共同祈祷会において、9人の黒人礼拝者の命を奪った悲劇的な銃撃事件の後、参列者を導いている。この集いは、参列者が手を取り合って祈るなかで、暴力に直面した共同体の悲嘆と連帯を反映している。この出来事は、オバマ大統領の在任中に強調された、人種と銃規制に関する継続的議論を浮き彫りにしている。厳粛な雰囲気は、アメリカにおける人種的緊張と銃暴力に関する課題と未解決問題を想起させる。

------------------------------------------------------------------------

**GR-CLIP Top-5 Results**

*Rank No.1*, *Cosine Similarity* = 0.4265, *Modality* = [image]{style="color: Magenta"} (**Ground truth**)

![](assets/fig25.png)

*Rank No.2*, *Cosine Similarity* = 0.3605, *Modality* = [text]{style="color: Orange"}

この法廷スケッチでは、著名な裁判の判決段階において、その人物が描かれ、厳粛な場面が展開している。その人物は死刑を宣告され、司法手続きにおける重要な局面を示している。緊張と厳粛さに満ちた法廷は、手続きの重大さを反映している。このスケッチは、裁判所によって下された決定の雰囲気と重みを捉えている。\

*Rank No.3*, *Cosine Similarity* = 0.3365, *Modality* = [text]{style="color: Orange"}

この画像は、アルゼンチンの1976--83年軍事独裁政権下でのカトリック司教殺害に関与したとして終身刑を宣告された元将軍を示している。裁判では、Pope Francis が提供した Vatican archives の書簡を含む文書が明らかにされ、それにより司教が政権の虐待を告発していたことが示された。この将軍は、1976年に Bishop Enrique Angelelli を殺害するよう命じた罪で有罪とされ、軍政期の高官が高位聖職者殺害で有罪判決を受けた重要な事例となった。\

*Rank No.4*, *Cosine Similarity* = 0.3224, *Modality* = [multimodal]{style="color: ForestGreen"}

![](assets/fig26.png)

国会議員らは、若者に対する入院型精神保健サービスへのアクセス不足について懸念を表明しており、長期の遅延と不十分な支援に直面した Nikki Mattocks の事例などを挙げている。重篤な精神健康問題に苦しみながらも、彼女は断片化したケア体制のなかに置かれ、その結果、救急受診の反復や遠方の精神科病棟への入院を余儀なくされた。こうした家族との連続性と近接性の欠如は、彼女の状態を悪化させた。この議会報告は、脆弱な若者へのさらなる害を防ぐために、早期介入とより適切な資源配分が急務であることを強調している。

*Rank No.5*, *Cosine Similarity* = 0.2956, *Modality* = [text]{style="color: Orange"}

2011年10月3日、感情の張り詰めた法廷で、Amanda Knox が殺人罪の有罪判決に対する控訴で勝訴したとの発表を受け、Amanda Knox の父親が妻に抱きしめられている。支持者や家族が判決に反応し、安堵と喜びに満ちた雰囲気が広がっている。この画像は、広く報道された劇的な法廷闘争のなかで、家族の支えと祝福の重要な瞬間を捉えている。

## References

{{BIBSTART:1}}[1] J. Bai, S. Bai, S. Yang, S. Wang, S. Tan, P. Wang, J. Lin, C. Zhou, and J. Zhou. Qwen-vl: A versatile vision-language model for understanding, localization, text reading, and beyond. arXiv preprint arXiv:2308.12966, 2023.

{{BIBSTART:2}}[2] P. BehnamGhader, V. Adlakha, M. Mosbach, D. Bahdanau, N. Chapados, and S. Reddy. Llm2vec: Large language models are secretly powerful text encoders. arXiv preprint arXiv:2404.05961, 2024.

{{BIBSTART:3}}[3] V. Boteva, D. Gholipour, A. Sokolov, and S. Riezler. A full-text learning to rank dataset for medical information retrieval. 2016.

{{BIBSTART:4}}[4] D. Chen and W. Dolan. Collecting highly parallel data for paraphrase evaluation. In ACL, 2011.

{{BIBSTART:5}}[5] Y.-C. Chen, L. Li, L. Yu, A. El Kholy, F. Ahmed, Z. Gan, Y. Cheng, and J. Liu. Uniter: Universal image-text representation learning. In ECCV, 2020.

{{BIBSTART:6}}[6] K. Drossos, S. Lipping, and T. Virtanen. Clotho: An audio captioning dataset. In ICASSP, pages 736-740. IEEE, 2020.

{{BIBSTART:7}}[7] M. Faysse, H. Sibille, T. Wu, B. Omrani, G. Viaud, C. HUDELOT, and P. Colombo. Colpali: Efficient document retrieval with vision language models. In ICLR, 2025.

{{BIBSTART:8}}[8] S. Fu, N. Y. Tamir, S. Sundaram, L. Chai, R. Zhang, T. Dekel, and P. Isola. Dreamsim: Learning new dimensions of human visual similarity using synthetic data. In NeurIPS, 2023.

{{BIBSTART:9}}[9] R. Girdhar, A. El-Nouby, Z. Liu, M. Singh, K. V. Alwala, A. Joulin, and I. Misra. Imagebind: One embedding space to bind them all. In CVPR, 2023.

{{BIBSTART:10}}[10] H. Hu, Y. Luan, Y. Chen, U. Khandelwal, M. Joshi, K. Lee, K. Toutanova, and M.-W. Chang. Open-domain visual entity recognition: Towards recognizing millions of wikipedia entities. In ICCV, 2023.

{{BIBSTART:11}}[11] K. J\"arvelin and J. Kek\"al\"ainen. Cumulated gain-based evaluation of ir techniques. TOIS, 2002.

{{BIBSTART:12}}[12] Z. Jiang, R. Meng, X. Yang, S. Yavuz, Y. Zhou, and W. Chen. VLM2vec: Training vision-language models for massive multimodal embedding tasks. In ICLR, 2025.

{{BIBSTART:13}}[13] V. Karpukhin, B. Oguz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W.-t. Yih. Dense passage retrieval for open-domain question answering. In EMNLP, 2020.

{{BIBSTART:14}}[14] O. Khattab and M. Zaharia. Colbert: Efficient and effective passage search via contextualized late interaction over bert. In SIGIR, 2020.

{{BIBSTART:15}}[15] K.-H. Lee, X. Chen, G. Hua, H. Hu, and X. He. Stacked cross attention for image-text matching. In ECCV, 2018.

{{BIBSTART:16}}[16] L. H. Li, M. Yatskar, D. Yin, C.-J. Hsieh, and K.-W. Chang. Visualbert: A simple and performant baseline for vision and language. arXiv preprint arXiv:1908.03557, 2019.

{{BIBSTART:17}}[17] V. W. Liang, Y. Zhang, Y. Kwon, S. Yeung, and J. Y. Zou. Mind the gap: Understanding the modality gap in multi-modal contrastive representation learning. In NeurIPS, 2022.

{{BIBSTART:18}}[18] T.-Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Doll\'ar, and C. L. Zitnick. Microsoft coco: Common objects in context. In ECCV, 2014.

{{BIBSTART:19}}[19] F. Liu, Y. Wang, T. Wang, and V. Ordonez. Visual news: Benchmark and challenges in news image captioning. In NeurIPS, 2021.

{{BIBSTART:20}}[20] H. Liu, C. Li, Y. Li, B. Li, Y. Zhang, S. Shen, and Y. J. Lee. Llava-next: Improved reasoning, ocr, and world knowledge, January 2024.

{{BIBSTART:21}}[21] H. Liu, C. Li, Q. Wu, and Y. J. Lee. Visual instruction tuning. In NeurIPS, 2023.

{{BIBSTART:22}}[22] J. Lu, D. Batra, D. Parikh, and S. Lee. Vilbert: Pretraining task-agnostic visiolinguistic representations for vision-and-language tasks. In NeurIPS, 2019.

{{BIBSTART:23}}[23] N. Muennighoff, S. Hongjin, L. Wang, N. Yang, F. Wei, T. Yu, A. Singh, and D. Kiela. Generative representational instruction tuning. In ICLR 2024 Workshop, 2024.

{{BIBSTART:24}}[24] J. Ngiam, A. Khosla, M. Kim, J. Nam, H. Lee, A. Y. Ng, et al. Multimodal deep learning. In ICML, 2011.

{{BIBSTART:25}}[25] A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal, G. Sastry, A. Askell, P. Mishkin, J. Clark, G. Krueger, and I. Sutskever. Learning transferable visual models from natural language supervision. In ICML, 2021.

{{BIBSTART:26}}[26] S. Robertson, H. Zaragoza, et al. The probabilistic relevance framework: Bm25 and beyond. Foundations and Trends in Information Retrieval, 2009.

{{BIBSTART:27}}[27] K. Srinivasan, K. Raman, J. Chen, M. Bendersky, and M. Najork. Wit: Wikipedia-based image text dataset for multimodal multilingual machine learning. In SIGIR, 2021.

{{BIBSTART:28}}[28] N. Srivastava and R. R. Salakhutdinov. Multimodal learning with deep boltzmann machines. In NIPS, 2012.

{{BIBSTART:29}}[29] Voyage AI. voyage-multimodal-3: all-in-one embedding model for interleaved text, images, and screenshots. Blog post, Nov. 2024.

{{BIBSTART:30}}[30] D. Wadden, S. Lin, K. Lo, L. L. Wang, M. van Zuylen, A. Cohan, and H. Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP, 2020.

{{BIBSTART:31}}[31] Y. Wang, K. Li, Y. Li, Y. He, B. Huang, Z. Zhao, H. Zhang, J. Xu, Y. Liu, Z. Wang, et al. Internvideo: General video foundation models via generative and discriminative learning. arXiv preprint arXiv:2212.03191, 2022.

{{BIBSTART:32}}[32] Y. Wu*, K. Chen*, T. Zhang*, Y. Hui*, T. Berg-Kirkpatrick, and S. Dubnov. Large-scale contrastive language-audio pretraining with feature fusion and keyword-to-caption augmentation. In ICASSP, 2023.

{{BIBSTART:33}}[33] H. Xu, S. Xie, X. Tan, P.-Y. Huang, R. Howes, V. Sharma, S.-W. Li, G. Ghosh, L. Zettlemoyer, and C. Feichtenhofer. Demystifying CLIP data. In ICLR, 2024.

{{BIBSTART:34}}[34] X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer. Sigmoid loss for language image pre-training. In ICCV, 2023.

{{BIBSTART:35}}[35] Y. Zhang, J. Z. HaoChen, S.-C. Huang, K.-C. Wang, J. Zou, and S. Yeung. Diagnosing and rectifying vision models using language. In ICLR, 2023.

{{BIBSTART:36}}[36] Y. Zhang, E. Sui, and S. Yeung-Levy. Connect, collapse, corrupt: Learning cross-modal tasks with uni-modal data. In ICLR, 2024.
