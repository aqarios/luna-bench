```mermaid
erDiagram
    Model ||--|| ModelMetadata: has
    Model }|..|{ ModelSet: "belongs to"
    ModelMetadata }|..|{ ModelSet: "related to"

    Model {
        int id PK
        bytes encoded_model
    }

    ModelMetadata {
        int id PK
        string name UK
        int varcount
    }

    ModelSet {
        int id PK
        string name UK
    }

    Benchmark {
        int id PK
        string name UK
    }

    MetricModelConfig {
        int id PK
        string name UK
    }

    MetricModelResult {
        int id PK
    }

    MetricConfig {
        int id PK
        string name UK
    }

    MetricResult {
        int id PK
    }

    AlgorithmConfig {
        int id PK
    }

    BackendConfig {
        int id PK
    }

    AlgorithmModelResult {
        int id PK
    }


```
