flowchart TB
    subgraph Frontend [" "]
        direction TB
        F[Frontend React App<br/>:80]
    end
    
    subgraph Gateway [" "]
        direction TB
        AG[API Gateway<br/>Express.js :3000]
    end
    
    subgraph Services [" "]
        direction TB
        US[User Service<br/>FastAPI :8000]
        RS[Recipe Service<br/>FastAPI :8001] 
        MPS[Meal Planner<br/>FastAPI :8002]
        NS[Notification Service<br/>FastAPI :8003]
    end
    
    subgraph External [" "]
        direction TB
        Q[Qdrant Vector DB<br/>:6333]
        G[Google Gemini API<br/>External]
    end
    
    F -->|All API Requests| AG
    
    AG -->|POST /api/auth/login<br/>GET /api/users/preferences| US
    AG -->|GET /api/recipes<br/>POST /api/recipes/recommendations| RS  
    AG -->|POST /api/meal-plans<br/>GET /api/meal-plans/grocery-list| MPS
    AG -->|POST /api/notifications| NS
    
    MPS -->|GET /api/users/preferences<br/>GET /api/users/allergies| US
    MPS -->|POST /recommendations<br/>GET /recipes/detail| RS
    
    RS -->|Vector Search<br/>Semantic Queries| Q
    RS -->|AI Query Generation<br/>Recipe Analysis| G
    MPS -->|Meal Plan Generation<br/>Grocery List Creation| G
    
    style F fill:#e3f2fd
    style AG fill:#fff3e0
    style US fill:#e8f5e8
    style RS fill:#f3e5f5
    style MPS fill:#fff8e1
    style NS fill:#fce4ec
    style Q fill:#f1f8e9
    style G fill:#fff3e0