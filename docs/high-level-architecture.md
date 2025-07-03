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
## Usecase

```mermaid
flowchart LR
 subgraph PipelineControl["Pipeline Control"]
        Create(["Create Pipeline"])
        Delete(["Delete Pipeline"])
        Run(["Run Pipeline"])
        Rerun(["Rerun Pipeline - Ignore Previous Results"])
        Resume{{"New Run <br>"}}
        Retry{{"Rerun Completed Run"}}
        n2@{ label: "<span style=\"padding-left:\">Resume Incomplete Run</span>" }
        n1{{"Retry Recoverable Errors"}}
  end
 subgraph ModelInput["Add Models"]
        AddModel(["Add Models"])
        AddFolder{{"From Folder"}}
        AddCode{{"By Code"}}
  end
 subgraph Configuration["Configuration"]
        ModelInput
        Algo(["Configure Algorithms"])
        Metrics(["Configure Metrics"])
        Plots(["Configure Plots"])
  end
 subgraph PluginsArea["Plugins"]
        CustomAlgo(["Custom Algorithms"])
        CustomMetrics(["Custom Metrics"])
        CustomPlots(["Custom Plots"])
  end
 subgraph Convenience["Convenience Functions"]
        Export(["Export Results as DataFrame"])
  end
 subgraph PipelineSystem["Pipeline System"]
        PipelineControl
        Configuration
        PluginsArea
        Convenience
  end
    User["User"] --> Create & Delete & Run & Rerun & Configuration & PluginsArea & Convenience
    AddModel -.-> AddFolder & AddCode
    Run -.-> Resume & Retry & n2 & n1
    Convenience --> PipelineSystem

    n2@{ shape: hexagon}
     Create:::action
     Delete:::action
     Run:::action
     Rerun:::action
     Resume:::auto
     Retry:::auto
     n2:::auto
     n1:::auto
     AddModel:::config
     AddFolder:::extend
     AddCode:::extend
     Algo:::config
     Metrics:::config
     Plots:::config
     CustomAlgo:::plugin
     CustomMetrics:::plugin
     CustomPlots:::plugin
     Export:::other
     User:::actor
     User:::actor
    classDef actor font-size:16px,stroke:#333,fill:#fff,stroke-width:2px,font-weight:bold,icon:stickman
    classDef action fill:#fef6e4,stroke:#666,stroke-width:1px
    classDef auto fill:#e0f7fa,stroke:#00838f,stroke-width:1px,stroke-dasharray: 4 2
    classDef config fill:#f3e5f5,stroke:#6a1b9a
    classDef plugin fill:#fff3e0,stroke:#ef6c00
    classDef other fill:#e8f5e9,stroke:#388e3c
    classDef extend fill:#fdf3ff,stroke:#ba00b4,stroke-dasharray: 4 2,stroke-width:1.5px

```
## Pipeline/Bench job

```mermaid
---
config:
  theme: redux
  layout: fixed
---
flowchart LR
    start["Start"] --> validate(["Validate pipeline"])
    validate ---> features(["Compute features<br>(e.g. nr. variables, constraints)"])
    features --> solvers["Run solver<br>(for each algorithm - schedule job)"]
    solvers --> queue["Job Queue"]
    queue --> collect>"Collect / wait for results"]
    collect --> metrics(["Compute metrics<br>(for each metric)"])
    metrics --> plots(["Generate plots<br>(for each plot)"])
    plots --> done["Done"]
    validate -- Load pipeline config --> db1[("SQLite DB")]
    db1 -- Status, schema --> validate
    features -- Store features --> db2[("SQLite DB")]
    db2 -- Config, model data --> features
    solvers -- Store job info --> db3[("SQLite DB")]
    db3 -- Algorithm config --> solvers
    collect -- Store raw results --> db4[("SQLite DB")]
    db4 -- Job results --> collect
    metrics -- Store metrics --> db5[("SQLite DB")]
    db5 -- Raw results --> metrics
    plots -- Store plots --> db6[("SQLite DB")]
    db6 -- Metric values --> plots
    start@{ shape: f-circ}
    solvers@{ shape: subproc}
    queue@{ shape: h-cyl}
    done@{ shape: fr-circ}
     db1:::db
     db2:::db
     db3:::db
     db4:::db
     db5:::db
     db6:::db
    classDef db fill:#f0f0f0,stroke:#999,stroke-width:2px


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
    n30 --> n7
    n10 --> n32

    n9@{ shape: card}
    n30@{ shape: f-circ}
    n32@{ shape: fr-circ}
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
- Model Metadata (from Compute features)
- Algorithm
- Solve Job Status
- Result/Solution
- Result/Solution Postprocessing
- Metrik

```mermaid
erDiagram
    BenchConfig ||--o{ Model : includes
    BenchConfig ||--o{ AlgorithmConfig : "has config"
    BenchConfig ||--o{ MetricConfig : "evaluates with"
    BenchConfig ||--o{ PlotConfig : "visualizes using"

    AlgorithmConfig ||--o{ SolveJob : "in combination with"
    Model ||--o{ SolveJob : "in combination with"

    SolveJob ||--|{ SolveJobRun : "runs"
    SolveJobRun ||--o| Result : "produces"

    MetricConfig ||--o{ MetricResult : "used in"
    Result ||--o{ MetricResult : "contains"

    Model ||--|| ModelMetadata : "has"

```

![img.png](https://d2slcw3kip6qmk.cloudfront.net/marketing/pages/chart/erd-symbols/ERD-Notation.PNG)
## Stuff we need
- DB => sqlite for now
- Queuing => [Huey](https://github.com/coleifer/huey)
  - Looks well maintained
  - SQLight based queues possible
- [Returns Lib](https://pypi.org/project/returns/#description) for better error handling and cleaner code
- Pydantic
- Luna-Quantum
