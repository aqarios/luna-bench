# This file descibes the high-level architecture of luna-bench

## Mindmap of ideas/features etc
```mermaid
mindmap
  root((core features))
    Bench Job
        One run of a benchmark
        One Model
        One Algorithm config
        List of Preprocessingsteps
        Result of Preprocessing
        Preprocessing intermediat or f
        X repetitions
        X solve jobs
            Requested
            Failed - Recoverable
            Failed - Not recoverable
            Done
        Y config of Metrics
        Y Metric results

    Pipeline
        Configuration
            Algorithm
                Add/Delete/Show Local existing algorithms
                Add/Delete/Show Luna algorithms
                Add/Delete/Show Custom algorithms
            Model list
                Add/Delete/Show Models
        Management
            Run
                run full pipeline
                run only algorithms
                run only metrik generation
                run only fetch results

            Load pipeline
            Store pipeline
            Delete pipeline

    Logging
    Customization
        Custom Transformations?
        Custom Algorithms
        Custom Metrics

```

## Pipeline/Bench job

```mermaid
---
config:
  theme: redux
  layout: fixed
---
flowchart TD
    n1["Filled Circle"] --> n2["More models configured <br>"]
    n2 -- Yes <br> --> n3["Preprocess"]
    n3 --> n2
    n2 -- No <br> --> n4["More Algorithm conmfigured"]
    n4 -- Yes <br> --> n5["Queue Job"]
    n5 --> n4
    n4 -- No <br> --> n6["Wait for results <br>"]
    n7["More Metrics configured"] -- Yes <br> --> n8["Calculate Metric"]
    n7 -- No <br> --> n9["More Plots configured"]
    n8 --> n7
    n9 -- Yes <br> --> n10["Plot"]
    n9 -- No <br> --> n11["Untitled Node"]
    n10 --> n9
    n6 --> n12["More Algorithm conmfigured"]
    n12 -- No <br> --> n7
    n12 -- Yes <br> --> n13["Postrosessing of result"]
    n13 --> n12
    n1@{ shape: f-circ}
    n2@{ shape: diam}
    n3@{ shape: card}
    n4@{ shape: diam}
    n7@{ shape: diam}
    n9@{ shape: diam}
    n11@{ shape: fr-circ}
    n12@{ shape: diam}

```
### Preprocessing
```mermaid
---
config:
  theme: redux
  layout: fixed
---
flowchart TD
 subgraph s1["Prepare Models"]
        n8["Load model"]
        n9["Has preprocessing <br>"]
        n11["Has more preprossing"]
        n10["Preprocess"]
        n12["Frames Circle"]
        n13["Store preprocessed model"]
        n14["Filled Circle"]
  end
    n9 -- Yes <br> --> n8
    n10 --> n11
    n9 -- No <br> --> n12
    n11 -- Yes <br> --> n10
    n11 --> n13
    n13 --> n12
    n14 --> n9
    n8 --> n10
    n8@{ shape: proc}
    n9@{ shape: diam}
    n11@{ shape: diam}
    n12@{ shape: fr-circ}
    n14@{ shape: f-circ}

```

### Algorithm execution
```mermaid
flowchart TD
 subgraph s1["Async Run"]
        n7["Run Async"]
        n8["Load Model"]
        n9["Run User Interface"]
        n10["Signal Job Id"]
        n30["Filled Circle"]
        n32["Frames Circle"]
  end
 subgraph s2["Sync Run"]
        n1["Run"]
        n2["Load Model"]
        n3["Run User Interface"]
        n4["Store Result"]
        n5["Signal Done"]
        n29["Filled Circle"]
        n31["Frames Circle"]
  end
 subgraph s3["Async Retriever"]
        n26["Filled Circle"]
        n18["Is Async Task remaining"]
        n25["Frames Circle"]
        n22["Get Async Job"]
        n23["Loader Interface"]
        n19["Retrieve Result"]
        n20["Is Done/Error"]
        n27["Result changed"]
        n28["Update Result"]
  end
    n1 --> n2
    n2 --> n3
    n3 --> n4
    n4 --> n5
    n7 --> n8
    n8 --> n9
    n9 --> n10
    n18 -- Yes --> n22
    n22 --> n23
    n23 --> n19
    n20 -- Yes --> n18
    n20 -- No --> n22
    n18 --> n25
    n26 --> n18
    n19 --> n27
    n27 -- No --> n20
    n27 --> n28
    n28 --> n20
    n29 --> n1
    n30 --> n7
    n5 --> n31
    n10 --> n32
    n9@{ shape: card}
    n30@{ shape: f-circ}
    n32@{ shape: fr-circ}
    n3@{ shape: card}
    n29@{ shape: f-circ}
    n31@{ shape: fr-circ}
    n26@{ shape: f-circ}
    n18@{ shape: diam}
    n25@{ shape: fr-circ}
    n23@{ shape: card}
    n20@{ shape: diam}
    n27@{ shape: diam}
    n28@{ shape: rect}

```

## Core components
- Model
- Model Preprocessing
- Algorithm
- Result/Solution
- Result/Solution Postprocessing
- Metrik
