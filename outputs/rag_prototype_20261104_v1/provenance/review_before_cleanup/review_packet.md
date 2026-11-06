# 20 条原型的辅助复核稿

此稿由助手依据已保存文本分析，不是人工金标。全文不读取检测分数；建议不进入正式指标。

先阅读问题、完整可见证据和回答，再核对建议；参考答案及隐藏支撑只用于答案正确性诊断，不能补足可见证据。

review_assisted.csv 已预填助手判断与理由，并去掉 review_source 列。请直接检查 evidence_label、answer_correctness 和 rationale，必要时修改；检查完成后通知助手。确认前不导入评估。

supported 要求全部实质性事实均有支撑；unsupported 表示至少一个事实无依据；contradicted 要求存在明确反证。拒答单列。


## 01. sample:0f0ee5d333b8eddbf040b66e98a99175995081779e305b5bd846124e64b9c80b


**问题**：What charter did the US believe was violated by intervening in the Korean conflict?


**回答**：North Korea was not invited as a sitting temporary member of the UN, which violated UN Charter Article 32.


**完整可见证据**：


> [Evidence 1; title: Korean_War; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The Soviet Union challenged the legitimacy of the war for several reasons. The ROK Army intelligence upon which Resolution 83 was based came from U.S. Intelligence; North Korea was not invited as a sitting temporary member of the UN, which violated UN Charter Article 32; and the Korean conflict was beyond the UN Charter's scope, because the initial north–south border fighting was classed as a civil war. Because the Soviet Union was boycotting the Security Council at the time, legal scholars posited that deciding upon an action of this type required the unanimous vote of the five permanent members.

> 

> [Evidence 2; title: First Battle of Naktong Bulge; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The First Battle of Naktong Bulge was an engagement between United States and North Korean forces early in the Korean War from August 5–19, 1950 in the vicinity of Yongsan (Yeongsan, Changnyeong county) and the Naktong River in South Korea. It was a part of the Battle of Pusan Perimeter, and was one of several large engagements fought simultaneously. The battle ended in a victory for the United States after large numbers of US reinforcements destroyed an attacking North Korean division.

> 

> [Evidence 3; title: Second Battle of Naktong Bulge; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Second Battle of Naktong Bulge was an engagement between United Nations (UN) and North Korean (NK) forces early in the Korean War from September 1 to September 15, 1950, along the Naktong River in South Korea. It was a part of the Battle of Pusan Perimeter, and was one of several large engagements fought simultaneously. The battle ended in a victory for the United Nations after large numbers of United States (US) and Republic of Korea (ROK) troops repelled a strong North Korean attack.

> 

> [Evidence 4; title: Denmark in the Eurovision Song Contest 2009; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Denmark participated in the Eurovision Song Contest 2009 held in Moscow on 16 May 2009. Denmark was represented by Brinck with the song "Believe Again". Two other Danish-born contestants also participated at the 2009 Eurovision contest: Susanne Georgi represented Andorra and Yohanna represented Iceland.

> 

> [Evidence 5; title: Shark Bait; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Shark Bait (The Reef: Shark Bait in the UK, Australia and North America, Pi's Story in South Korea) is a 2006 South Korean-American computer animated film. The plot revolves around Pi and his attempt to win the heart of Cordelia while dealing with a tiger shark that is terrorizing him and the reef's inhabitants. The film was a commercial failure. It was largely criticised for borrowing heavily from other films such as Disney/Pixar's "Finding Nemo", DreamWorks' "Shark Tale", and Walt Disney's "The Little Mermaid" (and at one point, a reference to "Star Wars" and "The Karate Kid"), and despite the talented actors and comedians involved in the voiceover work, was a box-office bomb. Despite being an American-South Korean co-production, the movie did not receive a theatrical release in the United States, where it was released direct to DVD in 2007.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

可见证据1明确包含未获邀请、UN Charter Article 32 两项事实。回答涵盖所问 charter；问题将主张归给 US，而正文归给 Soviet Union，属于题干归属歧义，建议复核者记录但不要补写回答未断言的主体。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [248:353] North Korea was not invited as a sitting temporary member of the UN, which violated UN Charter Article 32


**仅用于正确性诊断的参考答案**：["UN Charter Article 32"]


输入 SHA-256：`e00f1036866b371c671dba2561cf390b3f947e1c3d5a25f3ea69eff6bf83843a`；回答 SHA-256：`2fe79af0f0916af131634627e1c4b0bbd086bb09ca340ffc547a7b96158be205`。


## 02. sample:7abb0d7b8b57720e28011f02a8fda74eac4421b5d0199712024bdda0f952487e


**问题**：When was the beginning of the Social War?


**回答**：The Social War began in 91 BC.


**完整可见证据**：


> [Evidence 1; title: Battle of Anzio; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Battle of Anzio was a battle of the Italian Campaign of World War II that took place from January 22, 1944 (beginning with the Allied amphibious landing known as Operation "Shingle") to June 5, 1944 (ending with the capture of Rome). The operation was opposed by German forces in the area of Anzio and Nettuno. The operation was initially commanded by Major General John P. Lucas, of the U.S. Army, commanding U.S. VI Corps with the intention being to outflank German forces at the Winter Line and enable an attack on Rome.

> 

> [Evidence 2; title: Roman_Republic; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Between 135 BC and 71 BC there were three "Servile Wars" involving slave uprisings against the Roman state. The third and final uprising was the most serious, involving ultimately between 120,000 and 150,000 slaves under the command of the gladiator Spartacus. In 91 BC the Social War broke out between Rome and its former allies in Italy when the allies complained that they shared the risk of Rome's military campaigns, but not its rewards. Although they lost militarily, the allies achieved their objectives with legal proclamations which granted citizenship to more than 500,000 Italians.

> 

> [Evidence 3; title: 735th Tank Battalion (United States); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The 735th Tank Battalion was an independent tank battalion that participated in the European Theater of Operations with the United States Army in World War II. The battalion entered combat in Normandy in July 1944 with the 5th Infantry Division and fought across France with the 95th Infantry Division. When reattached to the 5th Infantry Division, the 735th Tank Battalion played a key role in the reduction of the fortifications of Metz. The battalion was also attached to the 26th Infantry Division during the Battle of the Bulge and fought the last several months of the war attached to the 87th Infantry Division. It was inactivated in October 1945.

> 

> [Evidence 4; title: British_Isles; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Scotland, meanwhile had remained an independent Kingdom. In 1603, that changed when the King of Scotland inherited the Crown of England, and consequently the Crown of Ireland also. The subsequent 17th century was one of political upheaval, religious division and war. English colonialism in Ireland of the 16th century was extended by large-scale Scottish and English colonies in Ulster. Religious division heightened and the King in England came into conflict with parliament. A prime issue was, inter alia, over his policy of tolerance towards Catholicism. The resulting English Civil War or War of the Three Kingdoms led to a revolutionary republic in England. Ireland, largely Catholic was mainly loyal to the king. Following defeat to the parliaments army, large scale land distributions from loyalist Irish nobility to English commoners in the service of the parliamentary army created the beginnings a new Ascendancy class which over the next hundred years would obliterate the English (Hiberno-Norman) and Gaelic Irish nobility in Ireland. The new ruling class was Protestant and British, whilst the common people were largely Catholic and Irish. This theme would influence Irish politics for centuries to come. When the monarchy was restored in England, the king found it politically impossible to restore all the lands of former land-owners in Ireland. The "Glorious Revolution" of 1688 repeated similar themes: a Catholic king pushing for religious tolerance in opposition to a Protestant parliament in England. The king's army was defeated at the Battle of the Boyne and at the militarily crucial Battle

> 

> [Evidence 5; title: United_States_presidential_election,_2004; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The Bush administration then turned its attention to Iraq, and argued the need to remove Saddam Hussein from power in Iraq had become urgent. Among the stated reasons were that Saddam's regime had tried to acquire nuclear material and had not properly accounted for biological and chemical material it was known to have previously possessed, and believed to still maintain. Both the possession of these weapons of mass destruction (WMD), and the failure to account for them, would violate the U.N. sanctions. The assertion about WMD was hotly advanced by the Bush administration from the beginning, but other major powers including China, France, Germany, and Russia remained unconvinced that Iraq was a threat and refused to allow passage of a UN Security Council resolution to authorize the use of force. Iraq permitted UN weapon inspectors in November 2002, who were continuing their work to assess the WMD claim when the Bush administration decided to proceed with war without UN authorization and told the inspectors to leave the country. The United States invaded Iraq on March 20, 2003, along with a "coalition of the willing" that consisted of additional troops from the United Kingdom, and to a lesser extent, from Australia and Poland. Within about three weeks, the invasion caused the collapse of both the Iraqi government and its armed forces, however, the U.S. and allied forces failed to find any weapon of mass destruction in Iraq. Traces of former materials and weapons labs were reported to have been located, but


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据2明确写 In 91 BC the Social War broke out；回答是这一事实的简洁改写。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [965:998] In 91 BC the Social War broke out


**仅用于正确性诊断的参考答案**：["91 BC"]


输入 SHA-256：`187e21f59987dfe146c5f0e4f07a8158cafd27d28393c5ef34ae31a83c2743d6`；回答 SHA-256：`e4b053945c441059a556baa1ff18d6700490c258c6efc89411ae180350abdcd4`。


## 03. sample:554e8adee2d4a5878bb739eea9c559ab92b7c26ef1503fe0efc108bca27dec57


**问题**：What is an alternative name for sentence-style capitalization?


**回答**：Sentence-style capitalization is an alternative name for sentence-case.


**完整可见证据**：


> [Evidence 1; title: Letter_case; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The convention followed by many British publishers (including scientific publishers, like Nature, magazines, like The Economist and New Scientist, and newspapers, like The Guardian and The Times) and U.S. newspapers is to use sentence-style capitalisation in headlines, where capitalisation follows the same rules that apply for sentences. This convention is usually called sentence case. It may also be applied to publication titles, especially in bibliographic references and library catalogues. Examples of global publishers whose English-language house styles prescribe sentence-case titles and headings include the International Organization for Standardization.

> 

> [Evidence 2; title: AC Golden Brewing Company; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The AC Golden Brewing Company is a subsidiary of MillerCoors, a joint venture between SABMiller and Molson Coors Brewing Company. Its purpose is to serve as a specialty brewing arm of MillerCoors, in the words of president Glenn Knippenberg, "Our mission for AC Golden is to be a brand incubator for what is now MillerCoors". The AC Golden Brewery operates in the former pilot brewery of the Coors Brewery. It debuted its first beer, Herman Joseph's Private Reserve, in 2008. The company began brewing its seasonal beer, a Vienna Style lager called Winterfest, in 2009. In April 2010, AC Golden introduced Colorado Native lager in Colorado, an amber lager made with 100% Colorado ingredients.

> 

> [Evidence 3; title: Kingdom of Northumbria; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Kingdom of Northumbria ( ; Old English: "Norþhymbra rīce" , "kingdom of the Northumbrians") was a medieval Anglian kingdom in what is now northern England and south-east Scotland, which subsequently became an earldom in a unified English kingdom. The name reflects the approximate southern limit to the kingdom's territory, the Humber estuary.

> 

> [Evidence 4; title: Las Vegas Weekly; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Las Vegas Weekly is a free alternative weekly newspaper based in Henderson, Nevada, covering Las Vegas arts, entertainment, culture and news. "Las Vegas Weekly" is published by Greenspun Media Group. The paper was founded in 1992 by James P. Reza, Greg Ryan and Robert Ringle as a free monthly publication called "Scope Magazine" covering Southern Nevada's culture, arts, music and lifestyle from a decidedly Generation X perspective . "Scope" published its first issue in April 1992. In 1996, Reza partnered with Daniel Greenspun, forming a new company (Radiant City Publications LLC) to publish "Scope". During this partnership, Reza continued on as Managing Editor, broadening the coverage to a more traditional alternative newsweekly style, and accelerated the publishing schedule to biweekly. In 1998, Reza sold his remaining interest in "Scope" to The Greenspun Corporation, who retooled it and renamed it "Las Vegas Weekly". As of December 2009, "Las Vegas Weekly" had a circulation of 65,000.

> 

> [Evidence 5; title: The Hybrid (album); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Hybrid is an album by American hip hop recording artist Danny Brown, released March 16, 2010. The album, which was preceded by a number of free mixtapes, was also released as a free download, by Washington, DC record label Rappers I Know. The label later published the album on vinyl. A deluxe edition of the album was released for sale on Amazon, on January 18, 2011, and later on iTunes, on February 8, 2011, via Hybrid Music. This music collective is what led Fool's Gold founder Nick Catchdubs, to sign Danny Brown to his indie record label. The album received critical acclaim, critics highly praising Brown's unique rapping style, and the production.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1明确将 sentence-style capitalisation 称为 sentence case；回答调换同义关系的表达方向，不改变事实。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [424:472] This convention is usually called sentence case.


**仅用于正确性诊断的参考答案**：["sentence case"]


输入 SHA-256：`4c3857cbfdc9fb3d00f0d54996b4b6f85b31f66097e2eeae699d685c23a08d71`；回答 SHA-256：`db945535346ad00dd1ebd80a0fa0805e0033c8148b368aa36d1e5d30481f337b`。


## 04. sample:73c506b759c8579595da6db37b6fbe31e17678954f4a930deadf514c554ed873


**问题**：At what Augusta hole was the Eisenhower Pine located?


**回答**：The Eisenhower Pine was located on Augusta's 17th hole.


**完整可见证据**：


> [Evidence 1; title: Dwight_D._Eisenhower; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> A loblolly pine, known as the "Eisenhower Pine", was located on Augusta's 17th hole, approximately 210 yards (192 m) from the Masters tee. President Dwight D. Eisenhower, an Augusta National member, hit the tree so many times that, at a 1956 club meeting, he proposed that it be cut down. Not wanting to offend the president, the club's chairman, Clifford Roberts, immediately adjourned the meeting rather than reject the request. The tree was removed in February 2014 after an ice storm caused it significant damage.

> 

> [Evidence 2; title: 56 Pine Street; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> 56 Pine Street – originally known as the Wallace Building after its developer, James Wallace – at 56-58 Pine Street between Pearl and William Streets in the Financial District of Manhattan, New York City, was built in 1893-94 and was designed by Oscar Wirz in the Romanesque Revival style.

> 

> [Evidence 3; title: Pine Street Elementary School; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Pine Street Elementary School is a public elementary school located at 500 South Pine Street in Spartanburg, South Carolina. It serves children from kindergarten through fifth grade and is part of Spartanburg County School District No. 7. Its school building, constructed in 1928-29, is a prominent local example of Beaux Arts architecture, and was listed on the National Register of Historic Places in 2016. It is the oldest continuously operating school in Spartanburg County.

> 

> [Evidence 4; title: 70 Pine Street; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> 70 Pine Street – formerly known as the American International Building, 60 Wall Tower and originally as the Cities Service Building – is a 67-story, 952-foot (290 m) office building located at the corner of Pearl Street and running to Cedar Street in the Financial District of Manhattan, New York City. It was built in 1931-32 by the Cities Service Company for the oil and gas baron Henry Latham Doherty, and was designed by the firms of Clinton & Russell and Holton & George in the Art Deco style.

> 

> [Evidence 5; title: Toland, Pennsylvania; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Toland is an unincorporated community in Cumberland County, Pennsylvania, United States. The very small village is located on Pine Grove Road, east of Mountain Creek Campground. Michaux State Forest, the site of Laurel Lake, Fuller Lake and Pine Grove Furnace State Park lie a few miles to the west near the intersection of Pine Grove Road and PA route 233. Toland has a mailing address of Gardners Pennsylvania, because the size of the community doesn't warrant a post-office, nor an official incorporated name. What is now a sand pit operation was originally a clay bank mining operation that was the reason for the location of the village of Toland. Less than 50 people reside in the close-knit community, which was built for the clay bank company workers in the first quarter of the 20th century. The original community of Toland, Pennsylvania consisted of 11 duplex houses, built side by side along Pine Grove Road, with less than 0.17 of an acre of land to each. Additional homes have been built since. When the community was originally built there was only a common well with a hand pump for all of the families to draw from. Toland is less than 1/4 of a mile long, and it is located less than half a mile from the Appalachian trail crossing. The closest town is Mount Holly Springs, Pennsylvania located (3 miles north of Toland). The village is roughly 10 miles south of Carlisle, Pennsylvania, 7 miles south east of Boiling Springs, Pennsylvania,


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1直接给出 17th hole；整句回答没有加入额外事实。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [142:176] was located on Augusta's 17th hole


**仅用于正确性诊断的参考答案**：["17th"]


输入 SHA-256：`d61ffba8c4a32633ca6deedd31281cf9283c8ff4f96fd53012f788e2e893b12a`；回答 SHA-256：`4fb2e6b8f6cb532f31f84eba730080509d2600b9a8bb371745d064e0c0d6e996`。


## 05. sample:f7cabea1aa6490af7e39f4c426e7d3608625d7af64eeeb79424f0545a70db417


**问题**：In what language were most books printed in the middle ages?


**回答**：Almost all the books published in Paris in the Middle Ages were in Latin, rather than French.


**完整可见证据**：


> [Evidence 1; title: Paris; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The first book printed in France, Epistolae ("Letters"), by Gasparinus de Bergamo (Gasparino da Barzizza), was published in Paris in 1470 by the press established by Johann Heynlin. Since then, Paris has been the centre of the French publishing industry, the home of some of the world's best-known writers and poets, and the setting for many classic works of French literature. Almost all the books published in Paris in the Middle Ages were in Latin, rather than French. Paris did not become the acknowledged capital of French literature until the 17th century, with authors such as Boileau, Corneille, La Fontaine, Molière, Racine, several coming from the provinces, and the foundation of the Académie française. In the 18th century, the literary life of Paris revolved around the cafés and salons, and was dominated by Voltaire, Jean-Jacques Rousseau, Pierre de Marivaux, and Beaumarchais.

> 

> [Evidence 2; title: Middle_Ages; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> In the 10th century the establishment of churches and monasteries led to the development of stone architecture that elaborated vernacular Roman forms, from which the term "Romanesque" is derived. Where available, Roman brick and stone buildings were recycled for their materials. From the tentative beginnings known as the First Romanesque, the style flourished and spread across Europe in a remarkably homogeneous form. Just before 1000 there was a great wave of building stone churches all over Europe. Romanesque buildings have massive stone walls, openings topped by semi-circular arches, small windows, and, particularly in France, arched stone vaults. The large portal with coloured sculpture in high relief became a central feature of façades, especially in France, and the capitals of columns were often carved with narrative scenes of imaginative monsters and animals. According to art historian C. R. Dodwell, "virtually all the churches in the West were decorated with wall-paintings", of which few survive. Simultaneous with the development in church architecture, the distinctive European form of the castle was developed, and became crucial to politics and warfare.

> 

> [Evidence 3; title: Weekend (magazine); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Weekend was a long-running Canadian magazine and newspaper supplement. The "Montreal Standard" was founded in 1905 as a weekly newspaper and was purchased by the "Montreal Star" in 1925. In 1951 the "Standard" was relaunched in magazine format as "Weekend Picture Magazine" serving as a newspaper supplement for the "Montreal Star" and eight other local newspapers across Canada. Eventually shortening its name to "Weekend", the magazine, printed using the rotogravure process, included features writing, cultural and entertainment reporting, cartoons by Doug Wright, colour advertising and photographs and recipes among other items. The magazine began with a circulation of 900,000 and peaked in the 1960s when it was carried in 41 newspapers and had a circulation of 2.5 million, making it the largest circulation magazine in Canada. In 1959 a French-language edition, "Perspectives", was launched.

> 

> [Evidence 4; title: Good Dog, Carl; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Good Dog, Carl is the eponymous name of the first of a series of children's picture books written and illustrated by Alexandra Day centering on a Rottweiler named Carl and a little girl named Madeleine, of whom he takes care. All of the books are mostly wordless, relying on the details of the illustrations to tell the stories. "Good Dog, Carl" was published in 1985 and has been continually in print since that date. There have been fourteen "Carl" titles after the first. All but the first have been published by Farrar, Straus and Giroux. The board book versions of these stories are particularly popular. In addition to the children and Rottweiler fanciers who have enjoyed them, the books have been found useful in teaching English as a second language, with Alzheimer's patients, and with children who are having difficulty learning to read.

> 

> [Evidence 5; title: Baritone; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> A baritone is a type of classical male singing voice whose vocal range lies between the bass and the tenor voice types. It is the most common male voice. Originally from the Greek βαρύτονος ("barýtonos") , meaning "deep (or heavy) sounding", music for this voice is typically written in the range from the second F below middle C to the F above middle C (i.e. F–F) in choral music, and from the second A below middle C to the A above middle C (A to A) in operatic music, but can be extended at either end. The baritone voice type is generally divided into the baryton-Martin baritone (light baritone), lyric baritone, "Kavalierbariton", Verdi baritone, dramatic baritone, "baryton-noble" baritone, and the bass-baritone.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1直接支持中世纪巴黎出版物几乎全用 Latin 而非 French；回答保留巴黎限定，没有把地域范围扩大。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [456:549] Almost all the books published in Paris in the Middle Ages were in Latin, rather than French.


**仅用于正确性诊断的参考答案**：["Latin"]


输入 SHA-256：`c6435e78b2449d4fe984a64d916698a1b99ed646e3905185e0f5b8542adb8553`；回答 SHA-256：`f8fd88a748f50252397be200289758aeb3498060faeb99b4c8949ae89eec2147`。


## 06. sample:7cda78d3c6e2b3c7d2b060c73d130afee2d3012898a40bd1368d52542c572908


**问题**：The lenited Attic Greek yielded /θ ð/ in what periods?


**回答**：The lenited Attic Greek yielded /θ ð/ in the Koine Greek period.


**完整可见证据**：


> [Evidence 1; title: Aspirated_consonant; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Later, during the Koine Greek period, the aspirated and voiceless stops /tʰ d/ of Attic Greek lenited to voiceless and voiced fricatives, yielding /θ ð/ in Medieval and Modern Greek.

> 

> [Evidence 2; title: Chihuahua_(state); version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> At a convention of citizens called to select a new provisional ruler, Gutierrez obtained the vote, with P. J. Escalante for his deputy, and a council to guide the administration. Santa Anna ordered the reinstatement of Mendarozqueta as comandante general. Gutiérrez yielded, but Escalante refused to surrender office, demonstrations of support ensued, but Escalante yielded when troops were summoned from Zacatecas. A new election brought a new legislature, and conforming governors. In September 1835 José Urrea a federalist army officer came into power.

> 

> [Evidence 3; title: Greece; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Regarding the classical music, it was through the Ionian islands (which were under western rule and influence) that all the major advances of the western European classical music were introduced to mainland Greeks. The region is notable for the birth of the first School of modern Greek classical music (Heptanesean or Ionian School, Greek: Επτανησιακή Σχολή), established in 1815. Prominent representatives of this genre include Nikolaos Mantzaros, Spyridon Xyndas, Spyridon Samaras and Pavlos Carrer. Manolis Kalomiris is considered the founder of the Greek National School of Music.

> 

> [Evidence 4; title: Maritsa; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Maritsa, Meriç or Evros (Bulgarian: Марица , "Marica"; Ancient Greek: Ἕβρος , "Hébros"; Modern Greek: Έβρος Evros; Latin: "Hebrus" ; Romanized Thracian: "Evgos" or "Ebros"; Turkish: "Meriç" ) is, with a length of 480 km , the longest river that runs solely in the interior of the Balkans. It has its origin in the Rila Mountains in Western Bulgaria, flowing southeast between the Balkan and Rhodope Mountains, past Plovdiv and Parvomay (where the Mechka and the Kayaliyka join it) to Edirne, Turkey. East of Svilengrad, Bulgaria, the river flows eastwards, forming the border between Bulgaria (on the north bank) and Greece (on the south bank), and then between Turkey and Greece. At Edirne, the river flows through Turkish territory on both banks, then turns towards the south and forms the border between Greece on the west bank and Turkey on the east bank to the Aegean Sea. Turkey was given a small sector on the west bank opposite the city of Edirne. The river enters the Aegean Sea near Enez, where it forms a delta. The Tundzha is its chief tributary; the Arda is another one. The lower course of the Maritsa/Evros forms part of the Bulgarian-Greek border and most of the Greek-Turkish border. The upper Maritsa valley is a principal east-west route in Bulgaria. The unnavigable river is used for power production and irrigation.

> 

> [Evidence 5; title: Mildred Lane Kemper Art Museum; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Mildred Lane Kemper Art Museum is an art museum located on the campus of Washington University in St. Louis, within the university's Sam Fox School of Design & Visual Arts. It was founded in 1881 as the St. Louis School and Museum of Fine Arts, and initially located in a building in downtown St. Louis. It is the oldest art museum west of the Mississippi River. Its collection was formed in large part by acquiring significant works by artists of the time, a legacy that continues today. The Museum contains strong holdings of 19th-, 20th-, and 21st-century European and American paintings, sculptures, prints, installations, and photographs. The collection also includes some Egyptian and Greek antiquities, Old Master prints, and the Wulfing Collection of approximately 14,000 ancient Greek, Roman, and Byzantine coins.


**助手建议**：证据支持 `undetermined`；答案正确性 `undetermined`。

关键时间歧义：原句把弱化过程放在 Koine Greek period，又把 yielding /θ ð/ 关联到 Medieval and Modern Greek。回答只给 Koine；应由复核者判断题目问过程发生期还是结果所属时期，不能机械按词重合标 supported，也不应未经裁决标 contradicted。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [92:274] Later, during the Koine Greek period, the aspirated and voiceless stops /tʰ d/ of Attic Greek lenited to voiceless and voiced fricatives, yielding /θ ð/ in Medieval and Modern Greek.


**仅用于正确性诊断的参考答案**：["Medieval and Modern Greek"]


输入 SHA-256：`1b92ee92b08a991c183005171d1aa6df9f8b126846e209bee06ad4e81886b847`；回答 SHA-256：`3860cb888eee85ee8b3f0ec9c66019d859be98eb0cfd19bc2a23a2ec3764df79`。


## 07. sample:b5b44018c9b1891c744991b751e5e3416b3b76d0f3af708ff043525275167c56


**问题**：Under which ruler did Armenia become a sovereign kingdom?


**回答**：In 885 AD, Armenia became a sovereign kingdom under the leadership of Ashot I of the Bagratid Dynasty.


**完整可见证据**：


> [Evidence 1; title: Armenians; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> In 885 AD the Armenians reestablished themselves as a sovereign kingdom under the leadership of Ashot I of the Bagratid Dynasty. A considerable portion of the Armenian nobility and peasantry fled the Byzantine occupation of Bagratid Armenia in 1045, and the subsequent invasion of the region by Seljuk Turks in 1064. They settled in large numbers in Cilicia, an Anatolian region where Armenians were already established as a minority since Roman times. In 1080, they founded an independent Armenian Principality then Kingdom of Cilicia, which became the focus of Armenian nationalism. The Armenians developed close social, cultural, military, and religious ties with nearby Crusader States, but eventually succumbed to Mamluk invasions. In the next few centuries, Djenghis Khan, Timurids, and the tribal Turkic federations of the Ak Koyunlu and the Kara Koyunlu ruled over the Armenians.

> 

> [Evidence 2; title: Kingdom of Northumbria; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Kingdom of Northumbria ( ; Old English: "Norþhymbra rīce" , "kingdom of the Northumbrians") was a medieval Anglian kingdom in what is now northern England and south-east Scotland, which subsequently became an earldom in a unified English kingdom. The name reflects the approximate southern limit to the kingdom's territory, the Humber estuary.

> 

> [Evidence 3; title: Andorra; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Andorra ( ; ] , ] ), officially the Principality of Andorra (Catalan: "Principat d'Andorra" ), also called the Principality of the Valleys of Andorra (Catalan: "Principat de les Valls d'Andorra" ), is a sovereign landlocked microstate in Southwestern Europe, located in the eastern Pyrenees mountains and bordered by Spain and France. Created under a charter in 988, the present principality was formed in 1278. It is known as a principality as it is a diarchy headed by two Co-Princesthe Catholic Bishop of Urgell in Spain, and the President of France.

> 

> [Evidence 4; title: Junior Eurovision Song Contest 2010; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Junior Eurovision Song Contest 2010 was the eighth edition of Junior Eurovision Song Contest and took place in Minsk, Belarus. It was held on 20 November 2010. The contest was won by Vladimir Arzumanyan from Armenia with the song Mama. This gave Armenia its first Junior Eurovision victory and its first victory in any Eurovision contest.

> 

> [Evidence 5; title: History_of_science; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Mathematics: The earliest traces of mathematical knowledge in the Indian subcontinent appear with the Indus Valley Civilization (c. 4th millennium BC ~ c. 3rd millennium BC). The people of this civilization made bricks whose dimensions were in the proportion 4:2:1, considered favorable for the stability of a brick structure. They also tried to standardize measurement of length to a high degree of accuracy. They designed a ruler—the Mohenjo-daro ruler—whose unit of length (approximately 1.32 inches or 3.4 centimetres) was divided into ten equal parts. Bricks manufactured in ancient Mohenjo-daro often had dimensions that were integral multiples of this unit of length.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1同一句同时给出 885 AD、Ashot I 和 Bagratid Dynasty；回答的附加年份和王朝也有依据。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [82:210] In 885 AD the Armenians reestablished themselves as a sovereign kingdom under the leadership of Ashot I of the Bagratid Dynasty.


**仅用于正确性诊断的参考答案**：["Ashot I"]


输入 SHA-256：`c12287aab8d451a979b14a578b11cd619c3157ef7a630bda5a1563eb1e209b8d`；回答 SHA-256：`eb32e1c4ef01a5879337ee98c9dc1fb9650bb81afbc1fac25e8ea912640ad742`。


## 08. sample:36a7721fbac3768da4f9cf6698f712490ca722e03b86c0ff847664475ce3466c


**问题**：For what type of military applications are pancake motors currently used?


**回答**：Pancake motors are currently used in high-performance servo-controlled systems, robotic systems, industrial automation, and medical devices for military applications.


**完整可见证据**：


> [Evidence 1; title: Electric_motor; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> These motors were originally invented to drive the capstan(s) of magnetic tape drives in the burgeoning computer industry, where minimal time to reach operating speed and minimal stopping distance were critical. Pancake motors are still widely used in high-performance servo-controlled systems, robotic systems, industrial automation and medical devices. Due to the variety of constructions now available, the technology is used in applications from high temperature military to low cost pump and basic servos.

> 

> [Evidence 2; title: Transistor; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Because the electron mobility is higher than the hole mobility for all semiconductor materials, a given bipolar n–p–n transistor tends to be swifter than an equivalent p–n–p transistor. GaAs has the highest electron mobility of the three semiconductors. It is for this reason that GaAs is used in high-frequency applications. A relatively recent FET development, the high-electron-mobility transistor (HEMT), has a heterostructure (junction between different semiconductor materials) of aluminium gallium arsenide (AlGaAs)-gallium arsenide (GaAs) which has twice the electron mobility of a GaAs-metal barrier junction. Because of their high speed and low noise, HEMTs are used in satellite receivers working at frequencies around 12 GHz. HEMTs based on gallium nitride and aluminium gallium nitride (AlGaN/GaN HEMTs) provide a still higher electron mobility and are being developed for various applications.

> 

> [Evidence 3; title: Media type; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> A media type (also MIME type and content type) is a two-part identifier for file formats and format contents transmitted on the Internet. The Internet Assigned Numbers Authority (IANA) is the official authority for the standardization and publication of these classifications. Media types were originally defined in Request for Comments 2045 in November 1996 as a part of "MIME (Multipurpose Internet Mail Extensions)" specification, for denoting type of email message content and attachments; hence the name "MIME type". Media types are also used by other internet protocols such as HTTP and document file formats such as HTML, for similar purpose.

> 

> [Evidence 4; title: Golden Nugget Pancake House; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Golden Nugget Pancake House is a chain of family restaurants originally launched in Florida but now operating exclusively in Chicago, Illinois. The restaurants serve breakfast 24 hours a day, and their decor generally has a Western motif.

> 

> [Evidence 5; title: Marquesas Keys; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Marquesas Keys form an uninhabited island group about 20 miles west of Key West, 4 miles (6 km) in diameter, and largely covered by mangrove forest. They are an unincorporated area of Monroe County, Florida and belong to the Lower Keys Census County Division. They are protected as part of the Key West National Wildlife Refuge. The Marquesas were used for target practice by the military as recently as 1980.


**助手建议**：证据支持 `unsupported`；答案正确性 `incorrect`。

证据把通用用途列表与 high temperature military 用途分开陈述。回答将伺服、机器人、自动化和医疗设备统称军事用途，缺少这层限定的依据，并未回答题干要求的 high temperature 类型；缺乏支持不等于已有明确反证。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [299:441] Pancake motors are still widely used in high-performance servo-controlled systems, robotic systems, industrial automation and medical devices.

- [493:597] the technology is used in applications from high temperature military to low cost pump and basic servos.


**仅用于正确性诊断的参考答案**：["high temperature"]


输入 SHA-256：`20a153cf7fe74b748ea932691437e64d2b5bdcd84eb02fccfd95720b9476dba3`；回答 SHA-256：`1eb68fee072f8cd307b267f1ec4039428cf005b91e9b6973debda01b9d992352`。


## 09. sample:6d97172604511dfa9ca7fff80ec7d0682a4e87ec2c4874e6db9e48beefa2753e


**问题**：In which Federalist paper did James Madison state that the legislative branch of government was predominate?


**回答**：James Madison stated that the legislative branch of government was predominant in Federalist Paper 51.


**完整可见证据**：


> [Evidence 1; title: Separation_of_powers_under_the_United_States_Constitution; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The Constitution does not explicitly indicate the pre-eminence of any particular branch of government. However, James Madison wrote in Federalist 51, regarding the ability of each branch to defend itself from actions by the others, that "it is not possible to give to each department an equal power of self-defense. In republican government, the legislative authority necessarily predominates."

> 

> [Evidence 2; title: Reform Party of New York State; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Reform Party of New York State (also known as the New York State Reform Party) is the name of two unrelated political parties in the state of New York: a qualified party active only in New York State, and the New York branch of the Reform Party of the United States of America.

> 

> [Evidence 3; title: Nintendo_Entertainment_System; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> In Europe and Australia, the system was released to two separate marketing regions. One region consisted of most of mainland Europe (excluding Italy), and distribution there was handled by a number of different companies, with Nintendo responsible for most cartridge releases. Most of this region saw a 1986 release. Mattel handled distribution for the other region, consisting of the United Kingdom, Ireland, Canada, Italy, Australia and New Zealand, starting the following year. Not until the 1990s did Nintendo's newly created European branch direct distribution throughout Europe.

> 

> [Evidence 4; title: Greece; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Greece is a unitary parliamentary republic. The nominal head of state is the President of the Republic, who is elected by the Parliament for a five-year term. The current Constitution was drawn up and adopted by the Fifth Revisionary Parliament of the Hellenes and entered into force in 1975 after the fall of the military junta of 1967–1974. It has been revised three times since, in 1986, 2001 and 2008. The Constitution, which consists of 120 articles, provides for a separation of powers into executive, legislative, and judicial branches, and grants extensive specific guarantees (further reinforced in 2001) of civil liberties and social rights. Women's suffrage was guaranteed with an amendment to the 1952 Constitution.

> 

> [Evidence 5; title: East Stroudsburg University of Pennsylvania; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> East Stroudsburg University of Pennsylvania is a public university located in East Stroudsburg, Pennsylvania. It is one of the 14 state universities that compose the Pennsylvania State System of Higher Education (PASSHE). It is commonly referred to as ESU by its students and members of the community. The university began its existence in 1893 as a preparatory school for teachers called the East Stroudsburg Normal School, which was private. Ownership was transferred to the Commonwealth of Pennsylvania in 1920, and the name was changed to East Stroudsburg State Normal School. In 1927, the right to confer the degrees of bachelor of science in education and bachelor of science in health education was granted, and the school's name then became the East Stroudsburg State Teachers College. In 1960, additional curricula were added and the school's name then became East Stroudsburg State College. The State System of Higher Education was authorized by Senate Bill 506 to assume its current name in 1983.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1明确 Madison 在 Federalist 51 写下 legislative authority necessarily predominates；Paper 51 的改写可接受。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [242:278] James Madison wrote in Federalist 51

- [472:523] the legislative authority necessarily predominates.


**仅用于正确性诊断的参考答案**：["Federalist 51"]


输入 SHA-256：`85f082545c6b7debc6d30c442ed62dc861039a556496c5e6e2b0e4dc1cb6cc71`；回答 SHA-256：`9363338612e08183070b42a46edc63fef05381c59ba944aa8578b6ad72c204d0`。


## 10. sample:f8664dbe742f8a5986acfe487511aeb64628c2703dc5145906774b3a7b1f3fbf


**问题**：What percent of undergraduate students live on campus at Washington University?


**回答**：INSUFFICIENT_EVIDENCE


**完整可见证据**：


> [Evidence 1; title: Washington_University_in_St._Louis; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> Over 50% of undergraduate students live on campus. Most of the residence halls on campus are located on the South 40, named because of its adjacent location on the south side of the Danforth Campus and its size of 40 acres (160,000 m2). It is the location of all the freshman buildings as well as several upperclassman buildings, which are set up in the traditional residential college system. All of the residential halls are co-ed. The South 40 is organized as a pedestrian-friendly environment wherein residences surround a central recreational lawn known as the Swamp. Bear's Den (the largest dining hall on campus), the Habif Health and Wellness Center (Student Health Services), the Residential Life Office, University Police Headquarters, various student-owned businesses (e.g. the laundry service, Wash U Wash), and the baseball, softball, and intramural fields are also located on the South 40.

> 

> [Evidence 2; title: Lynn University; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Lynn University is an American private university in Boca Raton, Florida. It was founded in 1962. Its students come from all over the USA and approximately 80 other nations: 24% of students have citizenship in countries outside the United States. The university is accredited by the Commission on Colleges of the Southern Association of Colleges and Schools to award associate's, baccalaureate, master's and doctoral degrees. It is named for the Lynn family (Christine E. and Eugene M. Lynn). It has a total undergraduate enrollment of 2,100, its setting is suburban, and the campus size is 123 acres. It utilizes a semester-based academic calendar. Lynn University's ranking in the 2015 edition of Best Colleges is National Universities, Tier 2.

> 

> [Evidence 3; title: Oxford College of Emory University; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Oxford College of Emory University, also called Oxford College and founded in 1836 as Emory College, is an American two-year residential college specializing in the foundations of liberal arts education. It is the birthplace and one of nine academic divisions of Emory University. The college is located on Emory University's original campus in Oxford, Georgia, 38 mi east of Emory's Atlanta campus. Students who enroll in Oxford College complete an associate of the arts degree there, after which they can continue their studies at Emory's Atlanta campus to pursue a bachelor degree without any additional applications.

> 

> [Evidence 4; title: University_of_Notre_Dame; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> The School of Architecture was established in 1899, although degrees in architecture were first awarded by the university in 1898. Today the school, housed in Bond Hall, offers a five-year undergraduate program leading to the Bachelor of Architecture degree. All undergraduate students study the third year of the program in Rome. The university is globally recognized for its Notre Dame School of Architecture, a faculty that teaches (pre-modernist) traditional and classical architecture and urban planning (e.g. following the principles of New Urbanism and New Classical Architecture). It also awards the renowned annual Driehaus Architecture Prize.

> 

> [Evidence 5; title: University_of_Notre_Dame; version: 7b6d24c440a36b6815f21b70d25016731768db1f]

> All of Notre Dame's undergraduate students are a part of one of the five undergraduate colleges at the school or are in the First Year of Studies program. The First Year of Studies program was established in 1962 to guide incoming freshmen in their first year at the school before they have declared a major. Each student is given an academic advisor from the program who helps them to choose classes that give them exposure to any major in which they are interested. The program also includes a Learning Resource Center which provides time management, collaborative learning, and subject tutoring. This program has been recognized previously, by U.S. News & World Report, as outstanding.


**助手建议**：证据支持 `undetermined`；答案正确性 `undetermined`。

拒答按协议不进入事实回答 AUC。证据1首句已提供 Over 50%，因此这是有答案情况下的过度拒答候选，不能将其计为正确事实回答或幻觉负类；保留为拒答质量案例。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [107:157] Over 50% of undergraduate students live on campus.


**仅用于正确性诊断的参考答案**：["Over 50%"]


输入 SHA-256：`bb94c0d68cc8ad6e69950b1560723e0f7c552c9381b3b679942b01f0ce3e2bc4`；回答 SHA-256：`a5fafaa214fa671c293071b6dac23e4c0f0bd9fe935f3d65c96c16bacf6ae345`。


## 11. sample:8f5dc887596c479a95c149cc7b9a184945bb840068eaa74d8fe3cdf9ad3c399f


**问题**：Are Bijou and Agua de Valencia both made from gin?


**回答**：INSUFFICIENT_EVIDENCE


**完整可见证据**：


> [Evidence 1; title: Agua de Valencia; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Valencian Water (Valencian, Aigua de València. Spanish, Agua de Valencia) is a cocktail made from a base of cava or champagne and orange juice. In general, it is served in pitchers of various sizes and is consumed from a broad cocktail glass. It was made for the first time in 1959 by Constante Gil in the bar Café Madrid de Valencia in the city of Valencia, Spain.

> 

> [Evidence 2; title: Bijou (cocktail); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> A bijou is a mixed alcoholic drink composed of gin, vermouth, and chartreuse. Bijou means "jewel" in French. It is said to have been invented by Harry Johnson. This cocktail is called Bijou because it combines the colors of three jewels: gin for diamond, vermouth for ruby, and chartreuse for emerald. An original-style Bijou is made stirred with ice as Harry Johnson's 1900 "New and Improved Bartender Manual" states "mix well with a spoon and serve." This recipe is also one of the oldest in the manual dating back to 1890s.

> 

> [Evidence 3; title: Ojo de Agua de Morán, Jalisco; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Ojo de Agua de Morán is a town within the municipality of the Atotonilco El Alto located in the southeastern part of the state of Jalisco in Mexico. It has 939 inhabitants. Ojo de Agua de Morán is 1980 meters above sea level. Along with neighbor of San Francisco de Asís. Founded in 1800s by Villalobos and Becerra families who are agriculturists.

> 

> [Evidence 4; title: ILCD; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> iLCD (Lighting Cell Display) is a device developed by a research team from Universidad Politecnica de Valencia, a MIT educated bioengineer, undergraduated students of the Universidad Politéctica de Valencia and Universitat de València and several members of the faculty and research staff from Universidad de València (Manuel Porcar), UPV (Pedro De Cordoba) and University of Malaga (Emilio Navarro).

> 

> [Evidence 5; title: Anneke van Giersbergen (band); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Anneke van Giersbergen (formerly Agua de Annique and Anneke van Giersbergen and Agua de Annique) is the solo project of the former The Gathering vocalist, Anneke van Giersbergen.


**助手建议**：证据支持 `undetermined`；答案正确性 `undetermined`。

拒答单列。Bijou 明确含 gin；Agua de Valencia 段落只列 base of cava or champagne and orange juice，未声明穷尽配料，不能从未提及 gin 推出不含 gin，也不能仅凭隐藏参考答案将拒答判错。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [166:232] a cocktail made from a base of cava or champagne and orange juice.

- [545:622] A bijou is a mixed alcoholic drink composed of gin, vermouth, and chartreuse.


**仅用于正确性诊断的参考答案**：["no"]


输入 SHA-256：`30d12539364787ca91c24bb652674b373552c078a6a25b548ccc315a78ea8713`；回答 SHA-256：`a5fafaa214fa671c293071b6dac23e4c0f0bd9fe935f3d65c96c16bacf6ae345`。


## 12. sample:5347b35e5333ef3bdb777a38723e28a4072f220ed05106dd1bd4d5444d7aa200


**问题**：Santon Bridge is a small village in Copeland, Cumbria, England, at a bridge over the River Irt, The Bridge Inn is the venue for which annual competition for telling lies, held in Cumbria, England?


**回答**：The Bridge Inn hosts the annual World's Biggest Liar competition, which is held in Cumbria, England.


**完整可见证据**：


> [Evidence 1; title: Santon Bridge; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Santon Bridge is a small village in Copeland, Cumbria, England, at a bridge over the River Irt. The civil parish is called Irton with Santon. The population of this civil parish as at the 2011 census was 316. The Bridge Inn is the venue for the annual World's Biggest Liar competition.

> 

> [Evidence 2; title: Irton with Santon; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Irton with Santon is a civil parish in Copeland, Cumbria, England, which includes the village of Santon Bridge. It has a parish council. In the 2011 census it was recorded as having a population of 316.

> 

> [Evidence 3; title: Listed buildings in Irton with Santon; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Irton with Santon is a civil parish in the Borough of Copeland, Cumbria, England. It contains 17 listed buildings that are recorded in the National Heritage List for England. Of these, two are listed at Grade II*, the middle of the three grades, and the others are at Grade II, the lowest grade. The parish is in the Lake District National Park. It contains the villages of Irton and Santon Bridge, and is otherwise rural. In the parish is the country house of Irton Hall, which incorporates a medieval tower house, and also has a clock tower; all of these are listed. The other listed buildings include houses, farmhouses, farm buildings, a church with a memorial in its churchyard, two bridges, a summer house, and an inn.

> 

> [Evidence 4; title: Nether Wasdale; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Nether Wasdale is a village in Cumbria, England, located in the Wasdale valley, near the River Irt and just over a mile to the west of the Wastwater lake.

> 

> [Evidence 5; title: Skelwith Bridge; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Skelwith Bridge is a small village in the southern area of the Lake District in Cumbria. Historically, Skelwith Bridge is part of Westmorland, lying on the ancient boundary with Lancashire. The civil parish is called Skelwith. Its population at the 2011 census was 155. It is located around 3 miles south of Grasmere and is nearby the waterfalls of Skelwith Force and Colwith Force. The nearest lakes to the village are Elter Water to the north-west and Loughrigg Tarn to the north.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1同段支持 Santon Bridge 位于 Cumbria, England 及 Bridge Inn 举办年度 World's Biggest Liar；无需依赖未检索到的另一金标文档。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [86:148] Santon Bridge is a small village in Copeland, Cumbria, England

- [295:371] The Bridge Inn is the venue for the annual World's Biggest Liar competition.


**仅用于正确性诊断的参考答案**：["World's Biggest Liar"]


输入 SHA-256：`79f7327bb2ac57df7416dabf381dd4aea96c691b61ef6bb3c859e2017c958397`；回答 SHA-256：`9b3fa48bcbe7cf4df5b46cdb51295e424f17ca491fb73f247b6682c2bdc7f7a3`。


## 13. sample:1acdfd7bb1339478e99f062d2fb15adf7c3bf80adaec038c70694351988a9930


**问题**：Are Freddie Mercury and Henry Paul both American?


**回答**：Freddie Mercury is not American.


**完整可见证据**：


> [Evidence 1; title: Magic Tour (Queen); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Magic Tour was the biggest and final tour by the British rock band Queen with their lead singer Freddie Mercury and their bass guitarist John Deacon, which took place in 1986. The band would not tour again until 19 years later, when the Queen + Paul Rodgers Tour began in 2005, after the death of Freddie Mercury on 24 November 1991, and the retirement of John Deacon in 1997. The Magic Tour took in 26 dates around Europe's stadiums, in support of their then latest album "A Kind of Magic".

> 

> [Evidence 2; title: Queen + Paul Rodgers Tour; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Queen + Paul Rodgers Tour was a world concert tour by Queen guitarist Brian May and drummer Roger Taylor, joined by singer Paul Rodgers under the moniker of Queen + Paul Rodgers. The tour was Queen's first since The Magic Tour in 1986, and the death of lead singer Freddie Mercury in November 1991. The band's drummer Roger Taylor commented; "We never thought we would tour again, Paul (Rodgers) came along by chance and we seemed to have a chemistry. Paul is just such a great singer. He's not trying to be Freddie." Bassist John Deacon also did not take part due to his retirement in 1997, however he gave the enterprise his blessing.

> 

> [Evidence 3; title: Freddie Mercury; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Farrokh "Freddie" Mercury (born Bulsara; 5 September 1946 – 24 November 1991) was a British singer, songwriter and record producer, known as the lead vocalist of the rock band Queen. He was known for his flamboyant stage persona and four-octave vocal range. Mercury wrote numerous hits for Queen, including "Bohemian Rhapsody", "Killer Queen", "Somebody to Love", "Don't Stop Me Now", "Crazy Little Thing Called Love", and "We Are the Champions". He led a solo career while performing with Queen, and occasionally served as a producer and guest musician for other artists.

> 

> [Evidence 4; title: The Freddie Mercury Album; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Freddie Mercury Album is a posthumous solo project with material from Queen frontman and vocalist Freddie Mercury released in 1992, to observe the anniversary of his death. The album is mainly made up of remixes from his past releases, as well as the original versions of "Barcelona", "Love Kills", "Exercises in Free Love", and "The Great Pretender". A week later, The Great Pretender, its US counterpart, was released.

> 

> [Evidence 5; title: Freddie Mercury: The Great Pretender; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Freddie Mercury: The Great Pretender is an Emmy/Rose d'Or award winning 2012 feature-length documentary about Queen singer Freddie Mercury and his attempt to forge a solo career. The documentary premiered on BBC One in edited form as part of the Imagine series, and later the Director's Cut was shown on BBC Four. It gained 3.5 million viewers when aired on BBC One in October 2012 and a further 1.2 million when shown on BBC Four.


**助手建议**：证据支持 `undetermined`；答案正确性 `correct`。

参考答案的否定方向可由回答表达，但严格证据支持存在边界：证据3称其 British，没有明确 not American；国籍可能并存。建议保留 undetermined，人工先裁决是否允许通常国籍问答的排他解读。Henry Paul 的国籍不是否定 both 命题的必要前提。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [1490:1542] was a British singer, songwriter and record producer


**仅用于正确性诊断的参考答案**：["no"]


输入 SHA-256：`1fc6cc563ba0cca4bd101147c636b1969e531b628695d3e07c3536619c3ca92a`；回答 SHA-256：`215cee0bbf6e0597b028d562573b79505aefd9a4afc6fcd39d9b0c8dde2df011`。


## 14. sample:c582502551e2e02a90ea2f724b83c9fad773f440852205d173c1f4a1b28f83ee


**问题**：Which star of the Karate Kid was born on July 8, 1998 ?


**回答**：Jaden Smith was born on July 8, 1998 and starred in the 2010 remake of "The Karate Kid".


**完整可见证据**：


> [Evidence 1; title: Jaden Smith; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Jaden Christopher Syre Smith (born July 8, 1998) is an American actor and rapper. He is the son of Jada Pinkett Smith and Will Smith. Jaden Smith's first movie role was with his father in the 2006 film "The Pursuit of Happyness". He also acted in the 2008 remake of "The Day the Earth Stood Still" and the 2010 remake of "The Karate Kid", and was in the 2013 film "After Earth" with his father.

> 

> [Evidence 2; title: Fumio Demura; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Fumio Demura (出村 文男 , Demura Fumio , born September 15, 1938) is a Japanese American master of karate. He is a well known master of karate and kobudo (weaponry), and was Pat Morita's martial arts stunt double in the first, third and fourth "Karate Kid" films. Demura holds the rank of 9th "dan" in Shitō-ryū Karate.

> 

> [Evidence 3; title: Pat Morita; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Noriyuki "Pat" Morita (June 28, 1932 – November 24, 2005) was an American stand-up comic, as well as a film and television actor who was well known for playing the roles of Matsuo "Arnold" Takahashi on "Happy Days" (1975–1983) and Mr. Kesuke Miyagi in "The Karate Kid" movie series, for which he was nominated for the Academy Award for Best Supporting Actor in 1985. Additional notable roles include the Emperor of China in the Disney animated film "Mulan" (1998) and Ah Chew in "Sanford and Son" (1974–1976).

> 

> [Evidence 4; title: The Karate Kid (2010 film); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Karate Kid is a 2010 family martial arts drama film directed by Harald Zwart. It stars Jaden Smith, Jackie Chan and Taraji P. Henson in lead roles, and it was produced by Jerry Weintraub, James Lassiter, Ken Stovitz and Jaden's parents Will and Jada. The screenplay by Christopher Murphey was from the story written by Robert Mark Kamen for the original 1984 film of the same name. Unlike the original, this remake is set in the People's Republic of China, and features Kung Fu instead of Japanese Karate. The film's music was composed by James Horner. It is an international co-production between China, Hong Kong, and the United States.

> 

> [Evidence 5; title: Pat E. Johnson; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Pat E. Johnson (born 1939 in Niagara Falls, New York) is a 9th degree black belt in the art of American Tang Soo Do. He is the president of the National Tang Soo Do Congress, which was originally created by Chuck Norris in 1973. Johnson is famous for the martial arts choreography in the "Karate Kid" series in which he also starred as the All Valley Karate Tournament head referee, and has been involved in many films, as choreographer and actor including "Enter The Dragon", "Teenage Mutant Ninja Turtles", "Mortal Kombat", "Green Street Hooligans" and recently, "". He is the 1995 "Black Belt Magazine" Instructor of the Year.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1同时支持出生日期和出演 2010 重拍版；证据4明确该片主演包括 Jaden Smith，回答全部事实可见。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [84:132] Jaden Christopher Syre Smith (born July 8, 1998)

- [314:421] He also acted in the 2008 remake of "The Day the Earth Stood Still" and the 2010 remake of "The Karate Kid"

- [1657:1725] It stars Jaden Smith, Jackie Chan and Taraji P. Henson in lead roles


**仅用于正确性诊断的参考答案**：["Jaden Smith"]


输入 SHA-256：`a44db2b3bbe8c73556dd90660e1eeaf8c81599c980e7963e74b4a007b951130e`；回答 SHA-256：`8e3d030e0640806d55893edf92b8e15389bca82247d8f6e162e09c58eb1a1148`。


## 15. sample:e71692555ff6e9aedd97e12989f4625a8bc3989bd7686041d541cbdf712374b8


**问题**：Dare was described as similar to a cross between Cruel Intentions and what 1986 American film?


**回答**：Dare was described as similar to a cross between Cruel Intentions and Pretty in Pink.


**完整可见证据**：


> [Evidence 1; title: Dare (film); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Dare is a 2009 indie romantic drama film directed by Adam Salky. It is written by David Brind. The movie is based on Salky's 2005 short film which was met with acclaim at film festivals. The feature-length version, which premiered at the Sundance Film Festival, stars Emmy Rossum in a story about how "three very different teenagers discover that, even in the safe world of a suburban prep school, no one is who she or he appears to be." IMDB also provides a different teaser synopsis: "The good girl, the outsider and the bad boy…like you’ve never seen them before." The film has been described as a cross between "Pretty in Pink" and "Cruel Intentions".

> 

> [Evidence 2; title: Cruel Intentions 2; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Cruel Intentions 2 (also known as Cruel Intentions 2: Manchester Prep or simply as Manchester Prep) is the 2001 American comedy-drama film. It was written and directed by Roger Kumble and starring Robin Dunne, Sarah Thompson, Keri Lynn Pratt and Amy Adams. It is a prequel to "Cruel Intentions" (1999) and was released direct-to-video on March 13, 2001. Both films are based on "Les Liaisons dangereuses" by Choderlos de Laclos.

> 

> [Evidence 3; title: Cruel Intentions 3; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Cruel Intentions 3 is a 2004 American teen drama film directed by Scott Ziehl and released direct-to-video in 2004. Despite its name, the film has almost no relation to the previous films in the series, except for the shared themes and the lead character in this film, Cassidy Merteuil, who is a cousin of one of the characters from the first film, Kathryn Merteuil.

> 

> [Evidence 4; title: Cruel Intentions: The Musical; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Cruel Intentions: The Musical is a jukebox musical adapted from the film "Cruel Intentions" by Jordan Ross and Lindsey Rosin with music direction and arrangements by Zach Spound. After two sold-out engagements in Los Angeles, the show made its New York City debut at Le Poisson Rouge in 2017.

> 

> [Evidence 5; title: Take You High; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "Take You High" is a song by American recording artist Kelly Clarkson from her seventh studio album, "Piece by Piece" (2015). Written by Jesse Shatkin and MoZella, the song is produced by Shatkin. A midtempo EDM gospel tune, it is a song of encouragement and escapism, in which the singer lends a hand to the despondent. Musically featuring an auto-tuned EDM breakdown, Shatkin described its sound as "an electronic banger" and "a little left-of-center", while Clarkson commented that it reminded her of the music of soundtrack to the 1999 film "Cruel Intentions".


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据1直接写影片被描述为 Pretty in Pink 与 Cruel Intentions 的混合；回答未附加 1986 年等证据未给出的事实。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [652:739] The film has been described as a cross between "Pretty in Pink" and "Cruel Intentions".


**仅用于正确性诊断的参考答案**：["Pretty in Pink"]


输入 SHA-256：`597c3e416fcdaa73f721522a8e417d04f32cfb1df7c396847de69fca8333ae1c`；回答 SHA-256：`6a86dc86c4c5abc293d278e66f3c705198ce4a8601378ca2e5898b88c17c8b27`。


## 16. sample:8ab6b71f96a0c0a06e6c177fbab174397a3f0ee97ff7a1da668987a8b3d943a2


**问题**：Los pájaros was released by the co-founder of which band?


**回答**：Vicentico, the co-founder of Los Fabulosos Cadillacs, was released by the band Los Pájaros.


**完整可见证据**：


> [Evidence 1; title: Los pájaros; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Los pájaros (The Birds) is the third studio album by the pop rock artist Vicentico. It was released in 2006 through BMG.

> 

> [Evidence 2; title: Arena en los Bolsillos; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Arena en los bolsillos is the first solo studio album from Spanish musician Manolo García, released in 1998. The album contains 12 individual songs, plus an alternate version of the song "Carbón y ramas secas" and an instrumental version of the song "Pájaros de barro."

> 

> [Evidence 3; title: Beaks: The Movie; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Beaks: The Movie (Spanish: "El ataque de los pájaros") is a 1987 Mexican horror movie directed by René Cardona Jr. It stars Michelle Johnson and Christopher Atkins as reporters trying to figure out why birds have starting attacking people. It was first released in Europe in 1987 and also known as "Beaks: The Birds 2", "Birds of Prey" and "Evil Birds".

> 

> [Evidence 4; title: Vicentico; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Gabriel Julio Fernández Capello (born (1964--) 24, 1964 in Buenos Aires, Argentina) is a musician and composer better known by his stage name Vicentico. Co-founder and vocalist of the band Los Fabulosos Cadillacs along with Flavio Cianciarulo. He was part of the group since its creation in 1984 to the year 2001, when he began a solo career as a singer.

> 

> [Evidence 5; title: Exotic Birds and Fruit; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Exotic Birds and Fruit is the seventh full-length studio album by British progressive rock band Procol Harum. It was released in 1974. Of special note is the release of the album in Argentina, calling the album "Pájaros Y Frutas Exóticas" (literally translated as "Birds and Exotic Fruit"). The cover artwork for the album is by Jakob Bogdani, a noted Slovak artist whose paintings centred on exotic birds and fruit.


**助手建议**：证据支持 `contradicted`；答案正确性 `incorrect`。

证据1将 Los pájaros 定义为 Vicentico 的专辑，证据4称 Vicentico 为 Los Fabulosos Cadillacs 联合创始人。回答反称 Vicentico 被 Los Pájaros 乐队发行，颠倒人物与作品并把专辑说成乐队。虽然含正确乐队名，整句关系错误。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [84:167] Los pájaros (The Birds) is the third studio album by the pop rock artist Vicentico.

- [1251:1341] Co-founder and vocalist of the band Los Fabulosos Cadillacs along with Flavio Cianciarulo.


**仅用于正确性诊断的参考答案**：["Los Fabulosos Cadillacs"]


输入 SHA-256：`712d0b1500e4302db37a20ef1b4d38e5eb01f8b0119bf0eafb1d294a7ff7dbe9`；回答 SHA-256：`d062796c60028717e75de6a5b7ee4b985e7e046f4ee5cde63399f488b91b6e35`。


## 17. sample:ec12579c775c45e80eaf9b0a6c6430cbf3759c14d50ae431904021f940b4b783


**问题**：Dana Mase is mostly known for her title track on what tv show starring James Van Der Beek?


**回答**：Dana Mase's title track was featured in the TV show "Dawson's Creek", starring James Van Der Beek.


**完整可见证据**：


> [Evidence 1; title: Dana Mase; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Dana Mase is an American pop singer and songwriter. She has released five albums so far: "Diary" (1994), "Sitting with an Angel" (1995), "Through the Concrete & the Rocks" (1998), "Thread of Blue" (2004) and "The Colors of Black and White" (2007). She is mostly known for the title track from the album "Sitting with an Angel", which was featured in the television show, "Dawson's Creek". She has worked with producers Steve Addabbo in "Through the Concrete and Rocks" and Neil Dorfsman in "Thread of Blue".

> 

> [Evidence 2; title: What Would Diplo Do?; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> What Would Diplo Do? is an American comedy television series created by Brandon Dermer and James Van Der Beek. The series stars James Van Der Beek, Dillon Francis, Dora Madison Burge, Jamar Malachi Neighbors, Bobby Lee and H. Michael Croner. The series premiered on August 3, 2017, on Viceland.

> 

> [Evidence 3; title: Hal Ozsan; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Halil "Hal" Özşan (born 26 October 1976) is a Turkish Cypriot-born British actor, screenwriter and producer. As an actor he is best known for various series regular and recurring roles on shows such as "The Blacklist", "Graceland", "Impastor", "90210", "Kyle XY", and "Dawson's Creek". As a screenwriter and producer he is best known as Co-Executive Producer and co-writer of the Viceland comedy "What Would Diplo Do? " starring James Van Der Beek

> 

> [Evidence 4; title: Harmsen van der Beek; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Eelco Martinus ten Harmsen van der Beek (more commonly Harmsen van der Beek or just Beek; October 8, 1897 in Amsterdam – July 24, 1953 in Blaricum) was a Dutch illustrator and commercial artist. Abroad, he is best remembered for his illustration of Enid Blyton's Noddy books.

> 

> [Evidence 5; title: Carters Get Rich; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Carters Get Rich is a 2017 British sitcom airing on Sky 1. The show follows the exploits of the Carter family after 11 year old Harry creates an app that sells for £10m. The show stars James Van Der Beek as the American billionaire who buys the app. The show is written by Claire Downes, Stuart Lane and Ian Jarvis. The first episode aired 31 March 2017. The season consists of six episodes.


**助手建议**：证据支持 `unsupported`；答案正确性 `correct`。

Dawson's Creek 这一问答目标与参考答案一致，证据1支持歌曲被该剧使用。但回答额外说该剧由 James Van Der Beek 主演，完整可见证据未建立这层关系；题干预设不能代替证据，隐藏金标支撑亦不能补入。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [410:470] which was featured in the television show, "Dawson's Creek".


**仅用于正确性诊断的参考答案**：["Dawson's Creek"]


输入 SHA-256：`105870c167dcf7d488850ed02cc892ca0108682e21e43fbd16db7c153f63ef72`；回答 SHA-256：`820dcddd56a8c9a9134e03d7c532bb234e7c75d13247c779294808efaf4d89cd`。


## 18. sample:7f407397a10c6020bdee454d548d03a483dc12226bb5fd1ba937ec5a0cf06abd


**问题**：The song Silence, a song written by producer KF Marshmello, features singer-songwritter who's best known for which debut single?


**回答**：The song Silence, a song written by producer KF Marshmello, features singer-songwritter Khalid, who is best known for his debut single "Location."


**完整可见证据**：


> [Evidence 1; title: Silence (Marshmello song); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "Silence" is a song by electronic dance music producer and DJ Marshmello, featuring American singer-songwriter Khalid. It was written by Khalid and Marshmello, with production handled by the latter. The song was released through RCA Records on August 11, 2017.

> 

> [Evidence 2; title: The Silence (song); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "The Silence" is a song by British singer Alexandra Burke from her debut studio album "Overcome" (2009). The song was written by Bilal Hajji and Savan Kotecha, along with the song's producer Nadir "RedOne" Khayat. The song was released as a promotional single in anticipation of the re-release of "Overcome" (2010). Burke stated that the song was written when her aunt told the singer about how she and her partner were experiencing troubles in their relationship, and that they were not telling each other how they felt. In response, Burke asked her aunt why he was letting the silence in their relationship do the talking instead of them discussing it. "The Silence" is an R&B and pop-influenced power ballad and instrumentation consists of a piano, a guitar and drums. The lyrics of the song feature the protagonist asking why the other person in the relationship remains silent about their difficulties instead of talking about them.

> 

> [Evidence 3; title: Never Gone (Andee song); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "Never Gone" is a song written and recorded by Canadian singer-songwriter Andee for her debut studio album, "Black and White Heart" (2015). The song was co-written and produced by Sébastien Lefebvre, best known as the rhythm guitarist and backing vocalist for Canadian band Simple Plan. "Never Gone" was released May 19, 2014 as Andee's debut single and the lead single for the album. Upon release, the single was available in both English and French, as a tribute to the co-writers' French Canadian heritage.

> 

> [Evidence 4; title: Alone (Marshmello song); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "Alone" is the major-label debut single released by DJ and record producer Marshmello. It was first released in May 2016, then later released as a digital download on June 17, 2016 on iTunes and for streaming on Spotify. Upon its release, it charted on the Canadian Hot 100 and US "Billboard" Hot 100, and its music video has received over 560 million views on YouTube, making it the first Monstercat song to reach this view total and easily making it the label's most popular release.

> 

> [Evidence 5; title: Just in Love; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> "Just in Love" is a song performed by the American singer Joe Jonas. The song was released on September 13, 2011 by Hollywood Records, as the second and final single from his debut album, "Fastlife" (2011). The song was written by Jonas and James Fauntleroy and produced by Rob Knox. The song garnered mixed reception from music critics. An official remix of the track features a verse from American rapper Lil Wayne and slightly altered production; it received a Parental Advisory sticker for this because of the explicit lyrics Lil Wayne raps.


**助手建议**：证据支持 `unsupported`；答案正确性 `correct`。

核心答案 Location 与参考一致；证据1只支持 Silence 与 Khalid 的关系，没有 Khalid 的首单信息。Location 来自模型记忆或不可见支撑的可能性不构成证据支持，不能因答对就标 supported。完整复核仍须检查所有可见段落。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [98:216] "Silence" is a song by electronic dance music producer and DJ Marshmello, featuring American singer-songwriter Khalid.


**仅用于正确性诊断的参考答案**：["\"Location\""]


输入 SHA-256：`fcb30bae1dc8f005fe162c5e6fda22abb6b38cf6afb2a20e58fb75f03cb54b64`；回答 SHA-256：`9152c564860ad53784904a5a1e5b5aae1fe68d5a1daa34f9a8347b5ac88c4c87`。


## 19. sample:6049a278afae4541c3a2283a61b3dcecd3d10fd28180afa65e37fb3e2f10c3cb


**问题**：George Walker was an English footballer, who played for which professional football club based in Selhurst, London?


**回答**：George Walker played for Crystal Palace FC.


**完整可见证据**：


> [Evidence 1; title: Crystal Palace F.C.; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Crystal Palace Football Club is a professional football club based in Selhurst, London, that plays in the Premier League, the top tier of English football.

> 

> [Evidence 2; title: George Walker (footballer, born 1877); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> George Walker (1877–1930) was an English footballer who played for Crystal Palace as a full back.

> 

> [Evidence 3; title: Arsenal F.C. in European football; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Arsenal Football Club is an English professional football club based in Holloway, North London. The club's first European football match was played against Copenhagen XI on 25 September 1963, and it has since participated in European club competitions on several occasions, most of which organised by the Union of European Football Associations (UEFA). Arsenal has won two European honours: the Inter-Cities Fairs Cup in 1970 and the Cup Winners' Cup in 1994 – the latter title recognised by the European confederation. The club played the 1994 European Super Cup and repeated its presence in the following year's Cup Winners' Cup final. Arsenal also reached the final of the UEFA Cup in 2000, and became the first London team to appear in a UEFA Champions League final, in 2006.

> 

> [Evidence 4; title: Sam Fisher (footballer); version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Sam Fisher (born 10 July 1982) is a former professional Australian rules footballer who played for the St Kilda Football Club in the Australian Football League (AFL).

> 

> [Evidence 5; title: Newcastle United F.C.; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Newcastle United Football Club is an English professional association football club based in Newcastle upon Tyne, that currently plays in the Premier League, the top tier of English football. Newcastle United was founded in 1892 by the merger of Newcastle East End and Newcastle West End, and has played at its current home ground, St James' Park, ever since. The ground was developed into an all-seater stadium in the mid-1990s and now has a capacity of 52,354.


**助手建议**：证据支持 `supported`；答案正确性 `correct`。

证据2直接说 George Walker played for Crystal Palace；证据1将俱乐部全名与所在地连接，FC 与 Football Club 可视为别名。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [359:456] George Walker (1877–1930) was an English footballer who played for Crystal Palace as a full back.


**仅用于正确性诊断的参考答案**：["Crystal Palace Football Club"]


输入 SHA-256：`2b99a335991dece5a851f5c0d6bc00958783dfc6c73b4fe110c4b1e73b133ee7`；回答 SHA-256：`26c86b9e6f3302773614114aece715225740fd950014b904d9ab248d21d1882f`。


## 20. sample:fe46cafde9042c4fffbdc0cfd061e1062aa221a99a750f694c2a5b25bd73f58e


**问题**：When was the Spanish footballer who plays as a right back for the team that was founded in 1919 and plays home matches at Estadio Nueva Condomina born?


**回答**：INSUFFICIENT_EVIDENCE


**完整可见证据**：


> [Evidence 1; title: Real Murcia; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Real Murcia Club de Fútbol, S.A.D., known as Real Murcia (] , "Royal Murcia"), is a Spanish football club based in Murcia, in the namesake region. Founded in 1919, it currently plays in Segunda División B – Group 4, playing home matches at "Estadio Nueva Condomina", which holds 31,179 spectators.

> 

> [Evidence 2; title: Albacete Balompié; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Albacete Balompié, S.A.D. is a Spanish football team based in Albacete, in the autonomous community of Castile–La Mancha. Founded on 2 August 1940, it currently plays in Segunda División, holding home matches at "Estadio Carlos Belmonte", with a capacity of 17,300. It is currently owned by Spanish footballer Georges David Kabchi.

> 

> [Evidence 3; title: Estadio Nueva Condomina; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Estadio Nueva Condomina is a multi-use stadium in Murcia, Spain. Completed in 2006, it is used mostly for football matches and hosts the homes matches of Real Murcia. The stadium has a capacity of 31,179 people. It replaced their previous stadium La Condomina.

> 

> [Evidence 4; title: CD Cristo Atlético; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> Club Deportivo Palencia Cristo Atlético is a Spanish football team based in Palencia, in the autonomous community of Castile and León. Founded in 1985, it plays in Tercera División – Group 8, holding home games at "Estadio Nueva Balastera", with a capacity of 8,070 seats.

> 

> [Evidence 5; title: Estadio Cincuentenario; version: 1908d6afbbead072334abe2965f91bd2709910ab]

> The Estadio Cincuentenario is an indoor arena in Formosa, Argentina. It hosts basketball, volleyball, futsal, boxing, handball and artistic events. Club La Unión plays at this stadium its home matches for the Liga Nacional de Básquet, the top level of the Argentine basketball league system. The same club also has a volleyball team that plays its home matches for the Liga Argentina de Voleibol – Serie A1 at the Cincuentenario as well.


**助手建议**：证据支持 `undetermined`；答案正确性 `undetermined`。

拒答单列。可见证据包含 Real Murcia 的创立时间与球场，却没有题目所问右后卫的身份与出生日期；隐藏金标中的 Juanra 不能视为已检索到。此例适合记录缺失多跳末端证据后的合理拒答候选。


**可见文本定位**（Unicode 字符偏移，左闭右开）：

- [231:349] Founded in 1919, it currently plays in Segunda División B – Group 4, playing home matches at "Estadio Nueva Condomina"


**仅用于正确性诊断的参考答案**：["born 18 January 1995"]


输入 SHA-256：`ecd05f23fa652fe5da545f34db144dc5b6098eb99207031a16261d15f669323b`；回答 SHA-256：`a5fafaa214fa671c293071b6dac23e4c0f0bd9fe935f3d65c96c16bacf6ae345`。
