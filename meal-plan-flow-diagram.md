flowchart LR
    subgraph L1 [" "]
        A[User Chat Input] --> B[Load User Preferences]
        B --> C[Recipe Service Call]
        C --> D[AI Query Generation]
        D --> E[Vector Search Engine]
    end
    
    subgraph L2 [" "]
        F[Retrieved Recipe Results] --> G[Final Prompt Assembly]
        G --> H[Gemini LLM Generation]
        H --> I[Structured Meal Plan]
        I --> J[Database Storage]
    end
    
    E --> F
    A -.-> D
    
    style A fill:#e1f5fe
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style H fill:#fff3e0
    style I fill:#e8f5e8