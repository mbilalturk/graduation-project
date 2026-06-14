# 🎬 Demo Video — Speech Script (English)

**Project:** Prediction of Bus Arrival Times in Public Transportation
**Authors:** Muhammed Bilal Türk · Ömer Faruk Koç
**Estimated length:** ~3.5–4 minutes
**Screen:** `demo/index.html` open in a browser (full screen recommended)

> **Note:** Since there are two of you, you can split the sections (e.g. one person does 1–3, the other 4–6). The **[SCREEN]** cues tell you what to show, **Speech:** what to say.

---

## 1. Opening (~25 s)
**[SCREEN] Top of the page — title and names visible.**

**Speech:**
> Hello. I'm Muhammed Bilal Türk, and this is my project partner Ömer Faruk Koç. Our graduation project is about **predicting bus arrival times** in public transportation. Our supervisor is Prof. Dr. Didem Gözüpek.
>
> At any bus stop there is one question everyone asks: "When will my bus arrive?" We set out to answer that question using real data from the İzmir ESHOT network and machine learning.

---

## 2. Problem and Data (~30 s)
**[SCREEN] Show the "Dataset" cards (81,575 segments, 73 days, 48 buses).**

**Speech:**
> What we actually predict is the travel time of a bus **from one stop to the next**. By accumulating these segments, we get an arrival estimate for the whole route.
>
> We collected our own data: from İzmir's open API we recorded bus positions every 30 seconds, along with weather and traffic, over roughly three months. For Route 502 this gives us **more than 81 thousand clean segments**. The average segment takes only about 1.2 minutes — so the target is short and quite variable.

---

## 3. Model Comparison (~40 s)
**[SCREEN] Scroll to the "Model Comparison" section — the bar chart.**

**Speech:**
> We trained many models, from a naïve schedule-based predictor to deep learning, and compared them all **on the same test set**.
>
> The result: our best models predict with a Mean Absolute Error of about **0.43 minutes** — roughly **26 seconds** — far below the schedule-based baseline.
>
> What is interesting is this: our statistical tests show that the classical **XGBoost and the deep LSTM are equivalent** — the deep model does not beat the classical one. Both are better than Random Forest. So the most practical model is actually the simple one: XGBoost.

---

## 4. Live Prediction (~40 s)
**[SCREEN] "Live Prediction" — select a segment, click the time-of-day buttons.**

**Speech:**
> Here we can try the system live. I select a stop segment...
>
> *(Pick a segment, for example one of the middle stops.)*
>
> ...and I change the time of day. As you can see, the estimated travel time goes up during the **morning peak** and down at **night**. The model also shows the GTFS scheduled time; the difference between the two is how much the bus deviates from the schedule — and that deviation is one of our model's strongest inputs.

---

## 5. Condition Analysis and Generalization (~35 s)
**[SCREEN] The four "Condition-Based Analysis" boxes, then the "Generalization" table.**

**Speech:**
> When we break the error down by condition, meaningful patterns emerge: the **morning peak** is the hardest time of day, the error rises noticeably in **rainy weather**, and at the **start of a route** — where there is no recent history yet — prediction is naturally harder.
>
> Most importantly, our method is not specific to one line: on routes **268 and 565** it gave consistent results without any changes. So it generalizes.

---

## 6. Reference Comparison, Findings, and Closing (~50 s)
**[SCREEN] The "Reference Study" and "Methodological Findings" sections.**

**Speech:**
> The reference paper reported an error of 2.97 minutes; we reach a much lower error at the segment scale. But here we have to be **honest**: we predict short inter-stop segments, while the paper predicts full-route arrivals — the scales are different, so we do not simply claim we beat it.
>
> In fact, the most valuable part of our project is this honesty. We tested every improvement with a controlled experiment and reached three key findings. One: the achievable accuracy is bounded by a **measurement floor** set by the data's sampling rate — it needs denser data, not a more complex model. Two: **more sophisticated is not always better** — the simple model matched the complex one. Three: a **fair comparison** corrected the impression that deep learning was best.
>
> In short: we built a reproducible, honestly evaluated, and generalizable bus arrival time prediction system. Thank you.

---

## 🎥 Recording Tips
- Put the browser in **full screen** (F11); scroll slowly so the section you are talking about is on screen.
- During the **live prediction**, make 1–2 interactions (change segment and time of day) — it conveys a "working system".
- Check before recording that the numbers and characters render correctly.
- `demo/index.html` needs **no internet** (all data is embedded) — it works offline.
- To stay on time, keep section 4 (live prediction) short and the whole video lands around ~3 minutes.
