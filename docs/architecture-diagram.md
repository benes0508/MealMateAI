# MealMateAI Architecture Diagram

This file contains the Mermaid code for generating the MealMateAI system architecture diagram. You can view this diagram by pasting the code into any Mermaid-compatible viewer such as:

- [Mermaid Live Editor](https://mermaid.live/)
- GitHub markdown
- GitLab markdown
- VS Code with Mermaid extension

## System Architecture Diagram

```mermaid
graph TD
    %% Define styles with better text contrast
    classDef client fill:#d4f1f9,stroke:#333,stroke-width:1px,color:#000
    classDef frontend fill:#ffcc99,stroke:#333,stroke-width:1px,color:#000
    classDef gateway fill:#c2e0c6,stroke:#333,stroke-width:1px,color:#000
    classDef service fill:#e0c6c2,stroke:#333,stroke-width:1px,color:#000
    classDef database fill:#c6c2e0,stroke:#333,stroke-width:1px,color:#000
    classDef external fill:#e0e0c2,stroke:#333,stroke-width:1px,color:#000

    %% Client Layer
    WebBrowser[Web Browser]:::client
    MobileBrowser[Mobile Browser]:::client
    iOSApp[iOS App<br/>Future]:::client
    AndroidApp[Android App<br/>Future]:::client

    %% Frontend Layer
    FrontendReact[Frontend<br/>React]:::frontend

    %% API Gateway
    APIGateway[API Gateway<br/>Express.js]:::gateway

    %% Microservices
    UserService[User Service<br/>FastAPI]:::service
    RecipeService[Recipe Service<br/>FastAPI]:::service
    MealPlannerService[Meal Planner<br/>Service FastAPI]:::service
    NotificationService[Notification<br/>Service FastAPI]:::service

    %% Databases
    UserDB[User DB<br/>MySQL]:::database
    PostgresDB[PostgreSQL<br/>Recipe & Meal Plan DBs]:::database
    QdrantDB[Qdrant Vector DB<br/>Recipe Embeddings]:::database
    NotificationDB[Notification DB<br/>Future]:::database

    %% External Services
    EmailService[Email Service<br/>SMTP]:::external
    RecipeAPI[Recipe APIs<br/>Future]:::external
    CloudStorage[Cloud Storage<br/>AWS S3]:::external
    Analytics[Analytics<br/>Future]:::external
    GeminiAPI[Google Gemini API<br/>LLM]:::external

    %% Client to Frontend connections
    WebBrowser --> FrontendReact
    MobileBrowser --> FrontendReact
    iOSApp --> FrontendReact
    AndroidApp --> FrontendReact

    %% Frontend to API Gateway
    FrontendReact -- HTTPS --> APIGateway
    
    %% API Gateway to Microservices
    APIGateway -- REST --> UserService
    APIGateway -- REST --> RecipeService
    APIGateway -- REST --> MealPlannerService
    APIGateway -- REST --> NotificationService

    %% Microservices to Databases
    UserService -- SQL --> UserDB
    RecipeService -- SQL --> PostgresDB
    RecipeService -- Vector Search --> QdrantDB
    MealPlannerService -- SQL --> PostgresDB
    NotificationService -- SQL --> NotificationDB

    %% Inter-service communication
    RecipeService -- Get user preferences --> UserService
    MealPlannerService -- Get recipes --> RecipeService
    MealPlannerService -- Get user preferences --> UserService
    NotificationService -- Get user contact info --> UserService
    NotificationService -- Get meal plans --> MealPlannerService

    %% External service connections
    NotificationService -- Send emails --> EmailService
    RecipeService -- External recipes --> RecipeAPI
    UserService -- Store images --> CloudStorage
    RecipeService -- Store images --> CloudStorage
    MealPlannerService -- Usage data --> Analytics
    MealPlannerService -- LLM Generation --> GeminiAPI
    RecipeService -- Generate embeddings --> GeminiAPI

    %% Add a title
    subgraph "MealMateAI System Architecture"
    end
```

## Component Communication Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Frontend (React)
    participant Gateway as API Gateway (Express.js)
    participant UserSvc as User Service (FastAPI)
    participant RecipeSvc as Recipe Service (FastAPI)
    participant MealSvc as Meal Planner Service (FastAPI)
    participant NotifSvc as Notification Service (FastAPI)
    participant UserDB as MySQL Database
    participant PostgresDB as PostgreSQL Database
    participant QdrantDB as Qdrant Vector Database
    participant GeminiAPI as Google Gemini API
    participant EmailSvc as Email Service (SMTP)
    
    %% User authentication flow
    User->>Frontend: Login with credentials
    Frontend->>Gateway: POST /api/users/login
    Gateway->>UserSvc: Forward authentication request
    UserSvc->>UserDB: Verify credentials
    UserDB-->>UserSvc: User data
    UserSvc-->>Gateway: JWT token
    Gateway-->>Frontend: Authentication response
    Frontend-->>User: Login success/failure
    
    %% Meal planning flow
    User->>Frontend: Request meal plan
    Frontend->>Gateway: GET /api/meal-plans
    Gateway->>MealSvc: Forward meal plan request
    MealSvc->>UserSvc: GET user preferences
    UserSvc->>UserDB: Fetch user data
    UserDB-->>UserSvc: User preferences
    UserSvc-->>MealSvc: User preferences
    MealSvc->>RecipeSvc: GET compatible recipes
    RecipeSvc->>QdrantDB: Vector search for recipes
    QdrantDB-->>RecipeSvc: Matching recipes
    RecipeSvc-->>MealSvc: Recipe data
    MealSvc->>GeminiAPI: Generate meal plan with LLM
    GeminiAPI-->>MealSvc: AI-generated meal plan
    MealSvc->>PostgresDB: Store meal plan
    PostgresDB-->>MealSvc: Confirmation
    MealSvc-->>Gateway: Generated meal plan
    Gateway-->>Frontend: Meal plan data
    Frontend-->>User: Display meal plan
    
    %% Shopping list generation
    User->>Frontend: Generate shopping list
    Frontend->>Gateway: GET /api/meal-plans/shopping-list
    Gateway->>MealSvc: Forward shopping list request
    MealSvc->>PostgresDB: Get meal plan ingredients
    PostgresDB-->>MealSvc: Ingredient data
    MealSvc->>RecipeSvc: GET detailed ingredients for meals
    RecipeSvc->>PostgresDB: Query recipe ingredients
    PostgresDB-->>RecipeSvc: Ingredient details
    RecipeSvc-->>MealSvc: Consolidated ingredient data
    MealSvc-->>Gateway: Generated shopping list
    Gateway-->>Frontend: Shopping list data
    Frontend-->>User: Display shopping list
    
    %% Notification scheduling
    MealSvc->>NotifSvc: Schedule meal reminders
    NotifSvc->>UserSvc: GET user contact info
    UserSvc-->>NotifSvc: Email address
    NotifSvc->>EmailSvc: Send email reminder
    EmailSvc-->>NotifSvc: Email sent confirmation
```

## Database Schema Diagram

```mermaid
erDiagram
    %% User Service Database (MySQL)
    USERS {
        int id PK
        string email UK
        string username UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_admin
        datetime created_at
        datetime updated_at
        json allergies
        json disliked_ingredients
        json preferred_cuisines
        json preferences
    }
    
    %% Recipe Service Database (PostgreSQL)
    RECIPES {
        int id PK
        text name
        text_array ingredients
        text_array meal_type
        text_array dietary_tags
        text_array allergens
        text difficulty
        text json_path
        text txt_path
        text_array cuisine
        text_array tags
        text directions
        text img_src
        text prep_time
        text cook_time
        text servings
        text rating
        text nutrition
        text url
        timestamptz created_at
        timestamptz updated_at
    }
    
    %% Meal Planner Service Database (PostgreSQL)
    MEAL_PLANS {
        int id PK
        int user_id FK
        string plan_name
        datetime created_at
        datetime updated_at
        int days
        int meals_per_day
        text plan_data
        text plan_explanation
    }
    
    MEAL_PLAN_RECIPES {
        int id PK
        int meal_plan_id FK
        int recipe_id FK
        int day
        string meal_type
    }
    
    USER_PREFERENCES_CACHE {
        int id PK
        int user_id UK
        text dietary_restrictions
        text allergies
        text cuisine_preferences
        text disliked_ingredients
        datetime updated_at
    }
    
    RECIPE_EMBEDDINGS {
        int id PK
        int recipe_id UK
        text recipe_name
        text ingredients
        text cuisine_type
        vector_768 embedding
        datetime created_at
    }
    
    %% Future/Planned Tables
    NOTIFICATIONS {
        int id PK
        int user_id FK
        string title
        string message
        string type
        string priority
        string related_entity_id
        string related_entity_type
        boolean read
        datetime created_at
        datetime read_at
    }
    
    PANTRY_ITEMS {
        int id PK
        int user_id FK
        string ingredient_name
        float quantity
        string unit
        datetime expiry_date
        datetime created_at
    }
    
    SHOPPING_LISTS {
        int id PK
        int meal_plan_id FK
        string name
        datetime created_at
    }
    
    SHOPPING_LIST_ITEMS {
        int id PK
        int shopping_list_id FK
        string ingredient_name
        float quantity
        string unit
        boolean purchased
        datetime created_at
    }

    %% Relationships
    USERS ||--o{ MEAL_PLANS : creates
    USERS ||--o{ USER_PREFERENCES_CACHE : has_cached_preferences
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ PANTRY_ITEMS : owns
    MEAL_PLANS ||--o{ MEAL_PLAN_RECIPES : includes
    MEAL_PLANS ||--o{ SHOPPING_LISTS : generates
    SHOPPING_LISTS ||--o{ SHOPPING_LIST_ITEMS : contains
    RECIPES ||--o{ RECIPE_EMBEDDINGS : has_embeddings
```

## Deployment Diagram

```mermaid
flowchart TD
    subgraph "Docker Environment"
        subgraph "Frontend Container"
            ReactApp[React Application]
        end
        
        subgraph "API Gateway Container"
            Express[Express.js Server]
            JWTAuth[JWT Authentication]
            RequestRouter[Request Router]
        end
        
        subgraph "User Service Container"
            UserAPI[FastAPI Application]
            UserLogic[Business Logic]
            UserORM[SQLAlchemy ORM]
        end
        
        subgraph "Recipe Service Container"
            RecipeAPI[FastAPI Application]
            RecipeLogic[Business Logic]
            RecipeORM[SQLAlchemy ORM]
        end
        
        subgraph "Meal Planner Container"
            MealAPI[FastAPI Application]
            MealLogic[Business Logic]
            MealORM[SQLAlchemy ORM]
        end
        
        subgraph "Notification Service Container"
            NotifAPI[FastAPI Application]
            NotifLogic[Business Logic]
            NotifORM[SQLAlchemy ORM]
            EmailClient[Email Client]
        end
        
        subgraph "Database Containers"
            MySQL[(MySQL Database)]
            PostgreSQL[(PostgreSQL Database)]
            QdrantVectorDB[(Qdrant Vector Database)]
        end
    end
    
    subgraph "External Services"
        GeminiAPI[Google Gemini API]
        S3[AWS S3]
        SMTP[SMTP Server]
    end
    
    ReactApp -- HTTP --> Express
    Express -- HTTP --> UserAPI
    Express -- HTTP --> RecipeAPI
    Express -- HTTP --> MealAPI
    Express -- HTTP --> NotifAPI
    
    UserORM -- SQL --> MySQL
    RecipeORM -- SQL --> PostgreSQL
    RecipeAPI -- Vector Search --> QdrantVectorDB
    MealORM -- SQL --> PostgreSQL
    NotifORM -- SQL --> PostgreSQL
    
    UserAPI -- HTTP --> RecipeAPI
    RecipeAPI -- HTTP --> MealAPI
    UserAPI -- HTTP --> MealAPI
    MealAPI -- HTTP --> NotifAPI
    UserAPI -- HTTP --> NotifAPI
    
    MealAPI -- LLM API --> GeminiAPI
    RecipeAPI -- Storage --> S3
    NotifAPI -- Email --> SMTP
```

## Using These Diagrams

1. Visit [Mermaid Live Editor](https://mermaid.live/)
2. Copy any of the diagram code sections above (without the ```mermaid part)
3. Paste into the editor 
4. View the rendered diagram
5. Export as SVG or PNG for documentation

You can also embed these diagrams directly in GitHub markdown, GitLab documentation, or other platforms that support Mermaid diagrams.

## RAG Meal Planning Workflow

```mermaid
flowchart TD
    User[User Input<br/>Natural Language Request]
    
    subgraph "Frontend Layer"
        UI[React UI<br/>Meal Planning Page]
    end
    
    subgraph "API Gateway"
        Gateway[Express.js<br/>Authentication & Routing]
    end
    
    subgraph "Meal Planner Service"
        Controller[Meal Plan Controller]
        RAGService[RAG Service]
        EmbedService[Embeddings Service]
        GeminiService[Gemini LLM Service]
        DBService[Database Service]
    end
    
    subgraph "Recipe Service"
        RecipeController[Recipe Controller]
        VectorSearch[Vector Search Service]
    end
    
    subgraph "User Service"
        UserController[User Controller]
        UserDB[(MySQL<br/>User Preferences)]
    end
    
    subgraph "External Databases"
        PostgresDB[(PostgreSQL<br/>Recipes & Meal Plans)]
        QdrantDB[(Qdrant<br/>Recipe Embeddings)]
    end
    
    subgraph "External APIs"
        GeminiAPI[Google Gemini API<br/>LLM Processing]
    end
    
    %% User interaction flow
    User --> UI
    UI --> Gateway
    Gateway --> Controller
    
    %% RAG Process Flow
    Controller --> RAGService
    RAGService --> EmbedService
    EmbedService --> VectorSearch
    VectorSearch --> QdrantDB
    QdrantDB --> VectorSearch
    VectorSearch --> RecipeController
    RecipeController --> PostgresDB
    PostgresDB --> RecipeController
    RecipeController --> RAGService
    
    %% User preferences retrieval
    RAGService --> UserController
    UserController --> UserDB
    UserDB --> UserController
    UserController --> RAGService
    
    %% LLM Generation
    RAGService --> GeminiService
    GeminiService --> GeminiAPI
    GeminiAPI --> GeminiService
    GeminiService --> RAGService
    
    %% Store and return results
    RAGService --> DBService
    DBService --> PostgresDB
    PostgresDB --> DBService
    DBService --> Controller
    Controller --> Gateway
    Gateway --> UI
    UI --> User
    
    %% Styling with better text contrast
    classDef userLayer fill:#d4f1f9,stroke:#333,stroke-width:2px,color:#000
    classDef frontendLayer fill:#ffcc99,stroke:#333,stroke-width:2px,color:#000
    classDef serviceLayer fill:#e0c6c2,stroke:#333,stroke-width:2px,color:#000
    classDef databaseLayer fill:#c6c2e0,stroke:#333,stroke-width:2px,color:#000
    classDef externalLayer fill:#e0e0c2,stroke:#333,stroke-width:2px,color:#000
    
    class User userLayer
    class UI frontendLayer
    class Gateway,Controller,RAGService,EmbedService,GeminiService,DBService,RecipeController,UserController,VectorSearch serviceLayer
    class PostgresDB,QdrantDB,UserDB databaseLayer
    class GeminiAPI externalLayer
```

## Microservices Communication Flow

```mermaid
graph LR
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile Browser]
    end
    
    subgraph "Application Layer"
        Frontend[React Frontend<br/>Port 80]
    end
    
    subgraph "Gateway Layer"
        APIGateway[API Gateway<br/>Express.js<br/>Port 3000]
    end
    
    subgraph "Microservices Layer"
        UserSvc[User Service<br/>FastAPI<br/>Port 8000]
        RecipeSvc[Recipe Service<br/>FastAPI<br/>Port 8001]
        MealSvc[Meal Planner Service<br/>FastAPI<br/>Port 8002]
        NotifSvc[Notification Service<br/>FastAPI<br/>Port 8003]
    end
    
    subgraph "Data Layer"
        MySQL[(MySQL<br/>Port 13306<br/>User Data)]
        PostgreSQL[(PostgreSQL<br/>Port 15432<br/>Recipes & Meal Plans)]
        Qdrant[(Qdrant Vector DB<br/>Port 6333<br/>Recipe Embeddings)]
    end
    
    subgraph "External Services"
        Gemini[Google Gemini API<br/>LLM Processing]
        SMTP[Email Service<br/>SMTP]
    end
    
    %% Client connections
    Browser --> Frontend
    Mobile --> Frontend
    
    %% Frontend to Gateway
    Frontend -.->|HTTPS| APIGateway
    
    %% Gateway to Services
    APIGateway -.->|/api/users/*| UserSvc
    APIGateway -.->|/api/recipes/*| RecipeSvc
    APIGateway -.->|/api/meal-plans/*| MealSvc
    APIGateway -.->|/api/notifications/*| NotifSvc
    
    %% Service to Database connections
    UserSvc --> MySQL
    RecipeSvc --> PostgreSQL
    RecipeSvc --> Qdrant
    MealSvc --> PostgreSQL
    NotifSvc --> PostgreSQL
    
    %% Inter-service communication
    MealSvc -.->|Get User Preferences| UserSvc
    MealSvc -.->|Search Recipes| RecipeSvc
    NotifSvc -.->|Get User Info| UserSvc
    NotifSvc -.->|Get Meal Plans| MealSvc
    
    %% External API connections
    MealSvc -.->|Generate Meal Plans| Gemini
    NotifSvc -.->|Send Emails| SMTP
    
    %% Styling with better text contrast
    classDef client fill:#d4f1f9,stroke:#333,stroke-width:2px,color:#000
    classDef frontend fill:#ffcc99,stroke:#333,stroke-width:2px,color:#000
    classDef gateway fill:#c2e0c6,stroke:#333,stroke-width:2px,color:#000
    classDef service fill:#e0c6c2,stroke:#333,stroke-width:2px,color:#000
    classDef database fill:#c6c2e0,stroke:#333,stroke-width:2px,color:#000
    classDef external fill:#e0e0c2,stroke:#333,stroke-width:2px,color:#000
    
    class Browser,Mobile client
    class Frontend frontend
    class APIGateway gateway
    class UserSvc,RecipeSvc,MealSvc,NotifSvc service
    class MySQL,PostgreSQL,Qdrant database
    class Gemini,SMTP external
```
